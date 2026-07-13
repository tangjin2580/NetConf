// Package hosts 管理与医保系统相关的 hosts 文件读写
package hosts

import (
	"os"
	"strings"

	"gnetconf/internal/config"
)

// HostsPath 系统 hosts 文件路径
const HostsPath = `C:\Windows\System32\drivers\etc\hosts`

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

const hostsComment = "# 医保系统"

// Modify 补全缺失的医保条目，返回实际新增的条目
func Modify() ([]string, error) {
	expected := config.HostsEntries

	var existing string
	if data, err := os.ReadFile(HostsPath); err == nil {
		existing = string(data)
	}

	f, err := os.OpenFile(HostsPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	hasComment := strings.Contains(existing, hostsComment)
	if !hasComment {
		if _, err := f.WriteString("\n" + hostsComment + "\n"); err != nil {
			return nil, err
		}
	}

	var added []string
	for _, entry := range expected {
		domain := strings.Fields(entry)[1]
		if !strings.Contains(existing, domain) {
			if _, err := f.WriteString(entry + "\n"); err != nil {
				return added, err
			}
			added = append(added, entry)
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
