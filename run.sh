#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================================"
echo "🎙️  实时音频翻译系统 V6 - 启动脚本"
echo "============================================================"

echo ""
echo "📋 检查系统环境..."

if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg 未安装，请运行: brew install ffmpeg"
    exit 1
fi
echo "✅ ffmpeg 已安装"

if [ -z "$NVIDIA_API_KEY" ]; then
    echo ""
    echo "⚠️  NVIDIA_API_KEY 未设置"
    echo "请运行: export NVIDIA_API_KEY='your-api-key'"
    echo ""
fi

echo ""
echo "📋 检查音频设备..."
ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -E "^\[AVFoundation.*audio" | head -5

echo ""
echo "============================================================"
echo "💡 使用说明:"
echo "============================================================"
echo ""
echo "1. 确保系统音频输出包含 BlackHole (多输出设备)"
echo "2. 播放视频或音频源"
echo "3. 程序会自动检测语音并翻译"
echo ""
echo "支持的语言:"
echo "  识别: 英语、中文、德语、西班牙语、法语、意大利语、日语、韩语等"
echo "  翻译: 中文、英语、日语、韩语、德语、法语、西班牙语等"
echo ""
echo "============================================================"
echo ""

cd "$SCRIPT_DIR"
python3 realtime_translate_v6_gui.py
