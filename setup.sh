#!/bin/bash

# Realtime Translation V2 Setup Script
# 实时翻译系统 V2 安装脚本

set -e

echo "🚀 开始安装实时翻译系统 V2"
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

# 6. 安装 Übersicht 组件
echo ""
echo "📦 安装 Übersicht 组件..."
UBERSICHT_WIDGETS="$HOME/Library/Application Support/Übersicht/widgets"

if [ -d "$UBERSICHT_WIDGETS" ]; then
    WIDGET_DIR="$UBERSICHT_WIDGETS/translation-widget-v2"
    mkdir -p "$WIDGET_DIR"
    
    cp "$(dirname "$0")/translation-widget-v2.coffee" "$WIDGET_DIR/index.coffee"
    
    echo "✅ Übersicht 组件已安装到: $WIDGET_DIR"
else
    echo "⚠️  Übersicht 未安装，跳过组件安装"
    echo "   如需桌面字幕显示，请安装: brew install --cask ubersicht"
fi

# 7. 创建便捷启动脚本
echo ""
echo "📦 创建启动脚本..."
SCRIPT_DIR="$(dirname "$0")"
START_SCRIPT="$SCRIPT_DIR/start.sh"

cat > "$START_SCRIPT" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python3 realtime_translate_v2.py "$@"
EOF

chmod +x "$START_SCRIPT"
echo "✅ 启动脚本已创建: $START_SCRIPT"

# 完成
echo ""
echo "================================"
echo "🎉 安装完成！"
echo ""
echo "📋 使用方法:"
echo "1. 确保系统音频输出设置为 BlackHole"
echo "2. 运行: ./start.sh"
echo "   或: python3 realtime_translate_v2.py"
echo ""
echo "⚙️  可选参数:"
echo "   -m, --model    模型大小: tiny/base/small/medium"
echo "   -d, --device   计算设备: auto/cpu/cuda"
echo ""
echo "💡 示例:"
echo "   ./start.sh -m small -d cuda"
echo ""
