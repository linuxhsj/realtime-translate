# 实时音频翻译系统 V2

实时捕获系统音频，自动识别语言并翻译，支持双屏显示。

## 特性

- **流式处理**: 使用 VAD (语音活动检测) 实现低延迟翻译
- **双屏显示**: 原文 + 译文并排输出
- **自动语言识别**: 自动检测音频语言
- **离线运行**: 无需网络连接

## 安装

```bash
# 1. 安装 ffmpeg
brew install ffmpeg

# 2. 安装 BlackHole (虚拟音频驱动)
brew install --cask blackhole-2ch

# 3. 安装 Python 依赖
pip3 install -r requirements.txt
```

## 配置

### 1. 设置音频输出

打开 **系统设置 → 声音 → 输出**，创建包含 BlackHole 的多输出设备：

1. 打开 **音频 MIDI 设置** (Audio MIDI Setup)
2. 点击左下角 **+** 创建 **多输出设备**
3. 勾选你的耳机和 BlackHole 2ch
4. 在系统声音设置中选择这个多输出设备

### 2. 验证配置

```bash
# 检查音频设备
ffmpeg -f avfoundation -list_devices true -i ""

# 应该看到 BlackHole 2ch 在音频设备列表中
```

## 使用

```bash
# 启动翻译
./run.sh

# 或直接运行
python3 realtime_translate_v2.py

# 使用不同模型
python3 realtime_translate_v2.py -m small

# 使用麦克风输入
python3 realtime_translate_v2.py -a 1
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-m, --model` | Whisper 模型大小 (tiny/base/small/medium) | base |
| `-a, --audio-device` | 音频设备编号 (0=BlackHole, 1=麦克风) | 0 |

## 输出

翻译结果保存在：
- `/tmp/translation_output.json` - 当前翻译结果
- `/tmp/translation_history.json` - 历史记录

## Übersicht 桌面字幕

1. 安装 Übersicht: `brew install --cask ubersicht`
2. 复制组件: `cp translation-widget-v2.coffee ~/Library/Application\ Support/Übersicht/widgets/`
3. 重启 Übersicht

## 文件说明

| 文件 | 说明 |
|------|------|
| `realtime_translate_v2.py` | 主程序 |
| `run.sh` | 启动脚本 |
| `translation-widget-v2.coffee` | Übersicht 桌面字幕组件 |
| `verify_system.py` | 系统验证脚本 |
| `test_basic.py` | 基础测试脚本 |

## 故障排除

### 没有翻译输出

1. 确认 BlackHole 正在接收音频：
   ```bash
   ffmpeg -f avfoundation -i ":0" -t 3 -f wav -y /tmp/test.wav
   # 检查文件大小，应该 > 100KB
   ```

2. 确认系统音频输出包含 BlackHole

3. 播放 YouTube 视频测试

### 延迟过高

- 使用更小的模型: `-m tiny`
- 检查 CPU 使用率

### 语言识别错误

- 指定源语言: 修改代码中的 `auto_detect = False` 并设置 `language="en"`
