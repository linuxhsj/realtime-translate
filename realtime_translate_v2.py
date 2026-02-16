#!/usr/bin/env python3
"""
实时音频翻译系统 V2 - 使用 NLLB 实时翻译
特性:
1. 流式处理 - 降低延迟
2. 双屏显示 - 原文 + 译文并排输出
3. 自动语言识别 - 自动检测音频语言
4. 实时翻译 - 使用 NLLB 模型翻译成中文

依赖: pip install openai-whisper numpy nllw
"""

import subprocess
import os
import sys
import json
import time
import wave
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from collections import deque
import numpy as np

os.environ["TOKENIZERS_PARALLELISM"] = "false"

try:
    import whisper
except ImportError:
    print("❌ 请安装 openai-whisper: pip install openai-whisper")
    sys.exit(1)

try:
    import nllw
except ImportError:
    print("❌ 请安装 nllw: pip install nllw")
    sys.exit(1)


@dataclass
class TranslationResult:
    original: str
    translated: str
    language: str
    language_prob: float
    timestamp: str
    latency_ms: float


class OpusTranslator:
    """OPUS-MT 翻译器 (更小更快, ~300MB)"""
    
    def __init__(self):
        self.pipeline = None
        self.model_map = {
            "en": "Helsinki-NLP/opus-mt-en-zh",
            "ja": "Helsinki-NLP/opus-mt-ja-zh",
            "ko": "Helsinki-NLP/opus-mt-ko-zh",
            "fr": "Helsinki-NLP/opus-mt-fr-zh",
            "de": "Helsinki-NLP/opus-mt-de-zh",
            "es": "Helsinki-NLP/opus-mt-es-zh",
            "ru": "Helsinki-NLP/opus-mt-ru-zh",
        }
        self.loaded_lang = None
        
    def check_cache(self):
        """检查模型缓存状态"""
        cache_path = os.path.expanduser("~/.cache/huggingface/hub/models--Helsinki-NLP--opus-mt-en-zh")
        if os.path.exists(cache_path):
            size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(cache_path)
                for filename in filenames
            )
            size_mb = size / (1024 * 1024)
            if size_mb > 100:
                return f"✅ 已缓存 ({size_mb:.0f}MB)"
            else:
                return f"⏳ 部分缓存 ({size_mb:.0f}MB)"
        return "❌ 未缓存 (需要下载 ~300MB)"

    def load_model(self):
        """加载翻译模型"""
        from transformers import pipeline
        print("📦 加载 OPUS-MT 翻译模型 (更小更快)...")
        cache_status = self.check_cache()
        print(f"   缓存状态: {cache_status}")
        print(f"   缓存位置: ~/.cache/huggingface/hub/")
        try:
            print("   [1/2] 加载英中翻译模型...")
            self.pipeline = pipeline(
                "translation",
                model="Helsinki-NLP/opus-mt-en-zh",
                device="cpu"
            )
            self.loaded_lang = "en"
            print("   [2/2] 完成!")
            print("✅ OPUS-MT 翻译模型加载完成 (~300MB)")
            return True
        except Exception as e:
            print(f"⚠️ OPUS-MT 加载失败: {e}")
            return False
    
    def translate(self, text: str, source_lang: str) -> str:
        """翻译文本到中文"""
        if not text or not text.strip():
            return text
            
        if source_lang == "zh":
            return text
            
        if self.pipeline is None:
            return text
            
        try:
            if source_lang != "en":
                return text
            
            result = self.pipeline(text, max_length=512)
            if result and len(result) > 0:
                return result[0]["translation_text"]
            return text
        except Exception as e:
            print(f"⚠️ 翻译失败: {e}")
            return text


