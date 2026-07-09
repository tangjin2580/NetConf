#!/usr/bin/env bash
# 在 macOS / Linux 上交叉编译 Windows 64 位静态可执行文件
# 用法: ./build.sh
set -e

echo "==> 生成 Windows 资源 (manifest + 图标) ..."
go run github.com/akavel/rsrc@latest -arch amd64 -manifest app.manifest -ico icon.ico -o rsrc.syso

echo "==> 交叉编译 Windows amd64 (CGO 关闭，零运行时依赖) ..."
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="-s -w -H windowsgui" -o NetConf.exe .

echo "==> 完成: NetConf.exe"
