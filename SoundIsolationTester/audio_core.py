# -*- coding: utf-8 -*-
import pyaudio
import numpy as np
import threading
import time
from datetime import datetime
import sys
import os
import wave
import json

class AudioCore:
    def __init__(self):
        self._initialize_audio()
        self.is_recording = False
        self.streams = {}
        self.audio_data = {'outside': [], 'inside': []}
        self.sample_rate = 44100
        self.chunk_size = 1024
        self.lock = threading.Lock()
        self.recordings_folder = "recordings"
        self.current_test_name = "unknown_test"
        self.record_duration = 0
        self.reference_text = None  # НОВОЕ: сохраняем фразу для проверки
        self._create_recordings_folder()
        
    def _create_recordings_folder(self):
        """Создать папку для записей если не существует"""
        if not os.path.exists(self.recordings_folder):
            os.makedirs(self.recordings_folder)
            print(f"✅ Создана папка для записей: {self.recordings_folder}")
    
    def _initialize_audio(self):
        """Инициализация аудио с обработкой ошибок"""
        try:
            self.p = pyaudio.PyAudio()
            print("✅ PyAudio инициализирован успешно")
        except Exception as e:
            print(f"❌ Ошибка инициализации PyAudio: {e}")
            raise
    
    def _fix_mojibake(self, text):
        """Исправление кодировщика (mojibake) - когда UTF-8 был прочитан как cp1251"""
        try:
            if not isinstance(text, str):
                return text
                
            if 'Р' in text and 'С' in text and 'Р' in text:
                try:
                    fixed = text.encode('cp1251').decode('utf-8')
                    print(f"✅ Исправлены кодировощик '{text}' -> '{fixed}'")
                    return fixed
                except (UnicodeEncodeError, UnicodeDecodeError):
                    pass
                    
            return text
        except Exception as e:
            print(f"⚠️ Ошибка исправления кодировщика: {e}")
            return text
    
    def _decode_device_name(self, name):
        """Корректное декодирование названий устройств для Windows"""
        try:
            if isinstance(name, bytes):
                try:
                    decoded = name.decode('utf-8')
                    print(f"✅ Успешно декодировано как UTF-8: {decoded}")
                    return decoded
                except UnicodeDecodeError:
                    print("⚠️ Не UTF-8, пробуем другие кодировки")
                    pass
                    
                for encoding in ['cp1251', 'cp866', 'iso-8859-5']:
                    try:
                        decoded = name.decode(encoding)
                        print(f"✅ Успешно декодировано как {encoding}: {decoded}")
                        return decoded
                    except UnicodeDecodeError:
                        continue
                
                return name.decode('utf-8', errors='replace')
            else:
                return self._fix_mojibake(str(name))
        except Exception as e:
            print(f"❌ Критическая ошибка декодирования: {e}")
            return f"Audio_Device_{hash(str(name)) % 10000}"
    
    def get_audio_devices(self):
        """Получить список доступных аудиоустройств с коррекцией кодировки"""
        devices = []
        try:
            for i in range(self.p.get_device_count()):
                info = self.p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    device_name = self._decode_device_name(info['name'])
                    
                    devices.append({
                        'index': i,
                        'name': device_name,
                        'channels': info['maxInputChannels'],
                        'sample_rate': info['defaultSampleRate'],
                        'host_api': info['hostApi']
                    })
            print(f"✅ Найдено устройств: {len(devices)}")
            
            for device in devices:
                print(f"   Устройство {device['index']}: '{device['name']}'")
                
        except Exception as e:
            print(f"❌ Ошибка получения устройств: {e}")
        
        return devices
    
    def _audio_callback(self, in_data, frame_count, time_info, status, channel):
        """Callback функция для записи аудио"""
        if self.is_recording:
            try:
                audio_array = np.frombuffer(in_data, dtype=np.int16)
                with self.lock:
                    self.audio_data[channel].extend(audio_array)
            except Exception as e:
                print(f"❌ Ошибка в callback {channel}: {e}")
        return (in_data, pyaudio.paContinue)
    
    def start_recording(self, outside_device_idx, inside_device_idx, duration=10, test_name="", reference_text=None):
        """Начать запись с двух микрофонов"""
        print(f"🎙️ Запуск записи: outside={outside_device_idx}, inside={inside_device_idx}, duration={duration}сек")
        
        # Сохраняем фразу для проверки
        self.reference_text = reference_text
        
        # Останавливаем предыдущую запись если есть
        if self.is_recording:
            self.stop_recording()
        
        with self.lock:
            self.audio_data = {'outside': [], 'inside': []}
        
        self.current_test_name = test_name or datetime.now().strftime("test_%Y%m%d_%H%M%S")
        self.record_duration = duration  # Сохраняем длительность
        self.is_recording = True
        self.record_start_time = time.time()
        
        success = True
        
        def start_outside():
            try:
                stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=outside_device_idx,
                    frames_per_buffer=self.chunk_size,
                    stream_callback=lambda *args: self._audio_callback(*args, 'outside')
                )
                self.streams['outside'] = stream
                stream.start_stream()
                print("✅ Внешний микрофон запущен")
            except Exception as e:
                print(f"❌ Ошибка внешнего микрофона: {e}")
                nonlocal success
                success = False
        
        def start_inside():
            try:
                stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=inside_device_idx,
                    frames_per_buffer=self.chunk_size,
                    stream_callback=lambda *args: self._audio_callback(*args, 'inside')
                )
                self.streams['inside'] = stream
                stream.start_stream()
                print("✅ Внутренний микрофон запущен")
            except Exception as e:
                print(f"❌ Ошибка внутреннего микрофона: {e}")
                nonlocal success
                success = False
        
        thread_outside = threading.Thread(target=start_outside)
        thread_inside = threading.Thread(target=start_inside)
        
        thread_outside.start()
        thread_inside.start()
        
        thread_outside.join()
        thread_inside.join()
        
        if success and duration > 0:
            # Запускаем таймер остановки с небольшим запасом времени
            print(f"⏰ Запуск таймера на {duration} секунд")
            self.stop_timer = threading.Timer(duration + 0.5, self._stop_by_timer)
            self.stop_timer.daemon = True  # Важно: делаем поток демоном
            self.stop_timer.start()
        
        return success
    
    def _stop_by_timer(self):
        """Остановка записи по таймеру"""
        print(f"⏰ Таймер сработал, останавливаем запись после {self.record_duration} сек")
        if self.is_recording:
            self.stop_recording()
    
    def stop_recording(self):
        """Остановить запись и сохранить файлы"""
        print("⏹️ Остановка записи...")
        self.is_recording = False
        
        # Отменяем таймер если он есть
        if hasattr(self, 'stop_timer'):
            self.stop_timer.cancel()
        
        for name, stream in self.streams.items():
            try:
                if stream.is_active():
                    stream.stop_stream()
                stream.close()
                print(f"✅ Поток {name} остановлен")
            except Exception as e:
                print(f"⚠️ Ошибка остановки потока {name}: {e}")
        
        self.streams.clear()
        
        saved_files = {}
        if len(self.audio_data['outside']) > 0 or len(self.audio_data['inside']) > 0:
            saved_files = self._save_recordings()
        else:
            print("⚠️ Нет данных для сохранения")
        
        with self.lock:
            outside_len = len(self.audio_data['outside'])
            inside_len = len(self.audio_data['inside'])
            duration = outside_len / self.sample_rate if outside_len > 0 else 0
            
            print(f"📊 Статистика записи:")
            print(f"   Снаружи: {outside_len} сэмплов ({duration:.2f} сек)")
            print(f"   Внутри: {inside_len} сэмплов")
            if saved_files:
                print(f"   Файлы: {saved_files}")
        
        return saved_files
    
    def _save_recordings(self):
        """Сохранить записи в WAV файлы"""
        saved_files = {}
        
        with self.lock:
            for channel in ['outside', 'inside']:
                if len(self.audio_data[channel]) > 0:
                    filename = f"{self.current_test_name}_{channel}.wav"
                    filepath = os.path.join(self.recordings_folder, filename)
                    
                    try:
                        audio_array = np.array(self.audio_data[channel], dtype=np.int16)
                        
                        with wave.open(filepath, 'wb') as wav_file:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(2)
                            wav_file.setframerate(self.sample_rate)
                            wav_file.writeframes(audio_array.tobytes())
                        
                        saved_files[channel] = {
                            'filename': filename,
                            'filepath': filepath,
                            'samples': len(audio_array),
                            'duration': len(audio_array) / self.sample_rate
                        }
                        print(f"✅ Сохранен {channel}: {filename}")
                        
                    except Exception as e:
                        print(f"❌ Ошибка сохранения {channel}: {e}")
                        saved_files[channel] = None
                else:
                    print(f"⚠️ Нет данных для канала {channel}")
                    saved_files[channel] = None
        
        if saved_files.get('outside') or saved_files.get('inside'):
            self._save_test_metadata(saved_files)
        
        return saved_files
    
    def _save_test_metadata(self, saved_files):
        """Сохранить метаданные теста для последующего анализа ИИ"""
        metadata = {
            'test_name': self.current_test_name,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'sample_rate': self.sample_rate,
            'duration': saved_files.get('outside', {}).get('duration', 0),
            'files': saved_files,
            'analysis_ready': True,
            'reference_text': self.reference_text,  # НОВОЕ: сохраняем фразу для проверки
            'app_version': '3.14'
        }
        
        metadata_file = os.path.join(self.recordings_folder, f"{self.current_test_name}_metadata.json")
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            print(f"✅ Метаданные сохранены: {metadata_file}")
            if self.reference_text:
                print(f"📝 Фраза для проверки сохранена в метаданных")
        except Exception as e:
            print(f"❌ Ошибка сохранения метаданных: {e}")
    
    def get_audio_levels(self):
        """Получить текущие уровни громкости"""
        levels = {'outside': 0.0, 'inside': 0.0}
        
        with self.lock:
            for channel in ['outside', 'inside']:
                if len(self.audio_data[channel]) > 0:
                    recent_samples = self.audio_data[channel][-self.chunk_size:]
                    if len(recent_samples) > 0:
                        audio_array = np.array(recent_samples, dtype=np.float32)
                        rms = np.sqrt(np.mean(np.square(audio_array)))
                        levels[channel] = min(rms / 32768.0, 1.0)
        
        return levels
    
    def get_recording_stats(self):
        """Получить статистику записи"""
        with self.lock:
            return {
                'outside_samples': len(self.audio_data['outside']),
                'inside_samples': len(self.audio_data['inside']),
                'duration': len(self.audio_data['outside']) / self.sample_rate if self.audio_data['outside'] else 0,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'test_name': getattr(self, 'current_test_name', 'unknown'),
                'reference_text': getattr(self, 'reference_text', None)
            }
    
    def get_recent_recordings(self):
        """Получить список последних записей"""
        try:
            recordings = []
            for file in os.listdir(self.recordings_folder):
                if file.endswith('_metadata.json'):
                    metadata_path = os.path.join(self.recordings_folder, file)
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            recordings.append(metadata)
                    except Exception as e:
                        print(f"⚠️ Ошибка чтения {file}: {e}")
            
            recordings.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return recordings
        except Exception as e:
            print(f"❌ Ошибка получения списка записей: {e}")
            return []
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.stop_recording()
        if hasattr(self, 'p'):
            self.p.terminate()
            print("✅ PyAudio ресурсы освобождены")
    
    def __del__(self):
        """Деструктор"""
        self.cleanup()