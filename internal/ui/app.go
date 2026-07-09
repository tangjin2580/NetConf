// Package ui 用 walk 构建原生 Win32 图形界面
package ui

import (
	"github.com/lxn/walk"
	"github.com/lxn/walk/declarative"

	"gnetconf/internal/config"
	"gnetconf/internal/network"
	"gnetconf/internal/server"
	"gnetconf/internal/system"
)

// App 持有主窗口与共享状态
type App struct {
	mw         *walk.MainWindow
	statusLabel *walk.Label
	serverURL   string

	// 双WAN页
	sunflowerStatus  *walk.Label
	routerIP         *walk.LineEdit
	routerUser       *walk.LineEdit
	routerPass       *walk.LineEdit
	serverStatusLabel *walk.Label
	fileList         *walk.ListBox
	fileContent      *walk.TextEdit

	// 单机配置页
	ifaceList    *walk.ListBox
	ipEdit       *walk.LineEdit
	maskEdit     *walk.LineEdit
	dnsEdit      *walk.LineEdit
	standaloneLog *walk.TextEdit

	// Hosts 页
	hostsStatus *walk.Label
	hostsLog    *walk.TextEdit

	// 配置信息服务器页
	serverFileList    *walk.ListBox
	serverFileContent *walk.TextEdit
	serverInfoLabel   *walk.Label

	// 服务器文件缓存（按浏览区域分别保存）
	dualWanFiles   []server.FileInfo
	serverPageFiles []server.FileInfo
}

// NewApp 创建应用实例
func NewApp() *App {
	return &App{serverURL: config.DefaultServerURL}
}

// serverClient 返回当前服务器客户端
func (a *App) serverClient() *server.Client {
	return server.NewClient(a.serverURL)
}

// setStatus 更新底部状态栏
func (a *App) setStatus(s string) {
	if a.statusLabel != nil {
		a.statusLabel.SetText(s)
	}
}

// logMsg 在指定文本框追加一行日志
func (a *App) logMsg(te *walk.TextEdit, s string) {
	if te == nil {
		return
	}
	cur := te.Text()
	if cur != "" {
		cur += "\r\n"
	}
	_ = te.SetText(cur + s)
}

// runAsync 后台执行任务并在 UI 线程回调
func (a *App) runAsync(work func() error, onDone func(err error)) {
	go func() {
		err := work()
		a.mw.Synchronize(func() {
			if onDone != nil {
				onDone(err)
			}
		})
	}()
}

// Run 构建并运行主窗口（使用 walk/declarative 声明式 API）
func (a *App) Run() error {
	var tw *walk.TabWidget

	mw := declarative.MainWindow{
		AssignTo: &a.mw,
		Title:    config.AppName + "  v" + config.LocalVersion,
		MinSize:  declarative.Size{Width: 880, Height: 640},
		Layout:   declarative.VBox{Margins: declarative.Margins{Left: 0, Top: 0, Right: 0, Bottom: 0}},
		MenuItems: []declarative.MenuItem{
			declarative.Menu{
				Text: "文件",
				Items: []declarative.MenuItem{
					declarative.Action{Text: "退出", OnTriggered: func() { a.mw.Close() }},
				},
			},
			declarative.Menu{
				Text: "设置",
				Items: []declarative.MenuItem{
					declarative.Action{Text: "服务器地址...", OnTriggered: a.showServerConfig},
				},
			},
			declarative.Menu{
				Text: "帮助",
				Items: []declarative.MenuItem{
					declarative.Action{Text: "关于", OnTriggered: a.showAbout},
				},
			},
		},
		Children: []declarative.Widget{
			declarative.TabWidget{
				AssignTo: &tw,
				Pages: []declarative.TabPage{
					a.dualWANPage(),
					a.standalonePage(),
					a.hostsPage(),
					a.serverPage(),
				},
			},
			declarative.Label{
				AssignTo: &a.statusLabel,
				Text:     "就绪",
			},
		},
	}
	if err := mw.Create(); err != nil {
		return err
	}

	// 后台启动内嵌信息服务器（作为服务器模式时可用）
	server.NewInfoServer().Start()

	a.setStatus("就绪")
	a.mw.Run()
	return nil
}

