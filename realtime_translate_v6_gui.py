#!/usr/bin/env python3
"""
实时音频翻译系统 V6 - macOS 风格 GUI 版本
特性:
1. macOS 风格界面
2. 双栏显示（原文 + 翻译）
3. NVIDIA Riva ASR 云端语音识别
4. NVIDIA Llama 翻译
5. 自动开始监听

依赖: pip install openai numpy riva-client tkinter
"""

import subprocess
import os
import sys
import json
import time
import threading
import queue
from datetime import datetime
from typing import Optional
import numpy as np
import re
import warnings

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "false"
warnings.filterwarnings("ignore")

try:
    from openai import OpenAI
except ImportError:
    print("❌ 请安装: pip install openai")
    sys.exit(1)

try:
    import riva.client
    import riva.client.proto.riva_asr_pb2 as rasr
    import riva.client.proto.riva_audio_pb2 as ra
    RIVA_AVAILABLE = True
except ImportError:
    RIVA_AVAILABLE = False

import tkinter as tk
from tkinter import ttk, scrolledtext


class RivaASR:
    LANGUAGES = {
        'en-US': '英语',
        'zh-CN': '中文',
        'de-DE': '德语',
        'es-ES': '西班牙语',
        'fr-FR': '法语',
        'it-IT': '意大利语',
        'ja-JP': '日语',
        'ko-KR': '韩语',
        'pt-BR': '葡萄牙语',
        'ru-RU': '俄语'
    }
    
    def __init__(self, api_key: str, language: str = "en-US"):
        if not RIVA_AVAILABLE:
            raise ImportError("riva-client 未安装")
        
        self.api_key = api_key
        self.language = language
        self.server = "grpc.nvcf.nvidia.com:443"
        self.function_id = "1598d209-5e27-4d3c-8079-4751568b1081"
        
        self.auth = riva.client.Auth(
            uri=self.server,
            use_ssl=True,
            metadata_args=[
                ("function-id", self.function_id),
                ("authorization", f"Bearer {api_key}")
            ]
        )
        self.asr_service = riva.client.ASRService(self.auth)
    
    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> tuple:
        try:
            audio_bytes = (audio * 32768).astype(np.int16).tobytes()
            
            config = rasr.RecognitionConfig(
                encoding=ra.AudioEncoding.LINEAR_PCM,
                sample_rate_hertz=sample_rate,
                language_code=self.language,
                max_alternatives=1,
                enable_automatic_punctuation=True
            )
            
            response = self.asr_service.offline_recognize(audio_bytes, config)
            
            if response.results:
                text = response.results[0].alternatives[0].transcript
                return text.strip(), self.language.split('-')[0]
            return "", self.language.split('-')[0]
        except Exception as e:
            return "", self.language.split('-')[0]


class NVIDIATranslator:
    TARGET_LANGUAGES = {
        'zh': '中文',
        'en': '英语',
        'ja': '日语',
        'ko': '韩语',
        'de': '德语',
        'fr': '法语',
        'es': '西班牙语',
        'it': '意大利语',
        'pt': '葡萄牙语',
        'ru': '俄语'
    }
    
    def __init__(self, api_key: str):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        self.model = "meta/llama-3.1-8b-instruct"
    
    def translate(self, text: str, source_lang: str = "en", target_lang: str = "zh") -> str:
        if not text or not text.strip():
            return ""
        
        try:
            lang_names = {
                'en': 'English', 'zh': 'Chinese', 'ja': 'Japanese',
                'ko': 'Korean', 'de': 'German', 'fr': 'French',
                'es': 'Spanish', 'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian'
            }
            source_name = lang_names.get(source_lang, source_lang)
            target_name = lang_names.get(target_lang, target_lang)
            
            prompt = f"Translate the following {source_name} text to {target_name}. Only output the translation, no explanations:\n\n{text}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[翻译错误: {e}]"


