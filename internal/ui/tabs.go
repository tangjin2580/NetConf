package ui

import (
	"fmt"
	"strings"

	"github.com/lxn/walk"
	"github.com/lxn/walk/declarative"

	"gnetconf/internal/config"
	"gnetconf/internal/hosts"
	"gnetconf/internal/network"
	"gnetconf/internal/server"
	"gnetconf/internal/system"
)

// ===================== 双WAN配置（路由器） =====================

func (a *App) dualWANPage() declarative.TabPage {
	isInstalled, path := system.CheckSunflowerInstalled()
	btnText := "立即下载向日葵"
	var onClick walk.EventHandler = func() { a.downloadSunflower() }
	if isInstalled {
		btnText = "启动向日葵"
		p := path
		onClick = func() { a.launchSunflower(p) }
	}

	gateway := network.GetDefaultGateway()
	if gateway == "" {
		gateway = "192.168.1.1"
	}

	return declarative.TabPage{
		Title:  "双WAN配置（路由器）",
		Layout: declarative.VBox{},
		Children: []declarative.Widget{
			declarative.Composite{
				Layout: declarative.HBox{},
				Children: []declarative.Widget{
					declarative.GroupBox{
						Title:  "向日葵远程控制 / 路由器配置",
						Layout: declarative.VBox{},
						Children: []declarative.Widget{
							declarative.Label{AssignTo: &a.sunflowerStatus, Text: sunflowerStatusText(isInstalled, path)},
							declarative.PushButton{Text: btnText, OnClicked: onClick},
							declarative.Label{Text: "请输入路由器管理账号密码:"},
							declarative.Composite{Layout: declarative.HBox{}, Children: []declarative.Widget{
								declarative.Label{Text: "路由器IP:"},
								declarative.LineEdit{AssignTo: &a.routerIP, Text: gateway},
							}},
							declarative.Composite{Layout: declarative.HBox{}, Children: []declarative.Widget{
								declarative.Label{Text: "管理账号:"},
								declarative.LineEdit{AssignTo: &a.routerUser, Text: "admin"},
							}},
							declarative.Composite{Layout: declarative.HBox{}, Children: []declarative.Widget{
								declarative.Label{Text: "管理密码:"},
								declarative.LineEdit{AssignTo: &a.routerPass, Text: "", PasswordMode: true},
							}},
							declarative.PushButton{Text: "⚡ 一键修改MTU=1300", OnClicked: func() { a.setAllMTU() }},
							declarative.PushButton{Text: "开始双WAN配置", OnClicked: func() { a.startDualWanConfig() }},
						},
					},
					declarative.GroupBox{
						Title:  "配置信息展示",
						Layout: declarative.VBox{},
						Children: []declarative.Widget{
							declarative.Label{AssignTo: &a.serverStatusLabel, Text: "服务器: " + a.serverURL},
							declarative.Composite{Layout: declarative.HBox{}, Children: []declarative.Widget{
								declarative.PushButton{Text: "刷新信息", OnClicked: func() {
									a.browseServer(a.serverClient(), a.serverStatusLabel, a.fileList, a.fileContent, &a.dualWanFiles)
								}},
								declarative.PushButton{Text: "打开服务器", OnClicked: func() { a.openServerURL() }},
							}},
							declarative.Composite{Layout: declarative.HBox{}, Children: []declarative.Widget{
								declarative.ListBox{
									AssignTo:              &a.fileList,
									Model:                 newStringListModel(),
									MinSize:               declarative.Size{Width: 220, Height: 220},
									OnCurrentIndexChanged: func() { a.onDualWanFileSelected() },
								},
								declarative.TextEdit{
									AssignTo: &a.fileContent,
									ReadOnly: true,
									VScroll:  true,
									MinSize:  declarative.Size{Width: 320, Height: 220},
								},
							}},
						},
					},
				},
			},
		},
	}
}

func sunflowerStatusText(installed bool, path string) string {
	if installed {
		return "✓ 向日葵已安装"
	}
	return "⚠ 向日葵未安装（需远程协助配置路由器）"
}

