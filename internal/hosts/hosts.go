// Package hosts 管理与医保系统相关的 hosts 文件读写
package hosts

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gnetconf/internal/config"
	"gnetconf/internal/system"
)

// HostsPath 系统 hosts 文件路径
const HostsPath = `C:\Windows\System32\drivers\etc\hosts`

// HostsDir hosts 文件所在目录
var HostsDir = filepath.Dir(HostsPath)

// Status 描述 hosts 文件检查状态
type Status struct {
	Complete bool
	Missing  []string
	Existing []string
}

// CheckStatus 检查 hosts 文件是否包含全部医保条目
func CheckStatus() Status {
	expected := config.HostsEntries
	st := Status{}

	if _, err := os.Stat(HostsPath); err != nil {
		st.Missing = append(st.Missing, expected...)
		return st
	}

	data, err := os.ReadFile(HostsPath)
	if err != nil {
		st.Missing = append(st.Missing, expected...)
		return st
	}
	content := string(data)

	for _, entry := range expected {
		domain := strings.Fields(entry)[1]
		if strings.Contains(content, domain) {
			st.Existing = append(st.Existing, entry)
		} else {
			st.Missing = append(st.Missing, entry)
		}
	}
	st.Complete = len(st.Missing) == 0
	return st
}

// Modify 补全缺失的医保条目，返回实际新增的条目
// 优先直接写入，失败则通过临时文件 + cmd move 覆盖写入（兼容杀软/权限限制）
func Modify() ([]string, error) {
	return modifyWithFallback(false)
}

// ModifyForce 强制使用备用路径写入（先写临时文件再覆盖）
func ModifyForce() ([]string, error) {
	return modifyWithFallback(true)
}

func modifyWithFallback(forceTemp bool) ([]string, error) {
	expected := config.HostsEntries

	var existing string
	if data, err := os.ReadFile(HostsPath); err == nil {
		existing = string(data)
	}

	var newContent strings.Builder
	if existing != "" {
		// 去除尾部空行，保留原有的 \r\n 行尾
		newContent.WriteString(strings.TrimRight(existing, "\r\n"))
		newContent.WriteString("\r\n")
	}
	newContent.WriteString("\r\n# 医保系统\r\n")

	var added []string
	for _, entry := range expected {
		domain := strings.Fields(entry)[1]
		if !strings.Contains(existing, domain) {
			newContent.WriteString(entry)
			newContent.WriteString("\r\n")
			added = append(added, entry)
		}
	}
	if len(added) == 0 {
		return added, nil
	}

	if !forceTemp {
		if err := os.WriteFile(HostsPath, []byte(newContent.String()), 0o644); err == nil {
			return added, nil
		}
	}

	// 备选方案：写入临时文件 → 覆盖
	tmpFile := filepath.Join(system.CacheFolder(), "hosts.tmp")
	if err := os.WriteFile(tmpFile, []byte(newContent.String()), 0o644); err != nil {
		return added, fmt.Errorf("无法创建临时 hosts 文件: %w", err)
	}
	if err := os.Rename(tmpFile, HostsPath); err != nil {
		cmd := fmt.Sprintf(`move /Y "%s" "%s"`, tmpFile, HostsPath)
		if out, err2 := system.RunLine(cmd); err2 != nil {
			_ = os.Remove(tmpFile)
			return added, fmt.Errorf("hosts 写入失败（已尝试直接写入和临时文件替换）\ncmd move 输出: %s\n%v", strings.TrimSpace(out), err2)
		}
	}
	return added, nil
}

// AlreadySet 判断 hosts 是否已配置（含任一医保域名即认为已配置）
func AlreadySet() bool {
	data, err := os.ReadFile(HostsPath)
	if err != nil {
		return false
	}
	content := string(data)
	for _, entry := range config.HostsEntries {
		domain := strings.Fields(entry)[1]
		if strings.Contains(content, domain) {
			return true
		}
	}
	return false
}

// OpenDir 在资源管理器中打开 hosts 文件所在目录
func OpenDir() error {
	return system.Run("explorer", "/select,", HostsPath)
}