class SentenceBuffer:
    def __init__(self, timeout: float = 1.5):
        self.buffer = ""
        self.timeout = timeout
        self.last_update = 0
        self.word_count = 0
        self.sentence_end_pattern = re.compile(r'[.!?。！？]$')
        
    def add(self, text: str) -> tuple:
        if not text:
            return None, False
        
        now = time.time()
        
        if self.buffer:
            self.buffer += " " + text.strip()
        else:
            self.buffer = text.strip()
        
        self.word_count = len(self.buffer.split())
        self.last_update = now
        
        if self.sentence_end_pattern.search(self.buffer.strip()):
            result = self.buffer.strip()
            self.buffer = ""
            self.word_count = 0
            return result, True
        
        return None, False
    
    def check_sentence_end(self) -> tuple:
        now = time.time()
        
        if self.buffer and now - self.last_update > self.timeout:
            result = self.buffer.strip()
            self.buffer = ""
            self.word_count = 0
            return result, True
        
        return None, False
    
    def get_current(self) -> str:
        return self.buffer.strip()
    
    def flush(self) -> Optional[str]:
        if self.buffer:
            result = self.buffer.strip()
            self.buffer = ""
            self.word_count = 0
            return result
        return None


class TranslationGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("实时音频翻译")
        self.root.geometry("1300x900")
        self.root.configure(bg='#f5f5f7')
        
        self.running = True
        self.asr = None
        self.translator = None
        self.sentence_buffer = SentenceBuffer()
        
        self.audio_queue = queue.Queue(maxsize=5)
        self.translate_queue = queue.Queue(maxsize=10)
        
        self.current_original = ""
        self.history = []
        
        self.source_lang = tk.StringVar(value="en-US")
        self.target_lang = tk.StringVar(value="zh")
        
        self._setup_ui()
        
        self.root.after(100, self._start_listening)
    
    def _setup_ui(self):
        main_container = tk.Frame(self.root, bg='#f5f5f7')
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        header_frame = tk.Frame(main_container, bg='#ffffff')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_container = tk.Frame(header_frame, bg='#ffffff')
        title_container.pack(fill=tk.X, padx=25, pady=20)
        
        title_label = tk.Label(
            title_container,
            text="🎙️ 实时音频翻译",
            font=('Helvetica', 32, 'bold'),
            fg='#1d1d1f',
            bg='#ffffff'
        )
        title_label.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(
            title_container,
            text="● 初始化中...",
            font=('Helvetica', 20, 'bold'),
            fg='#ff9500',
            bg='#ffffff'
        )
        self.status_label.pack(side=tk.RIGHT)
        
        lang_frame = tk.Frame(main_container, bg='#e8f4fd')
        lang_frame.pack(fill=tk.X, pady=(0, 20))
        
        lang_container = tk.Frame(lang_frame, bg='#e8f4fd')
        lang_container.pack(fill=tk.X, padx=25, pady=15)
        
        source_label = tk.Label(
            lang_container,
            text="识别语言:",
            font=('Helvetica', 14, 'bold'),
            fg='#1d1d1f',
            bg='#e8f4fd'
        )
        source_label.pack(side=tk.LEFT, padx=(0, 10))
        
        style = ttk.Style()
        style.configure('Custom.TCombobox', font=('Helvetica', 14))
        
        self.source_combo = ttk.Combobox(
            lang_container,
            textvariable=self.source_lang,
            values=[f"{code} - {name}" for code, name in RivaASR.LANGUAGES.items()],
            state='readonly',
            width=18,
            font=('Helvetica', 14)
        )
        self.source_combo.set("en-US - 英语")
        self.source_combo.pack(side=tk.LEFT, padx=(0, 30))
        self.source_combo.bind('<<ComboboxSelected>>', self._on_language_change)
        
        arrow_label = tk.Label(
            lang_container,
            text="→",
            font=('Helvetica', 20, 'bold'),
            fg='#0071e3',
            bg='#e8f4fd'
        )
        arrow_label.pack(side=tk.LEFT, padx=(0, 30))
        
        target_label = tk.Label(
            lang_container,
            text="翻译语言:",
            font=('Helvetica', 14, 'bold'),
            fg='#1d1d1f',
            bg='#e8f4fd'
        )
        target_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.target_combo = ttk.Combobox(
            lang_container,
            textvariable=self.target_lang,
            values=[f"{code} - {name}" for code, name in NVIDIATranslator.TARGET_LANGUAGES.items()],
            state='readonly',
            width=18,
            font=('Helvetica', 14)
        )
        self.target_combo.set("zh - 中文")
        self.target_combo.pack(side=tk.LEFT, padx=(0, 30))
        self.target_combo.bind('<<ComboboxSelected>>', self._on_language_change)
        
        self.lang_status = tk.Label(
            lang_container,
            text="英语 → 中文",
            font=('Helvetica', 16, 'bold'),
            fg='#0071e3',
            bg='#e8f4fd'
        )
        self.lang_status.pack(side=tk.RIGHT)
        
        current_frame = tk.Frame(main_container, bg='#ffffff')
        current_frame.pack(fill=tk.X, pady=(0, 20))
        
        current_container = tk.Frame(current_frame, bg='#ffffff')
        current_container.pack(fill=tk.X, padx=25, pady=20)
        
        current_title = tk.Label(
            current_container,
            text="当前识别",
            font=('Helvetica', 13),
            fg='#86868b',
            bg='#ffffff'
        )
        current_title.pack(anchor=tk.W)
        
        self.current_text = tk.Label(
            current_container,
            text="正在初始化...",
            font=('Helvetica', 20),
            fg='#1d1d1f',
            bg='#ffffff',
            anchor=tk.W,
            pady=10
        )
        self.current_text.pack(fill=tk.X)
        
        dual_frame = tk.Frame(main_container, bg='#f5f5f7')
        dual_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = tk.Frame(dual_frame, bg='#ffffff')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        left_container = tk.Frame(left_frame, bg='#ffffff')
        left_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        left_title = tk.Label(
            left_container,
            text="📝  原文",
            font=('Helvetica', 16, 'bold'),
            fg='#0071e3',
            bg='#ffffff'
        )
        left_title.pack(anchor=tk.W, pady=(0, 10))
        
        text_frame = tk.Frame(left_container, bg='#fafafa')
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.original_text = scrolledtext.ScrolledText(
            text_frame,
            font=('Helvetica', 18),
            fg='#1d1d1f',
            bg='#fafafa',
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=15,
            pady=15,
            spacing1=8,
            spacing3=8,
            borderwidth=0
        )
        self.original_text.pack(fill=tk.BOTH, expand=True)
        self.original_text.config(state=tk.DISABLED)
        
        right_frame = tk.Frame(dual_frame, bg='#ffffff')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        right_container = tk.Frame(right_frame, bg='#ffffff')
        right_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        right_title = tk.Label(
            right_container,
            text="🎯  翻译",
            font=('Helvetica', 16, 'bold'),
            fg='#34c759',
            bg='#ffffff'
        )
        right_title.pack(anchor=tk.W, pady=(0, 10))
        
        trans_frame = tk.Frame(right_container, bg='#fafafa')
        trans_frame.pack(fill=tk.BOTH, expand=True)
        
        self.translated_text = scrolledtext.ScrolledText(
            trans_frame,
            font=('Helvetica', 18),
            fg='#1d1d1f',
            bg='#fafafa',
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=15,
            pady=15,
            spacing1=8,
            spacing3=8,
            borderwidth=0
        )
        self.translated_text.pack(fill=tk.BOTH, expand=True)
        self.translated_text.config(state=tk.DISABLED)
        
        footer_frame = tk.Frame(main_container, bg='#f5f5f7')
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.stats_label = tk.Label(
            footer_frame,
            text="ASR: --ms  |  翻译: --ms",
            font=('Helvetica', 13),
            fg='#86868b',
            bg='#f5f5f7'
        )
        self.stats_label.pack(side=tk.LEFT)
        
        version_label = tk.Label(
            footer_frame,
            text="V6.0  •  NVIDIA Riva ASR + Llama 3.1",
            font=('Helvetica', 13),
            fg='#86868b',
            bg='#f5f5f7'
        )
        version_label.pack(side=tk.RIGHT)
    
    def _update_status(self, text: str, color: str):
        self.status_label.config(text=text, fg=color)
    
    def _on_language_change(self, event=None):
        source_val = self.source_combo.get()
        target_val = self.target_combo.get()
        
        source_code = source_val.split(' - ')[0]
        target_code = target_val.split(' - ')[0]
        
        source_name = RivaASR.LANGUAGES.get(source_code, source_code)
        target_name = NVIDIATranslator.TARGET_LANGUAGES.get(target_code, target_code)
        
        self.lang_status.config(text=f"{source_name} → {target_name}")
        
        if self.asr:
            self.asr.language = source_code
    
    def _update_stats(self, asr_ms: float, trans_ms: float = 0):
        self.stats_label.config(text=f"ASR: {asr_ms:.0f}ms  |  翻译: {trans_ms:.0f}ms")
    
    def _append_original(self, text: str):
        self.original_text.config(state=tk.NORMAL)
        self.original_text.insert(tk.END, text + "\n\n")
        self.original_text.see(tk.END)
        self.original_text.config(state=tk.DISABLED)
    
    def _append_translated(self, text: str):
        self.translated_text.config(state=tk.NORMAL)
        self.translated_text.insert(tk.END, text + "\n\n")
        self.translated_text.see(tk.END)
        self.translated_text.config(state=tk.DISABLED)
    
    def _update_current(self, text: str):
        self.current_text.config(text=text if text else "等待语音输入...")
    
    def _start_listening(self):
        self.nvidia_key = os.environ.get("NVIDIA_API_KEY")
        if not self.nvidia_key:
            self._update_status("❌ 请设置 NVIDIA_API_KEY", '#ff3b30')
            self._update_current("错误: 未设置 API Key")
            return
        
        self._update_status("● 初始化中...", '#ff9500')
        
        try:
            source_code = self.source_combo.get().split(' - ')[0]
            self.asr = RivaASR(self.nvidia_key, language=source_code)
            self.translator = NVIDIATranslator(self.nvidia_key)
            self._update_status("● 正在监听", '#34c759')
            self._update_current("等待语音输入...")
        except Exception as e:
            self._update_status(f"❌ 初始化失败", '#ff3b30')
            self._update_current(f"错误: {e}")
            return
        
        audio_thread = threading.Thread(target=self._audio_capture_worker, daemon=True)
        asr_thread = threading.Thread(target=self._asr_worker, daemon=True)
        translate_thread = threading.Thread(target=self._translate_worker, daemon=True)
        
        audio_thread.start()
        asr_thread.start()
        translate_thread.start()
    
    def _audio_capture_worker(self):
        frame_count = 0
        while self.running:
            try:
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "avfoundation",
                    "-i", ":0",
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    "-f", "s16le",
                    "-t", "1.5",
                    "-"
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                frame_count += 1
                
                audio_len = len(result.stdout)
                
                if audio_len > 1000:
                    audio = np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    energy = np.sqrt(np.mean(audio ** 2))
                    if energy > 0.00001:
                        try:
                            self.audio_queue.put((audio, energy), timeout=0.3)
                        except queue.Full:
                            pass
                            
            except subprocess.TimeoutExpired:
                continue
            except Exception as e:
                pass
    
    def _asr_worker(self):
        while self.running:
            try:
                audio, energy = self.audio_queue.get(timeout=1.0)
                
                start_time = time.time()
                
                original_text, detected_lang = self.asr.transcribe(audio)
                
                if original_text:
                    asr_latency = (time.time() - start_time) * 1000
                    
                    sentence, is_end = self.sentence_buffer.add(original_text)
                    current_text = self.sentence_buffer.get_current()
                    
                    self.root.after(0, self._update_current, current_text)
                    self.root.after(0, self._update_stats, asr_latency, 0)
                    
                    if not is_end:
                        sentence, is_end = self.sentence_buffer.check_sentence_end()
                    
                    if is_end and sentence:
                        self.root.after(0, self._append_original, sentence)
                        self.root.after(0, self._update_current, "")
                        
                        target_code = self.target_combo.get().split(' - ')[0]
                        source_code = self.source_combo.get().split(' - ')[0]
                        if detected_lang != target_code:
                            try:
                                self.translate_queue.put((sentence, source_code, target_code), timeout=0.3)
                            except queue.Full:
                                pass
                                    
            except queue.Empty:
                pass
            except Exception as e:
                pass
    
    def _translate_worker(self):
        while self.running:
            try:
                sentence, source_lang, target_lang = self.translate_queue.get(timeout=0.3)
                
                if sentence:
                    start_time = time.time()
                    translated = self.translator.translate(sentence, source_lang, target_lang)
                    trans_latency = (time.time() - start_time) * 1000
                    
                    if translated:
                        self.root.after(0, self._append_translated, translated)
                        self.root.after(0, self._update_stats, 0, trans_latency)
                        
            except queue.Empty:
                continue
            except Exception as e:
                pass
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = TranslationGUI()
    app.run()
