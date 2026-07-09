// Package server 提供配置信息服务器的客户端与内嵌 HTTP 服务
package server

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"gnetconf/internal/config"
	"gnetconf/internal/system"
)

// FileInfo 服务器文件元信息
type FileInfo struct {
	Name     string `json:"name"`
	Size     int64  `json:"size"`
	Modified string `json:"modified"`
}

// Client 配置信息服务器客户端
type Client struct {
	BaseURL string
	User    string
	Pass    string
}

// NewClient 用默认地址与凭据创建客户端
func NewClient(baseURL string) *Client {
	return &Client{BaseURL: baseURL, User: config.ServerUsername, Pass: config.ServerPassword}
}

// AuthHeader 生成 Basic Auth 请求头
func (c *Client) AuthHeader() string {
	raw := c.User + ":" + c.Pass
	return "Basic " + base64.StdEncoding.EncodeToString([]byte(raw))
}

func (c *Client) get(path string) (*http.Response, error) {
	req, err := http.NewRequest(http.MethodGet, c.BaseURL+path, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", c.AuthHeader())
	client := &http.Client{Timeout: 5 * time.Second}
	return client.Do(req)
}

// CheckStatus 检查服务器是否在线
func (c *Client) CheckStatus() (bool, map[string]any) {
	resp, err := c.get("/api/status")
	if err != nil {
		return false, nil
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return false, nil
	}
	var data map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return false, nil
	}
	ok, _ := data["success"].(bool)
	return ok, data
}

// FetchFiles 获取服务器文件列表
func (c *Client) FetchFiles() []FileInfo {
	resp, err := c.get("/api/files")
	if err != nil {
		return nil
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return nil
	}
	var data struct {
		Success bool       `json:"success"`
		Files   []FileInfo `json:"files"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
		return nil
	}
	if !data.Success {
		return nil
	}
	return data.Files
}

// DownloadToCache 下载文件到本地缓存，返回本地路径
func (c *Client) DownloadToCache(filename string) (string, error) {
	resp, err := c.get("/download/" + filename)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return "", fmt.Errorf("下载失败: HTTP %d", resp.StatusCode)
	}
	local := filepath.Join(system.CacheFolder(), filename)
	f, err := os.Create(local)
	if err != nil {
		return "", err
	}
	defer f.Close()
	if _, err := io.Copy(f, resp.Body); err != nil {
		return "", err
	}
	return local, nil
}

// FetchContent 获取文件文本内容
func (c *Client) FetchContent(filename string) string {
	resp, err := c.get("/download/" + filename)
	if err != nil {
		return ""
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return ""
	}
	data, _ := io.ReadAll(resp.Body)
	return string(data)
}