func (a *App) startDualWanConfig() {
	if a.routerPass.Text() == "" {
		walk.MsgBox(a.mw, "提示", "请输入路由器管理密码", walk.MsgBoxOK|walk.MsgBoxIconWarning)
		return
	}
	routerIP := a.routerIP.Text()
	routerUser := a.routerUser.Text()
	a.runAsync(func() error {
		results := network.SetAllMTU(config.DefaultMTU)
		a.mw.Synchronize(func() {
			msg := strings.Join(results, "\n")
			msg += "\n\n请使用向日葵远程连接路由器进行WAN口配置\n路由器IP: " + routerIP + "\n账号: " + routerUser
			walk.MsgBox(a.mw, "双WAN配置完成", msg, walk.MsgBoxOK)
		})
		return nil
	}, nil)
}

func (a *App) openServerURL() {
	_ = system.Run("cmd", "/c", "start", "", a.serverURL)
}

// ===================== 共用：浏览服务器文件 =====================

func (a *App) browseServer(client *server.Client, statusLabel *walk.Label, list *walk.ListBox, content *walk.TextEdit, cache *[]server.FileInfo) {
	a.runAsync(func() error {
		ok, data := client.CheckStatus()
		a.mw.Synchronize(func() {
			if !ok {
				statusLabel.SetText("⚠ 未检测到服务器: " + a.serverURL)
				list.SetModel(newStringListModel())
				content.SetText("")
				*cache = nil
				return
			}
			fc := 0
			if v, ok2 := data["files_count"].(float64); ok2 {
				fc = int(v)
			}
			statusLabel.SetText(fmt.Sprintf("✓ 已连接服务器 (文件数: %d)", fc))
			files := client.FetchFiles()
			names := make([]string, 0, len(files))
			for _, f := range files {
				names = append(names, f.Name)
			}
			list.SetModel(newStringListModel(names...))
			*cache = files
			content.SetText("")
		})
		return nil
	}, nil)
}

func (a *App) onDualWanFileSelected() {
	idx := a.fileList.CurrentIndex()
	a.showFileContent(a.serverClient(), a.dualWanFiles, idx, a.fileContent)
}

func (a *App) onServerFileSelected() {
	idx := a.serverFileList.CurrentIndex()
	a.showFileContent(a.serverClient(), a.serverPageFiles, idx, a.serverFileContent)
}

func (a *App) showFileContent(client *server.Client, files []server.FileInfo, idx int, content *walk.TextEdit) {
	if idx < 0 || idx >= len(files) {
		return
	}
	name := files[idx].Name
	a.runAsync(func() error {
		c := client.FetchContent(name)
		a.mw.Synchronize(func() { content.SetText(c) })
		return nil
	}, nil)
}

// ===================== 单机配置（直连） =====================

func (a *App) standalonePage() declarative.TabPage {
	ifaces := network.GetInterfaces()
	names := make([]string, 0, len(ifaces))
	for _, i := range ifaces {
		names = append(names, fmt.Sprintf("%s    [%s]", i.Name, i.IP))
	}

	children := []declarative.Widget{
		declarative.Label{Text: "请选择需要配置的网卡"},
	}
	if len(names) == 0 {
		children = append(children, declarative.Label{Text: "⚠ 未获取到任何网卡，请检查网络适配器"})
	} else {
		ifaceModel := newStringListModel(names...)
		children = append(children, declarative.ListBox{
			AssignTo: &a.ifaceList,
			Model:    ifaceModel,
			MinSize:  declarative.Size{Width: 600, Height: 120},
		})
	}
	children = append(children,
		declarative.Composite{Layout: declarative.HBox{}, Children: []declarative.Widget{
			declarative.Label{Text: "IP 地址:"},
			declarative.LineEdit{AssignTo: &a.ipEdit, Text: config.DefaultIPPrefix},
		}},
		declarative.Composite{Layout: declarative.HBox{}, Children: []declarative.Widget{
			declarative.Label{Text: "子网掩码:"},
			declarative.LineEdit{AssignTo: &a.maskEdit, Text: config.DefaultMask},
		}},
		declarative.Composite{Layout: declarative.HBox{}, Children: []declarative.Widget{
			declarative.Label{Text: "DNS:"},
			declarative.LineEdit{AssignTo: &a.dnsEdit, Text: config.DefaultDNS},
		}},
		declarative.Composite{Layout: declarative.HBox{}, Children: []declarative.Widget{
			declarative.PushButton{Text: "开始配置", OnClicked: func() { a.applyStandalone(false) }},
			declarative.PushButton{Text: "强制重新配置", OnClicked: func() { a.applyStandalone(true) }},
		}},
		declarative.TextEdit{AssignTo: &a.standaloneLog, ReadOnly: true, VScroll: true, MinSize: declarative.Size{Height: 160}},
	)

	return declarative.TabPage{
		Title:    "单机配置（直连）",
		Layout:   declarative.VBox{},
		Children: children,
	}
}

