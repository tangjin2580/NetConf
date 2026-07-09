package main

import (
	"fmt"
	"runtime/debug"

	"github.com/lxn/walk"

	"gnetconf/internal/system"
	"gnetconf/internal/ui"
)

func main() {
	system.ResetTrace()
	system.Trace("start")

	// 顶层崩溃兜底：任何 panic 都写入日志并弹窗，避免“黑框一闪而过”后毫无痕迹
	defer func() {
		if r := recover(); r != nil {
			stack := debug.Stack()
			system.WriteCrashLog(fmt.Sprintf("panic: %v\n\n%s", r, stack))
			msg := fmt.Sprintf("程序异常崩溃：\n%v\n\n详细堆栈已写入：\n%s", r, system.CrashLogPath())
			_ = walk.MsgBox(nil, "程序崩溃", msg, walk.MsgBoxOK|walk.MsgBoxIconError)
		}
	}()

	system.Trace("checking admin")
	if !system.IsAdmin() {
		system.Trace("not admin")
		_ = walk.MsgBox(nil, "需要管理员权限",
			"本程序需要修改网络配置（IP/路由/Hosts），\n请右键本程序，选择【以管理员身份运行】。",
			walk.MsgBoxOK|walk.MsgBoxIconWarning)
		return
	}
	system.Trace("admin ok")

	system.Trace("creating window")
	app := ui.NewApp()
	if err := app.Run(); err != nil {
		system.Trace("run error: " + err.Error())
		_ = walk.MsgBox(nil, "启动失败", "程序启动失败：\n"+err.Error(),
			walk.MsgBoxOK|walk.MsgBoxIconError)
	}
	system.Trace("run returned")
}
