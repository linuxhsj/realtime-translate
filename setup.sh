#!/bin/bash

# Realtime Translation V6 Setup Script
# 实时翻译系统 V6 安装脚本

set -e

echo "🚀 开始安装实时翻译系统 V6"
echo "================================"
echo ""

# 1. 检查 Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew 未安装，请先安装："
    echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi
echo "✅ Homebrew 已安装"

# 2. 检查并安装 ffmpeg
echo ""
echo "📦 检查 ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "安装 ffmpeg..."
    brew install ffmpeg
else
    echo "✅ ffmpeg 已安装"
fi

# 3. 检查 Python
echo ""
echo "📦 检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION 已安装"

# 4. 安装 Python 依赖
echo ""
echo "📦 安装 Python 依赖..."
pip3 install -r "$(dirname "$0")/requirements.txt" --quiet 2>/dev/null || \
    pip install -r "$(dirname "$0")/requirements.txt" --quiet 2>/dev/null || \
    echo "⚠️  部分 Python 依赖安装失败，请手动安装"

echo "✅ Python 依赖安装完成"

# 5. 检查 BlackHole
echo ""
echo "📦 检查 BlackHole 虚拟音频驱动..."
if ! system_profiler SPAudioDataType 2>/dev/null | grep -q "BlackHole"; then
    echo "⚠️  BlackHole 未安装"
    echo ""
    echo "请手动安装 BlackHole:"
    echo "  brew install --cask blackhole-2ch"
    echo ""
    echo "安装后需要重启电脑，并在系统设置中将音频输出改为 BlackHole"
else
    echo "✅ BlackHole 已安装"
fi

# 6. 检查 NVIDIA API Key
echo ""
echo "📦 检查 NVIDIA API Key..."
if [ -z "$NVIDIA_API_KEY" ]; then
    echo "⚠️  NVIDIA_API_KEY 未设置"
    echo ""
    echo "请设置环境变量:"
    echo "  export NVIDIA_API_KEY='your-api-key'"
    echo ""
    echo "获取 API Key: https://build.nvidia.com/"
else
    echo "✅ NVIDIA_API_KEY 已设置"
fi

# 完成
echo ""
echo "================================"
echo "🎉 安装完成！"
echo ""
echo "📋 使用方法:"
echo "1. 确保系统音频输出设置为 BlackHole (多输出设备)"
echo "2. 设置 NVIDIA API Key:"
echo "   export NVIDIA_API_KEY='your-api-key'"
echo "3. 运行: ./run.sh"
echo "   或: python3 realtime_translate_v6_gui.py"
echo ""
echo "🌐 支持的语言:"
echo "   识别: 英语、中文、德语、西班牙语、法语、意大利语、日语、韩语等"
echo "   翻译: 中文、英语、日语、韩语、德语、法语、西班牙语等"
echo ""
