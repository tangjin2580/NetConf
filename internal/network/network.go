// Package network 负责网卡解析、连通性测试与 netsh/route 网络配置
package network

import (
	"fmt"
	"net"
	"regexp"
	"strconv"
	"strings"
	"time"

	"gnetconf/internal/config"
	"gnetconf/internal/hosts"
	"gnetconf/internal/system"
)

// InterfaceInfo 描述一个网卡及其 IPv4 地址
type InterfaceInfo struct {
	Name string
	IP   string
}

var (
	adapterRe = regexp.MustCompile(`(?:以太网适配器|无线局域网适配器|Ethernet adapter|Wireless LAN adapter)\s+(.+?):`)
	ipRe      = regexp.MustCompile(`(?:IPv4 地址|IPv4 Address|IP Address)[^0-9]*(\d+\.\d+\.\d+\.\d+)`)
)

// runUTF8 以 UTF-8 代码页执行命令并返回输出（适配中文 Windows 的 GBK 输出）
func runUTF8(line string) (string, error) {
	return system.RunLine(`chcp 65001 >nul && ` + line)
}

// GetInterfaces 解析 ipconfig /all 获取网卡与 IPv4
func GetInterfaces() []InterfaceInfo {
	out, err := runUTF8(`ipconfig /all`)
	if err != nil && out == "" {
		return nil
	}
	var result []InterfaceInfo
	var curName, curIP string
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimSpace(line)
		if m := adapterRe.FindStringSubmatch(line); m != nil {
			if curName != "" {
				result = append(result, InterfaceInfo{Name: curName, IP: curIP})
			}
			curName = strings.TrimSpace(m[1])
			curIP = "未获取"
			continue
		}
		if curName != "" {
			if m := ipRe.FindStringSubmatch(line); m != nil {
				curIP = m[1]
			}
		}
	}
	if curName != "" {
		result = append(result, InterfaceInfo{Name: curName, IP: curIP})
	}
	return result
}

// PingResult 一次 ping 的结果
type PingResult struct {
	Host      string
	Sent      int
	Lost      int
	LossPct   int
	AvgTimeMs int
	OK        bool
}

// Ping 对目标执行 ping 测试
func Ping(host string, count, timeoutMs int) PingResult {
	r := PingResult{Host: host}
	out, err := system.RunLine(fmt.Sprintf(`ping -n %d -w %d %s`, count, timeoutMs, host))
	if err != nil && out == "" {
		return r
	}
	if m := regexp.MustCompile(`已发送 = (\d+)`).FindStringSubmatch(out); m != nil {
		r.Sent, _ = strconv.Atoi(m[1])
	}
	if m := regexp.MustCompile(`丢失 = (\d+)`).FindStringSubmatch(out); m != nil {
		r.Lost, _ = strconv.Atoi(m[1])
	}
	if m := regexp.MustCompile(`(\d+)% 丢失`).FindStringSubmatch(out); m != nil {
		r.LossPct, _ = strconv.Atoi(m[1])
	}
	if m := regexp.MustCompile(`平均 = (\d+)ms`).FindStringSubmatch(out); m != nil {
		r.AvgTimeMs, _ = strconv.Atoi(m[1])
	}
	r.OK = r.Lost < r.Sent && r.Sent > 0
	return r
}

// TestHostConnectivity TCP 连通性测试
func TestHostConnectivity(host string, port, timeoutSec int) bool {
	addr := net.JoinHostPort(host, strconv.Itoa(port))
	conn, err := net.DialTimeout("tcp", addr, time.Duration(timeoutSec)*time.Second)
	if err != nil {
		return false
	}
	_ = conn.Close()
	return true
}

// runNetsh 执行 netsh 命令并返回完整错误信息（包含命令输出）
func runNetsh(args ...string) error {
	return system.RunNetsh("netsh", args...)
}

// SetStaticIP 设置静态 IP 与子网掩码
func SetStaticIP(iface, ip, mask string) error {
	return runNetsh("interface", "ipv4", "set", "address",
		fmt.Sprintf(`name=%q`, iface), "static", ip, mask)
}

// SetDNS 设置 DNS
func SetDNS(iface, dns string) error {
	return runNetsh("interface", "ipv4", "set", "dns",
		fmt.Sprintf(`name=%q`, iface), "static", dns)
}

