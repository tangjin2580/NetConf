# 在 Windows 上直接构建（兼容 Windows 7）
# 用法: .\build.ps1
# 注意: Windows 7/8/8.1 仅 Go 1.21.x 及更早版本支持。Go 1.22+ 编译出的 exe 在 Win7 上
#       会因缺少 KERNEL32 导出符号而无法启动。此处强制使用 go1.21.13 工具链。
$ErrorActionPreference = "Stop"

# 强制使用 Go 1.21 工具链（Go 会自动下载，需联网）
$env:GOTOOLCHAIN = "go1.21.13"

Write-Host "==> 当前 Go 工具链: $(go version)"
Write-Host "==> 生成 Windows 资源 (manifest + 图标) ..."
go run github.com/akavel/rsrc@latest -arch amd64 -manifest app.manifest -ico icon.ico -o rsrc.syso

Write-Host "==> 编译 NetConf.exe ..."
go build -ldflags="-s -w -H windowsgui" -o NetConf.exe .

Write-Host "==> 完成: NetConf.exe"
