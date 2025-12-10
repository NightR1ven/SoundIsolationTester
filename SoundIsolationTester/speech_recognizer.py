# -*- coding: utf-8 -*-
import os
import json
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List
import warnings
import sys
import time

# Добавляем путь к локальным моделям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

warnings.filterwarnings('ignore')

class RecognitionEngine(Enum):
    """Доступные движки распознавания (все офлайн)"""
    # Whisper модели
    WHISPER_TINY = "whisper-tiny"
    WHISPER_BASE = "whisper-base" 
    WHISPER_SMALL = "whisper-small"
    WHISPER_MEDIUM = "whisper-medium"
    
    # Vosk модели
    VOSK_SMALL_RU = "vosk-small-ru"
    VOSK_LARGE_RU = "vosk-large-ru"

@dataclass
class RecognitionResult:
    text: str
    confidence: float
    words: List[Dict]
    engine: str
    processing_time: float = 0.0  # Сделали необязательным

class MultiEngineSpeechRecognizer:
    """Многоязычный распознаватель речи с локальными моделями"""
    
    def __init__(self, models_dir="models"):
        self.models_dir = models_dir
        
        # Проверяем доступность движков
        self.supported_engines = []
        self.engines = {}
        self.current_engine = None
        self.engine_status = {}
        
        # Создаем папки если нет
        self._create_model_dirs()
        
        # Инициализируем движки
        self._initialize_engines()
    
    def _create_model_dirs(self):
        """Создание папок для моделей"""
        dirs = ["whisper", "vosk"]
        for dir_name in dirs:
            path = os.path.join(self.models_dir, dir_name)
            os.makedirs(path, exist_ok=True)
    
    def _initialize_engines(self):
        """Инициализация доступных движков"""
        print("🔍 Поиск локальных моделей...")
        
        # Проверяем Whisper
        whisper_models = []
        for model in ["tiny", "base", "small", "medium"]:
            model_path = f"models/whisper/{model}.pt"
            if os.path.exists(model_path):
                whisper_models.append(model)
        
        if whisper_models:
            for model in whisper_models:
                engine_name = f"whisper-{model}"
                try:
                    engine = RecognitionEngine(engine_name)
                    self.supported_engines.append(engine)
                    print(f"✅ Whisper модель: {model}")
                    self.engine_status[engine_name] = "available"
                except ValueError:
                    self.engine_status[engine_name] = "not_available"
        
        # Проверяем Vosk
        vosk_models = []
        for model in ["small-ru", "large-ru"]:
            model_path = f"models/vosk/{model}"
            if os.path.exists(model_path):
                vosk_models.append(model)
        
        if vosk_models:
            for model in vosk_models:
                engine_name = f"vosk-{model}"
                try:
                    engine = RecognitionEngine(engine_name)
                    self.supported_engines.append(engine)
                    print(f"✅ Vosk модель: {model}")
                    self.engine_status[engine_name] = "available"
                except ValueError:
                    self.engine_status[engine_name] = "not_available"
        
        print(f"📊 Всего доступных движков: {len(self.supported_engines)}")
        
        if not self.supported_engines:
            print("⚠️ Нет доступных моделей! Запустите download_models.py")
    
    def get_available_engines(self):
        """Получить список доступных движков"""
        return [engine.value for engine in self.supported_engines]
    
    def set_engine(self, engine: RecognitionEngine):
        """Установка текущего движка распознавания"""
        try:
            print(f"⚙️ Загрузка движка: {engine.value}")
            
            if engine.value.startswith('whisper'):
                return self._load_whisper_engine(engine)
            
            elif engine.value.startswith('vosk'):
                return self._load_vosk_engine(engine)
            
            return False
            
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_whisper_engine(self, engine):
        """Загрузка Whisper модели"""
        model_size = engine.value.split('-')[1]
        model_path = f"models/whisper/{model_size}.pt"
        
        if not os.path.exists(model_path):
            print(f"❌ Модель Whisper {model_size} не найдена!")
            return False
        
        try:
            import whisper
            print(f"🔄 Загрузка Whisper {model_size}...")
            self.engines[engine] = whisper.load_model(model_path)
            self.current_engine = engine
            print(f"✅ Whisper {model_size} загружен")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки Whisper: {e}")
            return False
    
    def _load_vosk_engine(self, engine):
        """Загрузка Vosk модели - РАБОЧАЯ ВЕРСИЯ"""
        try:
            # Получаем название модели из enum
            engine_name = engine.value  # "vosk-small-ru" или "vosk-large-ru"
        
            # Извлекаем название модели
            # Разделяем по дефисам и берем все после первого
            parts = engine_name.split('-')
            if len(parts) >= 2:
                # "vosk-small-ru" -> ["vosk", "small", "ru"] -> "small-ru"
                model_name = '-'.join(parts[1:])
            else:
                model_name = engine_name
        
            # Путь к модели
            model_path = os.path.join("models", "vosk", model_name)
            abs_path = os.path.abspath(model_path)
        
            print(f"⚙️ Загрузка Vosk модели: {engine_name}")
            print(f"📁 Путь к модели: {abs_path}")
        
            # Проверяем существование
            if not os.path.exists(abs_path):
                print(f"❌ Папка модели не найдена: {abs_path}")
            
                # Показываем доступные папки
                vosk_dir = os.path.abspath("models/vosk")
                if os.path.exists(vosk_dir):
                    print(f"📁 Доступные папки в {vosk_dir}:")
                    for item in os.listdir(vosk_dir):
                        item_path = os.path.join(vosk_dir, item)
                        if os.path.isdir(item_path):
                            print(f"  • {item}/")
                        else:
                            print(f"  • {item}")
                return False
        
            # Проверяем структуру
            required = ["am", "conf", "graph"]
            for folder in required:
                folder_path = os.path.join(abs_path, folder)
                if not os.path.exists(folder_path):
                    print(f"❌ Отсутствует обязательная папка: {folder}")
                    return False
        
            # Загружаем модель
            from vosk import Model
            print(f"🔄 Загрузка модели из {abs_path}...")
            model = Model(abs_path)
        
            self.engines[engine] = model
            self.current_engine = engine
            print(f"✅ Модель {engine_name} успешно загружена")
            return True
        
        except Exception as e:
            print(f"❌ Ошибка загрузки Vosk модели: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def transcribe(self, audio_path: str, language: str = "ru") -> RecognitionResult:
        """Транскрибация аудиофайла"""
        if not self.current_engine:
            raise Exception("Движок не выбран")
        
        if not os.path.exists(audio_path):
            print(f"❌ Файл не найден: {audio_path}")
            return RecognitionResult(
                text="",
                confidence=0.0,
                words=[],
                engine=self.current_engine.value if self.current_engine else "unknown",
                processing_time=0.0
            )
        
        start_time = time.time()
        
        try:
            if self.current_engine.value.startswith('whisper'):
                result = self._transcribe_whisper(audio_path, language)
            elif self.current_engine.value.startswith('vosk'):
                result = self._transcribe_vosk(audio_path)
            else:
                raise Exception(f"Неизвестный движок: {self.current_engine}")
            
            processing_time = time.time() - start_time
            
            # Возвращаем результат с временем обработки
            return RecognitionResult(
                text=result.text,
                confidence=result.confidence,
                words=result.words,
                engine=result.engine,
                processing_time=processing_time
            )
            
        except Exception as e:
            print(f"❌ Ошибка транскрибации: {e}")
            import traceback
            traceback.print_exc()
            return RecognitionResult(
                text="",
                confidence=0.0,
                words=[],
                engine=self.current_engine.value if self.current_engine else "unknown",
                processing_time=0.0
            )
    
    def _transcribe_whisper(self, audio_path, language):
        """Транскрибация с помощью Whisper"""
        model = self.engines[self.current_engine]
        
        try:
            result = model.transcribe(
                audio_path,
                language=language,
                task="transcribe",
                fp16=False
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
                engine=self.current_engine.value,
                processing_time=0.0
            )
        except Exception as e:
            print(f"❌ Ошибка Whisper транскрибации: {e}")
            return RecognitionResult(
                text="",
                confidence=0.0,
                words=[],
                engine=self.current_engine.value,
                processing_time=0.0
            )
    
    def _transcribe_vosk(self, audio_path):
        """Транскрибация с помощью Vosk"""
        try:
            import wave
            import json
            from vosk import KaldiRecognizer
            
            model = self.engines[self.current_engine]
            
            wf = wave.open(audio_path, "rb")
            
            # Проверяем параметры аудио
            if wf.getnchannels() != 1:
                print("⚠️ Vosk требует моно-аудио")
                wf.close()
                return RecognitionResult(
                    text="",
                    confidence=0.0,
                    words=[],
                    engine=self.current_engine.value,
                    processing_time=0.0
                )
            
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
                engine=self.current_engine.value,
                processing_time=0.0
            )
        except Exception as e:
            print(f"❌ Ошибка Vosk транскрибации: {e}")
            return RecognitionResult(
                text="",
                confidence=0.0,
                words=[],
                engine=self.current_engine.value,
                processing_time=0.0
            )
    
    def calculate_wer(self, reference: str, hypothesis: str) -> float:
        """Расчет Word Error Rate"""
        if not reference or not hypothesis:
            return 1.0
        
        ref_words = reference.split()
        hyp_words = hypothesis.split()
        
        if not ref_words:
            return 1.0 if hyp_words else 0.0
        
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
        return min(wer, 1.0)  # Ограничиваем максимум 1.0
    
    def analyze_pair(self, outside_path: str, inside_path: str, reference_text: str = None):
        """Анализ пары аудио (снаружи/внутри)"""
        if not self.current_engine:
            raise Exception("Движок не выбран")
        
        # Проверяем существование файлов
        if not os.path.exists(outside_path):
            print(f"❌ Файл не найден: {outside_path}")
            return None
        if not os.path.exists(inside_path):
            print(f"❌ Файл не найден: {inside_path}")
            return None
        
        # Транскрибация с замером времени
        start_time = time.time()
        outside_result = self.transcribe(outside_path)
        inside_result = self.transcribe(inside_path)
        total_time = time.time() - start_time
        
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
            'comparison': {
                'total_processing_time': total_time
            },
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
    
    def get_engine_status(self):
        """Получить статус всех движков"""
        return self.engine_status
    
    def test_all_engines(self):
        """Протестировать все доступные движки"""
        results = {}
        
        for engine in self.supported_engines:
            print(f"\n🧪 Тестирование движка: {engine.value}")
            
            if self.set_engine(engine):
                try:
                    # Создаем тестовый аудио файл (1 секунда тишины)
                    import wave
                    import numpy as np
                    
                    test_file = "test_audio.wav"
                    sample_rate = 16000
                    duration = 1.0
                    
                    # Создаем тихий сигнал
                    t = np.linspace(0, duration, int(sample_rate * duration))
                    signal = 0.01 * np.sin(2 * np.pi * 440 * t)  # Тихий тон 440 Гц
                    signal = (signal * 32767).astype(np.int16)
                    
                    with wave.open(test_file, 'wb') as wav_file:
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2)
                        wav_file.setframerate(sample_rate)
                        wav_file.writeframes(signal.tobytes())
                    
                    # Пробуем транскрибировать
                    result = self.transcribe(test_file)
                    
                    results[engine.value] = {
                        'status': 'success',
                        'text': result.text[:50] + "..." if len(result.text) > 50 else result.text,
                        'confidence': result.confidence,
                        'processing_time': result.processing_time
                    }
                    
                    print(f"✅ {engine.value}: Успешно")
                    
                    # Удаляем тестовый файл
                    try:
                        os.remove(test_file)
                    except:
                        pass
                        
                except Exception as e:
                    results[engine.value] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    print(f"❌ {engine.value}: Ошибка - {e}")
            else:
                results[engine.value] = {
                    'status': 'failed_to_load',
                    'error': 'Не удалось загрузить движок'
                }
                print(f"❌ {engine.value}: Не удалось загрузить")
        
        return results


# Тестирование модуля
if __name__ == "__main__":
    print("🧪 Тестирование speech_recognizer.py")
    print("="*50)
    
    recognizer = MultiEngineSpeechRecognizer()
    
    print(f"\n📋 Доступные движки: {recognizer.get_available_engines()}")
    
    if recognizer.supported_engines:
        # Тестируем первый доступный движок
        test_engine = recognizer.supported_engines[0]
        print(f"\n🔧 Тестируем движок: {test_engine.value}")
        
        if recognizer.set_engine(test_engine):
            print("✅ Движок загружен успешно")
            
            # Тестируем все движки
            test_results = recognizer.test_all_engines()
            print("\n📊 Результаты тестирования:")
            for engine, result in test_results.items():
                print(f"  {engine}: {result['status']}")
        else:
            print("❌ Не удалось загрузить движок")
    else:
        print("❌ Нет доступных движков. Запустите download_models.py")