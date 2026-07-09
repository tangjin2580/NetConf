package main

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime/debug"

	"github.com/lxn/walk"

	"gnetconf/internal/system"
	"gnetconf/internal/ui"
)

func main() {
	// 顶层崩溃兜底：任何 panic 都写入日志并弹窗，避免“黑框一闪而过”后毫无痕迹
	defer func() {
		if r := recover(); r != nil {
			stack := debug.Stack()
			writeCrashLog(fmt.Sprintf("panic: %v\n\n%s", r, stack))
			msg := fmt.Sprintf("程序异常崩溃：\n%v\n\n详细堆栈已写入：\n%s", r, crashLogPath())
			_ = walk.MsgBox(nil, "程序崩溃", msg, walk.MsgBoxOK|walk.MsgBoxIconError)
		}
	}()

	if !system.IsAdmin() {
		_ = walk.MsgBox(nil, "需要管理员权限",
			"本程序需要修改网络配置（IP/路由/Hosts），\n请右键本程序，选择【以管理员身份运行】。",
			walk.MsgBoxOK|walk.MsgBoxIconWarning)
		return
	}

	app := ui.NewApp()
	if err := app.Run(); err != nil {
		_ = walk.MsgBox(nil, "启动失败", "程序启动失败：\n"+err.Error(),
			walk.MsgBoxOK|walk.MsgBoxIconError)
	}
}

// crashLogPath 返回崩溃日志路径（与 exe 同级）
func crashLogPath() string {
	if exe, err := os.Executable(); err == nil {
		return filepath.Join(filepath.Dir(exe), "NetConf.crash.log")
	}
	return "NetConf.crash.log"
}

// writeCrashLog 把崩溃信息写入 exe 同级日志文件
func writeCrashLog(content string) {
	_ = os.WriteFile(crashLogPath(), []byte(content), 0o644)
}
