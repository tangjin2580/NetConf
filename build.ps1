# 在 Windows 上直接构建（兼容 Windows 7）
# 用法: .\build.ps1
# 注意: Go 1.20 是最后一个支持 Windows 7/8/8.1 的版本；
#       Go 1.21+ 编译出的 exe 在 Win7 上会因运行时不兼容而直接崩溃。
#       此处强制使用 go1.20.14 工具链。
$ErrorActionPreference = "Stop"

# 强制使用 Go 1.20 工具链（最后一个支持 Win7 的版本）
$env:GOTOOLCHAIN = "go1.20.14"

Write-Host "==> 当前 Go 工具链: $(go version)"
Write-Host "==> 生成 Windows 资源 (manifest + 图标) ..."
go run github.com/akavel/rsrc@latest -arch amd64 -manifest app.manifest -ico icon.ico -o rsrc.syso

Write-Host "==> 编译 NetConf.exe ..."
go build -ldflags="-s -w -H windowsgui" -o NetConf.exe .

Write-Host "==> 完成: NetConf.exe"
