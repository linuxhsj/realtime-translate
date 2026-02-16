#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================================"
echo "🎙️  实时音频翻译系统 V2 - 启动脚本"
echo "============================================================"

echo ""
echo "📋 检查系统环境..."

if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg 未安装，请运行: brew install ffmpeg"
    exit 1
fi
echo "✅ ffmpeg 已安装"

if ! python3 -c "import whisper" 2>/dev/null; then
    echo "⚠️  openai-whisper 未安装，正在安装..."
    pip3 install openai-whisper numpy --quiet
fi
echo "✅ Python 依赖已安装"

echo ""
echo "📋 检查音频设备..."
ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -E "^\[AVFoundation.*audio" | head -5

echo ""
echo "============================================================"
echo "💡 使用说明:"
echo "============================================================"
echo ""
echo "1. 确保系统音频输出包含 BlackHole (多输出设备)"
echo "2. 播放 YouTube 或其他英文音频源"
echo "3. 程序会自动检测语音并翻译"
echo ""
echo "参数说明:"
echo "  -m, --model      模型大小: tiny/base/small/medium (默认: base)"
echo "  -a, --audio-device  音频设备编号 (默认: 0=BlackHole)"
echo ""
echo "示例:"
echo "  ./run.sh                    # 使用默认设置"
echo "  ./run.sh -m small           # 使用 small 模型"
echo "  ./run.sh -a 1               # 使用麦克风输入"
echo ""
echo "============================================================"
echo ""

cd "$SCRIPT_DIR"
python3 realtime_translate_v2.py "$@"
