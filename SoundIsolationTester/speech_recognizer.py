# -*- coding: utf-8 -*-
import os
import json
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List
import warnings
warnings.filterwarnings('ignore')

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Whisper не установлен")

try:
    from vosk import Model, KaldiRecognizer
    import wave
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("⚠️ Vosk не установлен")

try:
    import speech_recognition as sr
    SPEECHRECOGNITION_AVAILABLE = True
except ImportError:
    SPEECHRECOGNITION_AVAILABLE = False
    print("⚠️ SpeechRecognition не установлен")

class RecognitionEngine(Enum):
    WHISPER_TINY = "whisper-tiny"
    WHISPER_BASE = "whisper-base"
    WHISPER_SMALL = "whisper-small"
    WHISPER_MEDIUM = "whisper-medium"
    VOSK_SMALL = "vosk-small"
    VOSK_LARGE = "vosk-large"
    GOOGLE = "google"  # Онлайн
    
@dataclass
class RecognitionResult:
    text: str
    confidence: float
    words: List[Dict]
    engine: str
    processing_time: float

class MultiEngineSpeechRecognizer:
    """Многоязычный распознаватель речи с поддержкой разных движков"""
    
    def __init__(self, models_dir="models"):
        self.models_dir = models_dir
        self.engines = {}
        self.current_engine = None
        self.supported_engines = []
        
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Инициализация доступных движков"""
        # Whisper модели
        if WHISPER_AVAILABLE:
            self.supported_engines.extend([
                RecognitionEngine.WHISPER_TINY,
                RecognitionEngine.WHISPER_BASE,
                RecognitionEngine.WHISPER_SMALL,
                RecognitionEngine.WHISPER_MEDIUM
            ])
        
        # Vosk модели
        if VOSK_AVAILABLE:
            vosk_model_path = os.path.join(self.models_dir, "vosk")
            if os.path.exists(vosk_model_path):
                self.supported_engines.extend([
                    RecognitionEngine.VOSK_SMALL,
                    RecognitionEngine.VOSK_LARGE
                ])
        
        # Google онлайн
        if SPEECHRECOGNITION_AVAILABLE:
            self.supported_engines.append(RecognitionEngine.GOOGLE)
        
        print(f"✅ Доступные движки: {[e.value for e in self.supported_engines]}")
    
    def set_engine(self, engine: RecognitionEngine):
        """Установка текущего движка распознавания"""
        try:
            if engine == RecognitionEngine.GOOGLE:
                self.current_engine = engine
                print(f"✅ Выбран движок: {engine.value} (онлайн)")
            
            elif engine.value.startswith('whisper'):
                if not WHISPER_AVAILABLE:
                    raise Exception("Whisper не установлен")
                
                model_size = engine.value.split('-')[1]
                self.current_engine = engine
                self.engines[engine] = whisper.load_model(model_size)
                print(f"✅ Загружена модель Whisper: {model_size}")
            
            elif engine.value.startswith('vosk'):
                if not VOSK_AVAILABLE:
                    raise Exception("Vosk не установлен")
                
                model_size = engine.value.split('-')[1]
                model_path = os.path.join(self.models_dir, "vosk", f"model-{model_size}")
                
                if not os.path.exists(model_path):
                    print(f"⚠️ Модель Vosk {model_size} не найдена, скачивание...")
                    self._download_vosk_model(model_size, model_path)
                
                self.current_engine = engine
                self.engines[engine] = Model(model_path)
                print(f"✅ Загружена модель Vosk: {model_size}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки движка {engine.value}: {e}")
            return False
    
    def _download_vosk_model(self, model_size, target_path):
        """Скачивание модели Vosk"""
        import urllib.request
        import zipfile
        
        model_urls = {
            'small': 'https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip',
            'large': 'https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip'
        }
        
        if model_size not in model_urls:
            raise Exception(f"Неизвестный размер модели: {model_size}")
        
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        print(f"📥 Скачивание модели Vosk {model_size}...")
        zip_path = target_path + ".zip"
        
        urllib.request.urlretrieve(model_urls[model_size], zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(target_path))
        
        os.remove(zip_path)
        print(f"✅ Модель загружена в {target_path}")
    
    def transcribe(self, audio_path: str, language: str = "ru") -> RecognitionResult:
        """Транскрибация аудиофайла"""
        if not self.current_engine:
            raise Exception("Движок не выбран")
        
        import time
        start_time = time.time()
        
        try:
            if self.current_engine.value.startswith('whisper'):
                result = self._transcribe_whisper(audio_path, language)
            elif self.current_engine.value.startswith('vosk'):
                result = self._transcribe_vosk(audio_path)
            elif self.current_engine == RecognitionEngine.GOOGLE:
                result = self._transcribe_google(audio_path, language)
            else:
                raise Exception(f"Неизвестный движок: {self.current_engine}")
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка транскрибации: {e}")
            return RecognitionResult(
                text="",
                confidence=0.0,
                words=[],
                engine=self.current_engine.value,
                processing_time=0.0
            )
    
    def _transcribe_whisper(self, audio_path, language):
        """Транскрибация с помощью Whisper"""
        model = self.engines[self.current_engine]
        
        result = model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            fp16=False  # Для CPU
        )
        
        words = []
        if 'segments' in result:
            for segment in result['segments']:
                if 'words' in segment:
                    words.extend(segment['words'])
        
        return RecognitionResult(
            text=result['text'].strip(),
            confidence=float(result.get('confidence', 0.5)),
            words=words,
            engine=self.current_engine.value
        )
    
    def _transcribe_vosk(self, audio_path):
        """Транскрибация с помощью Vosk"""
        model = self.engines[self.current_engine]
        
        wf = wave.open(audio_path, "rb")
        recognizer = KaldiRecognizer(model, wf.getframerate())
        
        text_parts = []
        confidence_sum = 0.0
        word_count = 0
        all_words = []
        
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                if 'result' in result:
                    for word_info in result['result']:
                        all_words.append(word_info)
                        confidence_sum += word_info.get('conf', 0.5)
                        word_count += 1
        
        final_result = json.loads(recognizer.FinalResult())
        if 'text' in final_result:
            text_parts.append(final_result['text'])
        
        wf.close()
        
        confidence = confidence_sum / word_count if word_count > 0 else 0.5
        
        return RecognitionResult(
            text=" ".join(text_parts).strip(),
            confidence=confidence,
            words=all_words,
            engine=self.current_engine.value
        )
    
    def _transcribe_google(self, audio_path, language):
        """Транскрибация с помощью Google Speech Recognition"""
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        
        try:
            text = recognizer.recognize_google(audio, language=language)
            confidence = 0.8  # Google не возвращает confidence
        except sr.UnknownValueError:
            text = ""
            confidence = 0.0
        except sr.RequestError as e:
            text = f"Ошибка сервиса: {e}"
            confidence = 0.0
        
        return RecognitionResult(
            text=text,
            confidence=confidence,
            words=[],
            engine=self.current_engine.value
        )
    
    def calculate_wer(self, reference: str, hypothesis: str) -> float:
        """Расчет Word Error Rate"""
        if not reference or not hypothesis:
            return 1.0
        
        ref_words = reference.split()
        hyp_words = hypothesis.split()
        
        # Матрица для расчета расстояния Левенштейна
        d = np.zeros((len(ref_words) + 1, len(hyp_words) + 1))
        
        for i in range(len(ref_words) + 1):
            d[i][0] = i
        for j in range(len(hyp_words) + 1):
            d[0][j] = j
        
        # Расчет минимального расстояния
        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(hyp_words) + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    substitution = d[i-1][j-1] + 1
                    insertion = d[i][j-1] + 1
                    deletion = d[i-1][j] + 1
                    d[i][j] = min(substitution, insertion, deletion)
        
        wer = d[len(ref_words)][len(hyp_words)] / max(len(ref_words), 1)
        return wer
    
    def analyze_pair(self, outside_path: str, inside_path: str, reference_text: str = None):
        """Анализ пары аудио (снаружи/внутри)"""
        if not self.current_engine:
            raise Exception("Движок не выбран")
        
        outside_result = self.transcribe(outside_path)
        inside_result = self.transcribe(inside_path)
        
        analysis = {
            'outside': {
                'text': outside_result.text,
                'confidence': outside_result.confidence,
                'word_count': len(outside_result.text.split()),
                'processing_time': outside_result.processing_time
            },
            'inside': {
                'text': inside_result.text,
                'confidence': inside_result.confidence,
                'word_count': len(inside_result.text.split()),
                'processing_time': inside_result.processing_time
            },
            'comparison': {},
            'engine': self.current_engine.value
        }
        
        # Сравнение текстов
        if outside_result.text and inside_result.text:
            wer = self.calculate_wer(outside_result.text, inside_result.text)
            analysis['comparison']['wer'] = wer
            
            # Определение утечки
            if wer < 0.5 and len(inside_result.text.split()) > 3:
                analysis['comparison']['leakage_detected'] = True
                analysis['comparison']['leakage_score'] = 1 - wer
            else:
                analysis['comparison']['leakage_detected'] = False
                analysis['comparison']['leakage_score'] = 0.0
        
        # Сравнение с референсом если есть
        if reference_text:
            outside_wer_ref = self.calculate_wer(reference_text, outside_result.text)
            inside_wer_ref = self.calculate_wer(reference_text, inside_result.text)
            
            analysis['comparison']['wer_to_reference'] = {
                'outside': outside_wer_ref,
                'inside': inside_wer_ref
            }
        
        return analysis