// showAbout 显示关于对话框
func (a *App) showAbout() {
	walk.MsgBox(a.mw, "关于",
		config.AppName+"\n版本: "+config.LocalVersion+
			"\n\n用于医保网络环境的一键配置工具。\n基于 Go + walk 构建，单文件免安装，兼容 Windows 7 及以上。",
		walk.MsgBoxOK|walk.MsgBoxIconInformation)
}

// showServerConfig 显示服务器地址设置对话框
func (a *App) showServerConfig() {
	var dlg *walk.Dialog
	var urlEdit *walk.LineEdit
	var saveBtn, cancelBtn *walk.PushButton

	d := declarative.Dialog{
		AssignTo:      &dlg,
		Title:         "服务器配置",
		MinSize:       declarative.Size{Width: 420, Height: 180},
		Layout:        declarative.VBox{},
		DefaultButton: &saveBtn,
		CancelButton:  &cancelBtn,
		Children: []declarative.Widget{
			declarative.Label{Text: "服务器地址:"},
			declarative.LineEdit{AssignTo: &urlEdit, Text: a.serverURL},
			declarative.Composite{
				Layout: declarative.HBox{},
				Children: []declarative.Widget{
					declarative.PushButton{
						AssignTo: &saveBtn,
						Text:     "保存",
						OnClicked: func() {
							v := urlEdit.Text()
							if v == "" {
								walk.MsgBox(dlg, "警告", "服务器地址不能为空", walk.MsgBoxOK|walk.MsgBoxIconWarning)
								return
							}
							a.serverURL = v
							if a.serverStatusLabel != nil {
								a.serverStatusLabel.SetText("服务器: " + v)
							}
							if a.serverInfoLabel != nil {
								a.serverInfoLabel.SetText("服务器: " + v)
							}
							dlg.Accept()
						},
					},
					declarative.PushButton{
						AssignTo:  &cancelBtn,
						Text:      "取消",
						OnClicked: func() { dlg.Cancel() },
					},
				},
			},
		},
	}
	if err := d.Create(a.mw); err != nil {
		walk.MsgBox(a.mw, "错误", err.Error(), walk.MsgBoxOK|walk.MsgBoxIconError)
		return
	}

	_ = dlg.Run()
}

// downloadSunflower 下载向日葵
func (a *App) downloadSunflower() {
	if err := system.DownloadSunflower(); err != nil {
		walk.MsgBox(a.mw, "错误", err.Error(), walk.MsgBoxOK|walk.MsgBoxIconError)
	} else {
		walk.MsgBox(a.mw, "下载", "已打开浏览器下载向日葵，请下载并安装后重启本程序", walk.MsgBoxOK)
	}
}

// launchSunflower 启动向日葵
func (a *App) launchSunflower(path string) {
	if err := system.LaunchSunflower(path); err != nil {
		walk.MsgBox(a.mw, "错误", "启动向日葵失败: "+err.Error(), walk.MsgBoxOK|walk.MsgBoxIconError)
	} else {
		walk.MsgBox(a.mw, "提示", "向日葵已启动", walk.MsgBoxOK)
	}
}

// setAllMTU 一键设置所有网卡 MTU
func (a *App) setAllMTU() {
	a.runAsync(func() error {
		results := network.SetAllMTU(config.DefaultMTU)
		a.mw.Synchronize(func() {
			msg := ""
			for _, r := range results {
				msg += r + "\n"
			}
			walk.MsgBox(a.mw, "MTU设置完成", msg, walk.MsgBoxOK)
		})
		return nil
	}, nil)
}
