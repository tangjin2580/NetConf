package server

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"runtime/debug"
	"strings"

	"gnetconf/internal/config"
	"gnetconf/internal/system"
)

var expectedAuth = "Basic " + base64.StdEncoding.EncodeToString(
	[]byte(config.ServerUsername+":"+config.ServerPassword))

// InfoServer 内嵌的轻量级配置信息 HTTP 服务器
type InfoServer struct {
	Port       int
	InfoFolder string
}

// NewInfoServer 创建信息服务器（端口默认 8080，目录为 exe 同级 info）
func NewInfoServer() *InfoServer {
	return &InfoServer{
		Port:       config.ServerPort,
		InfoFolder: filepath.Join(system.ExeDir(), "info"),
	}
}

// Start 在后台启动 HTTP 服务
func (s *InfoServer) Start() {
	_ = os.MkdirAll(s.InfoFolder, 0o755)
	go func() {
		defer func() {
			if r := recover(); r != nil {
				system.WriteCrashLog(fmt.Sprintf("server goroutine panic: %v\n\n%s", r, debug.Stack()))
			}
		}()
		if err := http.ListenAndServe(fmt.Sprintf(":%d", s.Port), s.handler()); err != nil {
			system.Trace("信息服务器启动失败: " + err.Error())
		}
	}()
}

func (s *InfoServer) handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/api/files", s.auth(s.listFiles))
	mux.HandleFunc("/api/upload", s.auth(s.handleUpload))
	mux.HandleFunc("/api/save", s.auth(s.handleSave))
	mux.HandleFunc("/api/status", s.auth(s.handleStatus))
	mux.HandleFunc("/download/", s.auth(s.handleDownload))
	return mux
}

func (s *InfoServer) auth(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") != expectedAuth {
			w.Header().Set("WWW-Authenticate", `Basic realm="netconf"`)
			http.Error(w, "未授权", http.StatusUnauthorized)
			return
		}
		next(w, r)
	}
}

func (s *InfoServer) handleStatus(w http.ResponseWriter, r *http.Request) {
	files := s.readFiles()
	writeJSON(w, map[string]any{
		"success":     true,
		"port":        s.Port,
		"files_count": len(files),
	})
}

func (s *InfoServer) listFiles(w http.ResponseWriter, r *http.Request) {
	files := s.readFiles()
	writeJSON(w, map[string]any{"success": true, "files": files})
}

func (s *InfoServer) readFiles() []FileInfo {
	var files []FileInfo
	entries, err := os.ReadDir(s.InfoFolder)
	if err != nil {
		return files
	}
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		info, err := e.Info()
		if err != nil {
			continue
		}
		files = append(files, FileInfo{
			Name:     e.Name(),
			Size:     info.Size(),
			Modified: info.ModTime().Format("2006-01-02 15:04:05"),
		})
	}
	return files
}

func (s *InfoServer) handleDownload(w http.ResponseWriter, r *http.Request) {
	filename := filepath.Base(strings.TrimPrefix(r.URL.Path, "/download/"))
	path := filepath.Join(s.InfoFolder, filename)
	data, err := os.ReadFile(path)
	if err != nil {
		http.Error(w, "文件不存在", http.StatusNotFound)
		return
	}
	w.Header().Set("Content-Type", "application/octet-stream")
	w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="%s"`, filename))
	_, _ = w.Write(data)
}

func (s *InfoServer) handleUpload(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseMultipartForm(32 << 20); err != nil {
		writeJSON(w, map[string]any{"success": false, "message": "解析失败: " + err.Error()})
		return
	}
	file, header, err := r.FormFile("file")
	if err != nil {
		writeJSON(w, map[string]any{"success": false, "message": "未找到文件字段"})
		return
	}
	defer file.Close()
	name := filepath.Base(header.Filename)
	dst, err := os.Create(filepath.Join(s.InfoFolder, name))
	if err != nil {
		writeJSON(w, map[string]any{"success": false, "message": err.Error()})
		return
	}
	defer dst.Close()
	if _, err := io.Copy(dst, file); err != nil {
		writeJSON(w, map[string]any{"success": false, "message": err.Error()})
		return
	}
	writeJSON(w, map[string]any{"success": true, "message": "上传成功: " + name})
}

func (s *InfoServer) handleSave(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Filename string `json:"filename"`
		Content  string `json:"content"`
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		writeJSON(w, map[string]any{"success": false, "message": err.Error()})
		return
	}
	name := filepath.Base(body.Filename)
	if name == "" {
		writeJSON(w, map[string]any{"success": false, "message": "文件名不能为空"})
		return
	}
	if err := os.WriteFile(filepath.Join(s.InfoFolder, name), []byte(body.Content), 0o644); err != nil {
		writeJSON(w, map[string]any{"success": false, "message": err.Error()})
		return
	}
	writeJSON(w, map[string]any{"success": true, "message": "保存成功: " + name})
}

func writeJSON(w http.ResponseWriter, data any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	_ = json.NewEncoder(w).Encode(data)
}
