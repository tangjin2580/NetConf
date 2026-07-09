// Package config 保存应用的常量与默认配置
package config

// 应用基本信息
const (
	AppName     = "医保网络配置工具"
	LocalVersion = "2.0.0"
)

// 配置信息服务器（远程）
const (
	DefaultServerURL = "http://14.18.248.25:4888"
	ServerUsername   = "info"
	ServerPassword   = "mecPassw0rd"
	ServerPort       = 8080
)

// 网络配置默认值
const (
	DefaultIPPrefix = "10.36."
	DefaultMask     = "255.255.255.0"
	DefaultDNS      = "10.37.128.3"
	DefaultMTU      = 1300
	DefaultRoute    = "10.0.0.0"
	DefaultRouteMask = "255.0.0.0"
)

// HostsEntries 需要写入 hosts 文件的医保系统条目
var HostsEntries = []string{
	"10.37.224.243 hisips.shx.hsip.gov.cn",
	"10.37.225.216 fms.shx.hsip.gov.cn",
	"10.37.231.230 cts-svc.shx.hsip.gov.cn",
	"10.37.227.210 zfzg.shx.hsip.gov.cn",
}

// TargetHosts 连通性测试目标（医保地址）
var TargetHosts = []string{
	"hisips.shx.hsip.gov.cn",
	"fms.shx.hsip.gov.cn",
	"cts-svc.shx.hsip.gov.cn",
}

// 向日葵远程控制
const (
	SunflowerDownloadURL = "https://down.oray.com/sunlogin/windows/SunloginClient_ng.exe"
)

// SunflowerPaths 可能的向日葵安装路径
var SunflowerPaths = []string{
	`C:\Program Files\Oray\SunLogin\SunloginClient\AweSun.exe`,
	`C:\Program Files (x86)\Oray\SunLogin\SunloginClient\AweSun.exe`,
	`C:\Program Files\Oray\SunLogin\SunloginClient.exe`,
	`C:\Program Files (x86)\Oray\SunLogin\SunloginClient.exe`,
	`C:\Program Files\Oray\SunLogin\AweSun.exe`,
	`C:\Program Files (x86)\Oray\SunLogin\AweSun.exe`,
	`C:\Program Files\Oray\SunLogin\SunloginClient\sunlogin.exe`,
	`C:\Program Files (x86)\Oray\SunLogin\SunloginClient\sunlogin.exe`,
}

// 版本检查（GitHub Releases）
const (
	GitHubRepo      = "tangjin2580/NetConf"
	GitHubReleases  = "https://github.com/" + GitHubRepo + "/releases"
	GitHubAPILatest = "https://api.github.com/repos/" + GitHubRepo + "/releases/latest"
)
