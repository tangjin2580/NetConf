# 在 Windows 上直接构建
# 用法: .\build.ps1
$ErrorActionPreference = "Stop"

Write-Host "==> 生成 Windows 资源 (manifest + 图标) ..."
go run github.com/akavel/rsrc@latest -arch amd64 -manifest app.manifest -ico icon.ico -o rsrc.syso

Write-Host "==> 编译 NetConf.exe ..."
go build -ldflags="-s -w" -o NetConf.exe .

Write-Host "==> 完成: NetConf.exe"