func (a *App) applyStandalone(force bool) {
	if a.ifaceList == nil {
		return
	}
	sel := a.ifaceList.CurrentIndex()
	ifaces := network.GetInterfaces()
	if sel < 0 || sel >= len(ifaces) {
		walk.MsgBox(a.mw, "错误", "请先选择网卡", walk.MsgBoxOK|walk.MsgBoxIconError)
		return
	}
	iface := ifaces[sel].Name
	ip := a.ipEdit.Text()
	mask := a.maskEdit.Text()
	dns := a.dnsEdit.Text()

	a.setStatus("正在配置 " + iface + " ...")
	a.logMsg(a.standaloneLog, "开始配置网卡: "+iface)

	a.runAsync(func() error {
		missing := network.GetMissingItems(iface)
		if force {
			missing = []string{"IP 地址", "路由", "MTU", "hosts 文件"}
		}
		applyErrs := network.ApplyMissingConfig(iface, ip, mask, dns, missing, func(c, t int, m string) {
			a.mw.Synchronize(func() { a.setStatus(fmt.Sprintf("[%d/%d] %s", c, t, m)) })
		})

		var sb strings.Builder
		sb.WriteString("=== 配置校验 ===\n")
		sb.WriteString(fmt.Sprintf("IP 已配置: %v\n", network.IpAlreadySet(iface)))
		sb.WriteString(fmt.Sprintf("MTU=1300: %v\n", network.MtuAlreadySet(iface)))
		sb.WriteString(fmt.Sprintf("hosts 已配置: %v\n", hosts.AlreadySet()))
		sb.WriteString(fmt.Sprintf("路由已配置: %v\n\n", network.RouteAlreadySet()))
		if len(applyErrs) > 0 {
			sb.WriteString("=== 执行错误 ===\n")
			for _, e := range applyErrs {
				sb.WriteString(e + "\n")
			}
			sb.WriteString("\n")
		}
		sb.WriteString("医保地址连通性测试:\n")
		for _, h := range config.TargetHosts {
			ok := network.TestHostConnectivity(h, 80, 3)
			mark := "🟢 可访问"
			if !ok {
				mark = "🔴 不可访问"
			}
			sb.WriteString(fmt.Sprintf("  %s: %s\n", h, mark))
		}
		a.mw.Synchronize(func() {
			a.logMsg(a.standaloneLog, sb.String())
			walk.MsgBox(a.mw, "配置完成", sb.String(), walk.MsgBoxOK)
		})
		return nil
	}, func(err error) {
		if err != nil {
			walk.MsgBox(a.mw, "失败", err.Error(), walk.MsgBoxOK|walk.MsgBoxIconError)
		}
		a.setStatus("就绪")
	})
}

// ===================== Hosts 文件 =====================

