// Package system 提供系统级能力：管理员检测、向日葵检测、本地缓存
package system

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"unsafe"

	"golang.org/x/sys/windows"

	"gnetconf/internal/config"
)

// IsAdmin 判断当前进程是否以管理员权限运行
func IsAdmin() bool {
	var token windows.Token
	if err := windows.OpenProcessToken(windows.CurrentProcess(), windows.TOKEN_QUERY, &token); err != nil {
		return false
	}
	defer token.Close()

	var elevation uint32
	var outLen uint32
	if err := windows.GetTokenInformation(
		token,
		windows.TokenElevation,
		(*byte)(unsafe.Pointer(&elevation)),
		uint32(unsafe.Sizeof(elevation)),
		&outLen,
	); err != nil {
		return false
	}
	return elevation != 0
}

// ExeDir 返回当前可执行文件所在目录
func ExeDir() string {
	exe, err := os.Executable()
	if err != nil {
		return "."
	}
	return filepath.Dir(exe)
}

// CacheFolder 返回本地缓存目录（位于 exe 同级的 cache 子目录）
func CacheFolder() string {
	dir := filepath.Join(ExeDir(), "cache")
	_ = os.MkdirAll(dir, 0o755)
	return dir
}

// ClearCache 清空缓存目录下的所有文件
func ClearCache() {
	dir := CacheFolder()
	entries, err := os.ReadDir(dir)
	if err != nil {
		return
	}
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		_ = os.Remove(filepath.Join(dir, e.Name()))
	}
}

// CheckSunflowerInstalled 检测向日葵是否已安装，返回路径
func CheckSunflowerInstalled() (bool, string) {
	for _, p := range config.SunflowerPaths {
		expanded := os.ExpandEnv(p)
		if _, err := os.Stat(expanded); err == nil {
			return true, expanded
		}
	}
	return false, ""
}

// DownloadSunflower 打开浏览器下载向日葵安装包
func DownloadSunflower() error {
	cmd := exec.Command("cmd", "/c", "start", "", config.SunflowerDownloadURL)
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("无法打开浏览器，请手动访问: %s", config.SunflowerDownloadURL)
	}
	return nil
}

// LaunchSunflower 启动已安装的向日葵
func LaunchSunflower(installPath string) error {
	cmd := exec.Command("cmd", "/c", "start", "", installPath)
	return cmd.Start()
}

// runCmd 执行 Windows 命令并返回组合输出（错误也返回输出，方便排查）
func runCmd(name string, args ...string) (string, error) {
	cmd := exec.Command(name, args...)
	out, err := cmd.CombinedOutput()
	return string(out), err
}

// Run 执行设置类命令（netsh / route 等），失败返回错误
func Run(name string, args ...string) error {
	_, err := runCmd(name, args...)
	return err
}

// RunLine 执行一条完整的 cmd 命令行
func RunLine(line string) (string, error) {
	return runCmd("cmd", "/c", line)
}

// ExpandEnv 展开 %VAR% 形式的环境变量（供 UI 层复用）
func ExpandEnv(s string) string {
	return os.ExpandEnv(s)
}

// StringsContains 判断切片是否包含某字符串
func StringsContains(list []string, s string) bool {
	for _, v := range list {
		if strings.EqualFold(v, s) {
			return true
		}
	}
	return false
}
