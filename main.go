package main

import (
	"fmt"

	"gnetconf/internal/system"
	"gnetconf/internal/ui"
)

func main() {
	if !system.IsAdmin() {
		fmt.Println("权限不足：请右键以【管理员身份】运行本程序")
		return
	}

	app := ui.NewApp()
	if err := app.Run(); err != nil {
		fmt.Println("程序启动失败:", err)
	}
}