class NLLBTranslator:
    """NLLB 实时翻译器 (更准确, ~1GB)"""
    
    def __init__(self):
        self.model = None
        self.translator = None
        self.lang_map = {
            "en": "eng_Latn",
            "zh": "zho_Hans",
            "ja": "jpn_Jpan",
            "ko": "kor_Hang",
            "fr": "fra_Latn",
            "de": "deu_Latn",
            "es": "spa_Latn",
            "ru": "rus_Cyrl",
            "pt": "por_Latn",
            "it": "ita_Latn",
        }
        
    def check_cache(self):
        """检查模型缓存状态"""
        cache_path = os.path.expanduser("~/.cache/huggingface/hub/models--facebook--nllb-200-distilled-600M")
        if os.path.exists(cache_path):
            size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(cache_path)
                for filename in filenames
            )
            size_mb = size / (1024 * 1024)
            if size_mb > 500:
                return f"✅ 已缓存 ({size_mb:.0f}MB)"
            else:
                return f"⏳ 部分缓存 ({size_mb:.0f}MB)"
        return "❌ 未缓存 (需要下载 ~1GB)"

    def load_model(self):
        """加载翻译模型"""
        print("📦 加载 NLLB 翻译模型 (更准确)...")
        cache_status = self.check_cache()
        print(f"   缓存状态: {cache_status}")
        print(f"   缓存位置: ~/.cache/huggingface/hub/")
        try:
            print("   [1/3] 加载模型...")
            self.model = nllw.load_model(
                src_langs=["eng_Latn", "fra_Latn", "deu_Latn", "spa_Latn", "jpn_Jpan", "kor_Hang"],
                nllb_backend="transformers",
                nllb_size="600M"
            )
            print("   [2/3] 初始化翻译器...")
            self.translator = nllw.OnlineTranslation(
                self.model,
                input_languages=["eng_Latn", "fra_Latn", "deu_Latn", "spa_Latn", "jpn_Jpan", "kor_Hang"],
                output_languages=["zho_Hans"]
            )
            print("   [3/3] 完成!")
            print("✅ NLLB 翻译模型加载完成")
            return True
        except Exception as e:
            print(f"⚠️ NLLB 加载失败: {e}")
            print("将使用 Whisper 内置翻译（仅支持翻译成英文）")
            return False
    
    def translate(self, text: str, source_lang: str) -> str:
        """翻译文本到中文"""
        if not text or not text.strip():
            return text
            
        if source_lang == "zh":
            return text
            
        nllb_lang = self.lang_map.get(source_lang, "eng_Latn")
        
        if self.translator is None:
            return text
            
        try:
            tokens = [nllw.timed_text.TimedText(text)]
            self.translator.insert_tokens(tokens)
            validated, buffer = self.translator.process()
            if validated:
                if hasattr(validated, 'text'):
                    return validated.text
                return str(validated)
            return text
        except Exception as e:
            print(f"⚠️ 翻译失败: {e}")
            return text


class StreamingTranslator:
    """流式翻译器 - 使用 Whisper + 翻译模型"""
    
    def __init__(self, model_size: str = "base", translator_type: str = "opus"):
        self.model_size = model_size
        self.translator_type = translator_type
        self.whisper_model = None
        self.translator = None
        
    def load_model(self):
        """加载模型"""
        print(f"📦 加载 Whisper {self.model_size} 模型...")
        self.whisper_model = whisper.load_model(self.model_size)
        print("✅ Whisper 模型加载完成")
        
        if self.translator_type == "nllb":
            self.translator = NLLBTranslator()
        else:
            self.translator = OpusTranslator()
        self.translator.load_model()
        
    def transcribe(self, audio: np.ndarray) -> tuple:
        """语音识别 - 返回 (原文, 语言)"""
        detect_result = self.whisper_model.transcribe(
            audio,
            task="transcribe",
            fp16=False,
            verbose=False
        )
        original_text = detect_result.get("text", "").strip()
        detected_lang = detect_result.get("language", "en")
        return original_text, detected_lang
        
    def translate_text(self, text: str, source_lang: str) -> str:
        """翻译文本"""
        if not text or source_lang == "zh":
            return text
        return self.translator.translate(text, source_lang)
        
    def translate(self, audio: np.ndarray) -> TranslationResult:
        """完整翻译流程"""
        start_time = time.time()
        
        original_text, detected_lang = self.transcribe(audio)
        
        if not original_text:
            return None
            
        translated_text = self.translate_text(original_text, detected_lang)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return TranslationResult(
            original=original_text,
            translated=translated_text,
            language=detected_lang,
            language_prob=0.9,
            timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
            latency_ms=latency_ms
        )


class DualScreenDisplay:
    """双屏显示模块"""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history = deque(maxlen=max_history)
        self.output_file = "/tmp/translation_output.json"
        
    def display_original(self, text: str, lang: str):
        """先显示原文"""
        print("\n" + "─" * 60)
        print(f"📝 原文 ({lang.upper()}): {text}")
        print("⏳ 翻译中...", end="", flush=True)
        
    def display_translation(self, result: TranslationResult):
        """显示翻译结果"""
        self.history.append(result)
        
        print(f"\r🎯 译文: {result.translated}")
        print("─" * 60)
        
        self._save_to_file(result)
        
    def display(self, result: TranslationResult):
        """显示翻译结果"""
        self.history.append(result)
        
        print("\n" + "─" * 60)
        print(f"⏰ [{result.timestamp}] | 🌐 {result.language.upper()} | ⚡ {result.latency_ms:.0f}ms")
        print("─" * 60)
        print(f"📝 原文: {result.original}")
        print(f"🎯 译文: {result.translated}")
        print("─" * 60)
        
        self._save_to_file(result)
        
    def _save_to_file(self, result: TranslationResult):
        """保存结果到文件"""
        output = {
            "timestamp": result.timestamp,
            "original": result.original,
            "translated": result.translated,
            "language": result.language,
            "language_prob": result.language_prob,
            "latency_ms": result.latency_ms
        }
        
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)


