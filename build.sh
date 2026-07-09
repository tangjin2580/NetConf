#!/usr/bin/env bash
# 在 macOS / Linux 上交叉编译 Windows 64 位静态可执行文件（兼容 Windows 7）
# 用法: ./build.sh
# 注意: Windows 7/8/8.1 仅 Go 1.21.x 及更早版本支持；Go 1.22+ 编译出的 exe 会在
#       Win7 上因缺少 KERNEL32 导出符号而无法启动。因此强制使用 go1.21.13 工具链。
set -e

# 强制使用 Go 1.21 工具链（Go 会自动下载，需联网）
export GOTOOLCHAIN=go1.21.13

echo "==> 当前 Go 工具链: $(go version)"
echo "==> 生成 Windows 资源 (manifest + 图标) ..."
go run github.com/akavel/rsrc@latest -arch amd64 -manifest app.manifest -ico icon.ico -o rsrc.syso

echo "==> 交叉编译 Windows amd64 (CGO 关闭，零运行时依赖，Win7 兼容) ..."
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="-s -w -H windowsgui" -o NetConf.exe .

echo "==> 完成: NetConf.exe"
