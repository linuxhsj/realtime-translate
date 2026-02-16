# 实时音频翻译系统 V6

实时捕获系统音频，自动识别语言并翻译，支持多语言选择和 macOS 风格 GUI 界面。

## 特性

- **macOS 风格 GUI**: 简洁白色卡片设计，符合 Apple 设计语言
- **自动监听**: 启动后自动开始捕获音频，无需手动操作
- **双栏显示**: 左侧原文，右侧翻译，实时同步
- **多语言支持**: 支持 10 种语言的识别和翻译
- **实时切换**: 无需重启即可切换语言
- **云端处理**: 使用 NVIDIA Riva ASR + Llama 3.1 翻译

## 支持的语言

### 识别语言 (ASR)
英语、中文、德语、西班牙语、法语、意大利语、日语、韩语、葡萄牙语、俄语

### 翻译语言
中文、英语、日语、韩语、德语、法语、西班牙语、意大利语、葡萄牙语、俄语

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

### 1. 获取 NVIDIA API Key

1. 访问 [NVIDIA NIM](https://build.nvidia.com/)
2. 注册并获取 API Key
3. 设置环境变量:
   ```bash
   export NVIDIA_API_KEY='your-api-key'
   ```

### 2. 设置音频输出

打开 **系统设置 → 声音 → 输出**，创建包含 BlackHole 的多输出设备：

1. 打开 **音频 MIDI 设置** (Audio MIDI Setup)
2. 点击左下角 **+** 创建 **多输出设备**
3. 勾选你的耳机和 BlackHole 2ch
4. 在系统声音设置中选择这个多输出设备

### 3. 验证配置

```bash
# 检查音频设备
ffmpeg -f avfoundation -list_devices true -i ""

# 应该看到 BlackHole 2ch 在音频设备列表中
```

## 使用

```bash
# 设置 API Key
export NVIDIA_API_KEY='your-api-key'

# 方式1: 使用启动脚本
./run.sh

# 方式2: 直接运行
python3 realtime_translate_v6_gui.py
```

## 界面说明

```
┌─────────────────────────────────────────────────────────────┐
│  🎙️ 实时音频翻译                          ● 正在监听        │
├─────────────────────────────────────────────────────────────┤
│  识别语言: [en-US - 英语 ▼]  →  翻译语言: [zh - 中文 ▼]    │
│                                          英语 → 中文         │
├─────────────────────────────────────────────────────────────┤
│  当前识别                                                    │
│  等待语音输入...                                             │
├─────────────────────────────────────────────────────────────┤
│  📝  原文                    │  🎯  翻译                     │
│  ┌──────────────────────────┐│┌────────────────────────────┐│
│  │   实时显示原文            │││   实时显示翻译              ││
│  └──────────────────────────┘│└────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  ASR: --ms  |  翻译: --ms     V6.0  •  NVIDIA Riva + Llama  │
└─────────────────────────────────────────────────────────────┘
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `realtime_translate_v6_gui.py` | V6 GUI 主程序 |
| `run.sh` | 启动脚本 |
| `setup.sh` | 安装脚本 |
| `requirements.txt` | Python 依赖 |

## 技术架构

```
音频捕获 → 音频队列 → NVIDIA Riva ASR → 句子缓冲
                                          ↓
GUI 显示 ← 主线程 ← 翻译队列 ← NVIDIA Llama 翻译
```

- **ASR**: NVIDIA Riva (云端语音识别)
- **翻译**: NVIDIA NIM Llama 3.1 8B (云端翻译)
- **GUI**: Tkinter (macOS 风格)

## 故障排除

### 没有翻译输出

1. 确认 BlackHole 正在接收音频：
   ```bash
   ffmpeg -f avfoundation -i ":0" -t 3 -f wav -y /tmp/test.wav
   # 检查文件大小，应该 > 100KB
   ```

2. 确认系统音频输出包含 BlackHole

3. 播放视频测试

### API 错误

1. 确认 NVIDIA_API_KEY 已正确设置
2. 确认网络连接正常
3. 检查 API Key 是否有效

### 语言识别不准确

在界面下拉菜单中选择正确的识别语言

## 系统要求

- macOS 10.15+
- Python 3.8+
- ffmpeg
- BlackHole 2ch
- NVIDIA API Key