class RealtimeTranslator:
    """实时翻译系统主类"""
    
    def __init__(self, 
                 model_size: str = "base",
                 audio_device: str = "0",
                 chunk_duration: int = 2,
                 translator_type: str = "opus"):
        self.model_size = model_size
        self.audio_device = audio_device
        self.chunk_duration = chunk_duration
        self.translator_type = translator_type
        self.running = False
        
        self.translator = StreamingTranslator(model_size, translator_type)
        self.display = DualScreenDisplay()
        
    def start(self):
        """启动实时翻译"""
        translator_name = "OPUS-MT" if self.translator_type == "opus" else "NLLB"
        print("=" * 60)
        print(f"🎙️  实时音频翻译系统 V2 - {translator_name}版")
        print("=" * 60)
        print("特性: 流式处理 | 双屏显示 | 自动语言识别 | 实时翻译")
        print("=" * 60)
        
        if not self._check_dependencies():
            return
        
        self.translator.load_model()
        
        print(f"\n🚀 开始监听音频 (每 {self.chunk_duration} 秒处理一次)...")
        print("💡 提示: 非中文音频会自动翻译成中文")
        print("⏹️  按 Ctrl+C 停止\n")
        
        self.running = True
        self._process_loop()
        
    def _check_dependencies(self) -> bool:
        """检查依赖"""
        try:
            result = subprocess.run(
                ["which", "ffmpeg"],
                capture_output=True
            )
            if result.returncode != 0:
                print("❌ ffmpeg 未安装，请先安装: brew install ffmpeg")
                return False
        except Exception:
            print("❌ 检查依赖失败")
            return False
        return True
    
    def _process_loop(self):
        """主处理循环"""
        temp_file = "/tmp/realtime_chunk.wav"
        
        try:
            while self.running:
                cmd = [
                    "ffmpeg",
                    "-f", "avfoundation",
                    "-i", f":{self.audio_device}",
                    "-ar", "16000",
                    "-ac", "1",
                    "-t", str(self.chunk_duration),
                    "-y", temp_file
                ]
                
                result = subprocess.run(cmd, capture_output=True)
                
                if os.path.exists(temp_file):
                    size = os.path.getsize(temp_file)
                    if size > 10000:
                        self._process_audio_file(temp_file)
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def _process_audio_file(self, filepath: str):
        """处理音频文件"""
        try:
            with wave.open(filepath, 'rb') as f:
                frames = f.getnframes()
                rate = f.getframerate()
                data = f.readframes(frames)
                audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            
            energy = np.sqrt(np.mean(audio ** 2))
            
            if energy > 0.0005:
                original_text, detected_lang = self.translator.transcribe(audio)
                
                if original_text:
                    self.display.display_original(original_text, detected_lang)
                    translated_text = self.translator.translate_text(original_text, detected_lang)
                    
                    latency_ms = 0
                    result = TranslationResult(
                        original=original_text,
                        translated=translated_text,
                        language=detected_lang,
                        language_prob=0.9,
                        timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                        latency_ms=latency_ms
                    )
                    self.display.display_translation(result)
            else:
                print(f"🔇 静音 (能量: {energy:.6f})")
                
        except Exception as e:
            print(f"❌ 处理错误: {e}")
    
    def stop(self):
        """停止翻译"""
        self.running = False
        print("\n🛑 翻译已停止")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="实时音频翻译系统 V2")
    parser.add_argument(
        "-m", "--model",
        default="tiny",
        choices=["tiny", "base", "small", "medium"],
        help="Whisper 模型大小 (default: tiny, 最快)"
    )
    parser.add_argument(
        "-a", "--audio-device",
        default="0",
        help="音频输入设备编号 (0=BlackHole, default: 0)"
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=2,
        help="音频分块时长/秒 (default: 2, 越小延迟越低)"
    )
    parser.add_argument(
        "-t", "--translator",
        default="opus",
        choices=["opus", "nllb"],
        help="翻译模型: opus=更快更小(~300MB), nllb=更准确(~1GB) (default: opus)"
    )
    
    args = parser.parse_args()
    
    translator = RealtimeTranslator(
        model_size=args.model,
        audio_device=args.audio_device,
        chunk_duration=args.duration,
        translator_type=args.translator
    )
    
    try:
        translator.start()
    except KeyboardInterrupt:
        print("\n")
        translator.stop()


if __name__ == "__main__":
    main()