func (a *App) hostsPage() declarative.TabPage {
	st := hosts.CheckStatus()
	statusText := "✓ hosts 文件已完善"
	if !st.Complete {
		statusText = fmt.Sprintf("⚠ hosts 文件不完整（缺失 %d 项）", len(st.Missing))
	}
	return declarative.TabPage{
		Title:  "Hosts文件",
		Layout: declarative.VBox{},
		Children: []declarative.Widget{
			declarative.Label{AssignTo: &a.hostsStatus, Text: statusText},
			declarative.Composite{Layout: declarative.HBox{}, Children: []declarative.Widget{
				declarative.PushButton{Text: "检查并补全", OnClicked: func() { a.checkAndFixHosts() }},
				declarative.PushButton{Text: "刷新状态", OnClicked: func() { a.refreshHostsStatus() }},
				declarative.PushButton{Text: "打开文件目录", OnClicked: func() { a.openHostsDir() }},
			}},
			declarative.TextEdit{AssignTo: &a.hostsLog, ReadOnly: true, VScroll: true, MinSize: declarative.Size{Height: 220}},
		},
	}
}

func (a *App) checkAndFixHosts() {
	a.runAsync(func() error {
		st := hosts.CheckStatus()
		if st.Complete {
			a.mw.Synchronize(func() {
				walk.MsgBox(a.mw, "完成", "hosts 文件已完善，无需修改", walk.MsgBoxOK)
				a.logMsg(a.hostsLog, "hosts 文件已完善，无需修改")
			})
			return nil
		}
		added, err := hosts.Modify()
		a.mw.Synchronize(func() {
			if err != nil {
				walk.MsgBox(a.mw, "错误", err.Error(), walk.MsgBoxOK|walk.MsgBoxIconError)
				return
			}
			msg := fmt.Sprintf("已补全 %d 个条目", len(added))
			for _, e := range added {
				msg += "\n" + e
			}
			walk.MsgBox(a.mw, "完成", msg, walk.MsgBoxOK)
			a.logMsg(a.hostsLog, msg)
			a.refreshHostsStatus()
		})
		return nil
	}, nil)
}

func (a *App) refreshHostsStatus() {
	st := hosts.CheckStatus()
	if st.Complete {
		a.hostsStatus.SetText("✓ hosts 文件已完善")
	} else {
		a.hostsStatus.SetText(fmt.Sprintf("⚠ hosts 文件不完整（缺失 %d 项）", len(st.Missing)))
	}
	var sb strings.Builder
	if len(st.Existing) > 0 {
		sb.WriteString("已存在:\n")
		for _, e := range st.Existing {
			sb.WriteString("  ✓ " + e + "\n")
		}
	}
	if len(st.Missing) > 0 {
		sb.WriteString("缺失:\n")
		for _, e := range st.Missing {
			sb.WriteString("  ✗ " + e + "\n")
		}
	}
	a.hostsLog.SetText(sb.String())
}

func (a *App) openHostsDir() {
	if err := hosts.OpenDir(); err != nil {
		walk.MsgBox(a.mw, "错误", "无法打开目录: "+err.Error(), walk.MsgBoxOK|walk.MsgBoxIconError)
	}
}

// ===================== 配置信息服务器 =====================

func (a *App) serverPage() declarative.TabPage {
	return declarative.TabPage{
		Title:  "配置信息服务器",
		Layout: declarative.VBox{},
		Children: []declarative.Widget{
			declarative.Label{AssignTo: &a.serverInfoLabel, Text: "服务器: " + a.serverURL},
			declarative.Composite{Layout: declarative.HBox{}, Children: []declarative.Widget{
				declarative.PushButton{Text: "刷新信息", OnClicked: func() {
					a.browseServer(a.serverClient(), a.serverInfoLabel, a.serverFileList, a.serverFileContent, &a.serverPageFiles)
				}},
				declarative.PushButton{Text: "打开服务器", OnClicked: func() { a.openServerURL() }},
			}},
			declarative.Composite{Layout: declarative.HBox{}, Children: []declarative.Widget{
				declarative.ListBox{
					AssignTo:              &a.serverFileList,
					Model:                 newStringListModel(),
					MinSize:               declarative.Size{Width: 260, Height: 280},
					OnCurrentIndexChanged: func() { a.onServerFileSelected() },
				},
				declarative.TextEdit{
					AssignTo: &a.serverFileContent,
					ReadOnly: true,
					VScroll:  true,
					MinSize:  declarative.Size{Width: 360, Height: 280},
				},
			}},
		},
	}
}
