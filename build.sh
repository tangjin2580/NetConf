#!/usr/bin/env bash
# 在 macOS / Linux 上交叉编译 Windows 64 位静态可执行文件（兼容 Windows 7）
# 用法: ./build.sh
# 注意: Go 1.20 是最后一个支持 Windows 7/8/8.1 的版本；
#       Go 1.21+ 编译出的 exe 会在 Win7 上因运行时不兼容而直接崩溃。
#       因此强制使用 go1.20.14 工具链。
set -e

# 强制使用 Go 1.20 工具链（最后一个支持 Win7 的版本）
export GOTOOLCHAIN=go1.20.14

echo "==> 当前 Go 工具链: $(go version)"
echo "==> 生成 Windows 资源 (manifest + 图标) ..."
go run github.com/akavel/rsrc@latest -arch amd64 -manifest app.manifest -ico icon.ico -o rsrc.syso

echo "==> 交叉编译 Windows amd64 (CGO 关闭，零运行时依赖，Win7 兼容) ..."
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="-s -w -H windowsgui" -o NetConf.exe .

echo "==> 完成: NetConf.exe"