// SetMTU 设置网卡 MTU（Win7 兼容: 移除 store=persistent，MTU 默认持久化）
func SetMTU(iface string, mtu int) error {
	return runNetsh("interface", "ipv4", "set", "subinterface",
		fmt.Sprintf(`"%s"`, iface), fmt.Sprintf("mtu=%d", mtu))
}

// AddRoute 添加永久路由
func AddRoute(gateway string) error {
	return system.RunNetsh("route", "-p", "add", config.DefaultRoute, "mask", config.DefaultRouteMask, gateway)
}

// SetAllMTU 设置所有网卡 MTU
func SetAllMTU(mtu int) []string {
	var results []string
	for _, i := range GetInterfaces() {
		if err := SetMTU(i.Name, mtu); err != nil {
			results = append(results, fmt.Sprintf("✗ %s 设置失败: %v", i.Name, err))
		} else {
			results = append(results, fmt.Sprintf("✓ %s MTU已设置为 %d", i.Name, mtu))
		}
	}
	return results
}

// GetDefaultGateway 从路由表获取默认网关
func GetDefaultGateway() string {
	out, err := runUTF8(`route print -4`)
	if err != nil && out == "" {
		return ""
	}
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimSpace(line)
		if strings.Count(line, "0.0.0.0") >= 2 {
			fields := strings.Fields(line)
			for i, f := range fields {
				if f == "0.0.0.0" && i+2 < len(fields) && fields[i+1] == "0.0.0.0" {
					gw := fields[i+2]
					if gw != "On-link" {
						return gw
					}
				}
			}
		}
	}
	return ""
}

// IpAlreadySet 判断网卡是否已配置 10.36. 段 IP
func IpAlreadySet(iface string) bool {
	for _, i := range GetInterfaces() {
		if i.Name == iface && strings.HasPrefix(i.IP, config.DefaultIPPrefix) {
			return true
		}
	}
	return false
}

// MtuAlreadySet 判断网卡 MTU 是否为 1300
func MtuAlreadySet(iface string) bool {
	out, err := runUTF8(fmt.Sprintf(`netsh interface ipv4 show interface "%s"`, iface))
	if err != nil && out == "" {
		return false
	}
	return regexp.MustCompile(`MTU\s*:\s*1300`).MatchString(out)
}

// RouteAlreadySet 判断 10.0.0.0 路由是否已存在
func RouteAlreadySet() bool {
	out, err := runUTF8(`route print ` + config.DefaultRoute)
	if err != nil && out == "" {
		return false
	}
	return strings.Contains(out, config.DefaultRoute)
}

// GetMissingItems 返回指定网卡缺失的配置项
func GetMissingItems(iface string) []string {
	var missing []string
	if !IpAlreadySet(iface) {
		missing = append(missing, "IP 地址")
	}
	if !MtuAlreadySet(iface) {
		missing = append(missing, "MTU")
	}
	if !hosts.AlreadySet() {
		missing = append(missing, "hosts 文件")
	}
	if !RouteAlreadySet() {
		missing = append(missing, "路由")
	}
	return missing
}

// ProgressCB 配置进度回调
type ProgressCB func(current, total int, message string)

// ApplyMissingConfig 按缺失项应用配置
func ApplyMissingConfig(iface, ip, mask, dns string, missing []string, cb ProgressCB) {
	total := len(missing)
	cur := 0
	step := func(msg string) {
		cur++
		if cb != nil {
			cb(cur, total, msg)
		}
	}

	if system.StringsContains(missing, "IP 地址") {
		_ = SetStaticIP(iface, ip, mask)
		_ = SetDNS(iface, dns)
		step("正在配置IP地址...")
	}
	if system.StringsContains(missing, "路由") {
		gw := strings.Join(strings.Split(ip, ".")[:3], ".") + ".1"
		_ = AddRoute(gw)
		step("正在添加路由...")
	}
	if system.StringsContains(missing, "MTU") {
		_ = SetMTU(iface, config.DefaultMTU)
		step("正在设置MTU...")
	}
	if system.StringsContains(missing, "hosts 文件") {
		_, _ = hosts.Modify()
		step("正在修改hosts文件...")
	}
}
