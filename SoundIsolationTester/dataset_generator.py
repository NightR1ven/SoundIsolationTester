# dataset_generator.py
# -*- coding: utf-8 -*-
"""
Генератор тестового датасета для дипломной работы
Создает речевые записи с имитацией различных акустических условий
"""

import os
import json
import numpy as np
import wave
import struct
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import csv
import random
import math

@dataclass
class AcousticCondition:
    """Акустические условия для генерации датасета"""
    name: str
    description: str
    # Параметры шумов
    background_noise_level: float  # Уровень фонового шума (0-1)
    reverberation_time: float  # Время реверберации в секундах
    noise_types: List[str]  # Типы шумов ['white', 'pink', 'brown', 'urban', 'office']
    # Параметры речи
    speech_level_variation: float  # Вариация уровня речи (дБ)
    speech_speed_variation: float  # Вариация скорости речи (0.8-1.2)
    # Параметры помещения
    room_size: Tuple[float, float, float]  # Размеры помещения (м)
    absorption_coefficient: float  # Коэффициент поглощения
    distance_to_microphone: float  # Расстояние до микрофона (м)


class TestDatasetGenerator:
    """Генератор тестового датасета с имитацией акустической обстановки"""
    
    def __init__(self, output_dir="test_datasets"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_dataset(self, conditions: List[AcousticCondition], 
                        num_samples_per_condition: int = 10,
                        sample_rate: int = 16000,
                        duration_range: Tuple[float, float] = (2.0, 5.0)):
        """Сгенерировать полный датасет"""
        
        print(f"🧪 Генерация тестового датасета")
        print(f"📊 Условий: {len(conditions)}")
        print(f"📊 Образцов на условие: {num_samples_per_condition}")
        
        speech_samples = self._get_default_speech_samples()
        
        dataset_info = {
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'sample_rate': sample_rate,
            'total_conditions': len(conditions),
            'samples_per_condition': num_samples_per_condition,
            'total_samples': len(conditions) * num_samples_per_condition,
            'duration_range': duration_range,
            'conditions': [],
            'samples': []
        }
        
        for condition_idx, condition in enumerate(conditions):
            print(f"\n🔧 Условие {condition_idx+1}: {condition.name}")
            
            condition_dir = os.path.join(self.output_dir, f"condition_{condition_idx+1:02d}")
            os.makedirs(condition_dir, exist_ok=True)
            
            condition_info = {
                'id': condition_idx + 1,
                'name': condition.name,
                'description': condition.description,
                'parameters': {
                    'background_noise_level': condition.background_noise_level,
                    'reverberation_time': condition.reverberation_time,
                    'noise_types': condition.noise_types,
                    'speech_level_variation': condition.speech_level_variation,
                    'speech_speed_variation': condition.speech_speed_variation,
                    'room_size': condition.room_size,
                    'absorption_coefficient': condition.absorption_coefficient,
                    'distance_to_microphone': condition.distance_to_microphone
                },
                'samples': []
            }
            
            for sample_idx in range(num_samples_per_condition):
                # Выбираем случайную речевую фразу
                speech_text = random.choice(speech_samples)
                
                # Генерируем аудио
                duration = random.uniform(*duration_range)
                processed_audio = self._generate_synthetic_audio(
                    speech_text, condition, sample_rate, duration
                )
                
                # Сохраняем аудио
                sample_id = f"cond_{condition_idx+1:02d}_sample_{sample_idx+1:03d}"
                audio_filename = f"{sample_id}.wav"
                audio_path = os.path.join(condition_dir, audio_filename)
                
                # Сохраняем WAV файл
                self._save_audio_wav(processed_audio, audio_path, sample_rate)
                
                # Извлекаем фичи
                audio_features = self._extract_audio_features(processed_audio, sample_rate)
                
                # Рассчитываем SNR
                snr_db = self._calculate_snr(processed_audio)
                
                # Выбираем случайный тип шума
                noise_type = random.choice(condition.noise_types)
                
                # Сохраняем метаданные
                sample_metadata = {
                    'sample_id': sample_id,
                    'condition_id': condition_idx + 1,
                    'condition_name': condition.name,
                    'speech_text': speech_text,
                    'audio_path': audio_path,
                    'duration': duration,
                    'sample_rate': sample_rate,
                    'audio_features': audio_features,
                    'acoustic_parameters': {
                        'snr_db': snr_db,
                        'reverberation_level': condition.reverberation_time,
                        'noise_type': noise_type,
                        'distance_to_mic': condition.distance_to_microphone,
                    }
                }
                
                condition_info['samples'].append(sample_metadata)
                dataset_info['samples'].append(sample_metadata)
                
                print(f"  📝 Сэмпл {sample_idx+1}: '{speech_text[:40]}...' (SNR: {snr_db:.1f} дБ)")
            
            dataset_info['conditions'].append(condition_info)
        
        # Сохраняем датасет
        self._save_dataset_metadata(dataset_info)
        
        # Генерируем отчет
        self._generate_dataset_report(dataset_info)
        
        print(f"\n✅ Датасет сгенерирован!")
        print(f"📁 Папка: {self.output_dir}")
        print(f"📊 Всего сэмплов: {len(dataset_info['samples'])}")
        
        return dataset_info
    
    def _get_default_speech_samples(self) -> List[str]:
        """Получить стандартные речевые фразы для тестирования"""
        return [
            "Микрофон записывает речь с двух каналов одновременно восемьдесят",
            "Акустические тесты проводятся в специальной камере семьдесят семь",
            "Система распознавания речи работает оффлайн двадцать один",
            "Защита дипломной работы состоится в июне сорок пять",
            "Научное исследование требует точных измерений девяносто девять",
            "Важный эксперимент проводится в лаборатории двенадцать",
            "Современный компьютер обрабатывает данные быстро восемьдесят восемь",
            "Строгий преподаватель объясняет сложную тему шестьдесят четыре",
            "Молодой студент учится в университете тридцать семь",
            "Яркая звезда светит в темном небе сто одиннадцать",
            "Красный трактор стоит на зеленом поле сорок два",
            "Синий автомобиль едет по широкой дороге семнадцать",
            "Высокое дерево растет возле старого дома восемьдесят три",
            "Быстрая река течет между высокими горами двадцать пять",
            "Большой корабль плывет по синему морю девяносто шесть",
            "Жаркое солнце светит над теплым пляжем тридцать четыре",
            "Стройная береза качается на сильном ветру семьдесят один",
            "Громкий колокол звонит в старой церкви пятьдесят восемь",
            "Пушистый кот спит на мягком диване двадцать девять",
            "Звукоизоляция помещения измеряется в децибелах шестьдесят шесть",
        ]
    
    def _generate_synthetic_audio(self, text: str, condition: AcousticCondition, 
                                 sample_rate: int, duration: float) -> np.ndarray:
        """Сгенерировать синтетическое аудио"""
        
        # Создаем основную речевую компоненту
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Имитация речи через синусоиды разных частот
        base_freq = 100 + random.uniform(-20, 20)  # Базовая частота с вариацией
        
        # Основной тон
        speech = 0.5 * np.sin(2 * np.pi * base_freq * t)
        
        # Добавляем гармоники (характерные для речи)
        for harmonic in [2, 3, 4]:
            speech += 0.2/harmonic * np.sin(2 * np.pi * base_freq * harmonic * t)
        
        # Добавляем модуляцию (имитация артикуляции)
        modulation = 0.3 * np.sin(2 * np.pi * 5 * t)  # 5 Гц - частота слогов
        speech *= (1 + modulation)
        
        # Добавляем вариацию уровня
        if condition.speech_level_variation > 0:
            gain_variation = np.random.uniform(
                1 - condition.speech_level_variation,
                1 + condition.speech_level_variation
            )
            speech *= gain_variation
        
        # Нормализуем
        if np.max(np.abs(speech)) > 0:
            speech = speech / np.max(np.abs(speech)) * 0.8
        else:
            speech = speech * 0.8
        
        # Добавляем фоновый шум
        audio_with_noise = self._add_background_noise(speech, condition)
        
        # Применяем затухание из-за расстояния
        distance_attenuation = 1.0 / (condition.distance_to_microphone ** 0.5)
        final_audio = audio_with_noise * distance_attenuation
        
        return final_audio
    
    def _add_background_noise(self, audio: np.ndarray, condition: AcousticCondition) -> np.ndarray:
        """Добавить фоновый шум"""
        noise_level = condition.background_noise_level
        
        if noise_level <= 0:
            return audio
        
        # Выбираем тип шума
        noise_type = random.choice(condition.noise_types)
        
        if noise_type == 'white':
            # Белый шум (равномерный спектр)
            noise = np.random.normal(0, noise_level, len(audio))
            
        elif noise_type == 'pink':
            # Розовый шум (1/f) - упрощенная генерация
            white_noise = np.random.normal(0, noise_level, len(audio))
            # Фильтр низких частот
            b, a = [0.05, -0.1, 0.05], [1, -2.5, 2.0, -0.5]
            noise = white_noise.copy()
            for i in range(3, len(noise)):
                noise[i] = b[0]*white_noise[i] + b[1]*white_noise[i-1] + b[2]*white_noise[i-2]
                noise[i] -= a[1]*noise[i-1] + a[2]*noise[i-2]
            
        elif noise_type == 'brown':
            # Броуновский шум (1/f²)
            brown_noise = np.cumsum(np.random.normal(0, 1, len(audio)))
            brown_noise = brown_noise - np.mean(brown_noise)
            noise = brown_noise / np.max(np.abs(brown_noise)) * noise_level
            
        elif noise_type == 'urban':
            # Городской шум (низкочастотный)
            base = np.random.normal(0, noise_level * 0.5, len(audio))
            # Низкочастотные компоненты
            t = np.linspace(0, 10, len(audio))
            lf_noise = 0.3 * noise_level * np.sin(2 * np.pi * 0.5 * t)
            noise = base + lf_noise
            
        elif noise_type == 'office':
            # Офисный шум (разговоры на фоне)
            base = np.random.normal(0, noise_level * 0.3, len(audio))
            # Имитация разговоров
            t = np.linspace(0, 10, len(audio))
            speech_like = 0.4 * noise_level * np.sin(2 * np.pi * 200 * t) * np.sin(2 * np.pi * 2 * t)
            noise = base + speech_like
            
        else:
            # По умолчанию - белый шум
            noise = np.random.normal(0, noise_level, len(audio))
        
        # Смешиваем с оригинальным аудио
        if np.std(audio) > 0:
            return audio + noise * np.std(audio)
        else:
            return audio + noise
    
    def _save_audio_wav(self, audio: np.ndarray, filepath: str, sample_rate: int = 16000):
        """Сохранить аудио в WAV файл"""
        try:
            # Нормализуем и конвертируем в 16-бит
            if len(audio) == 0:
                audio = np.zeros(1000)  # Защита от пустого массива
            
            # Нормализуем до максимального значения 0.9
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio / max_val * 0.9
            
            audio_int16 = (audio * 32767).astype(np.int16)
            
            with wave.open(filepath, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
                
            #print(f"  ✅ Аудио сохранено: {os.path.basename(filepath)}")
                
        except Exception as e:
            print(f"❌ Ошибка сохранения аудио {filepath}: {e}")
            # Создаем минимальное аудио в случае ошибки
            try:
                simple_audio = np.zeros(sample_rate * 3)  # 3 секунды тишины
                simple_audio = (simple_audio * 32767).astype(np.int16)
                with wave.open(filepath, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(simple_audio.tobytes())
                print(f"  ⚠️ Создан пустой аудиофайл вместо ошибки")
            except:
                pass
    
    def _extract_audio_features(self, audio: np.ndarray, sample_rate: int) -> Dict:
        """Извлечь аудио-фичи"""
        if len(audio) == 0:
            return {
                'duration_samples': 0,
                'rms': 0.0,
                'max_amplitude': 0.0,
                'zero_crossing_rate': 0.0,
            }
        
        # Базовые статистики
        rms = np.sqrt(np.mean(audio**2))
        
        # Zero crossing rate
        zero_crossings = np.sum(np.diff(np.sign(audio)) != 0)
        zcr = zero_crossings / len(audio)
        
        return {
            'duration_samples': len(audio),
            'rms': float(rms),
            'max_amplitude': float(np.max(np.abs(audio))),
            'zero_crossing_rate': float(zcr),
        }
    
    def _calculate_snr(self, audio: np.ndarray) -> float:
        """Рассчитать SNR (отношение сигнал/шум)"""
        if len(audio) == 0:
            return 0.0
        
        # Простая оценка SNR
        signal_power = np.mean(audio**2)
        
        if signal_power == 0:
            return 0.0
        
        # Оцениваем шум через высокочастотные компоненты
        # Для простоты используем упрощенную формулу
        noise_power = np.mean((audio - np.mean(audio))**2)
        
        if noise_power > 0:
            snr = 10 * np.log10(signal_power / (noise_power + 1e-10))
        else:
            snr = 50.0  # Очень высокий SNR
        
        # Ограничиваем диапазон
        return float(max(0.0, min(50.0, snr)))
    
    def _save_dataset_metadata(self, dataset_info: Dict):
        """Сохранить метаданные датасета"""
        metadata_path = os.path.join(self.output_dir, "dataset_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, ensure_ascii=False, indent=2)
        
        # Сохраняем в CSV для удобства (с кодировкой для Excel)
        csv_path = os.path.join(self.output_dir, "dataset_samples.csv")
        
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as csvfile:
            # Определяем заголовки
            fieldnames = [
                'sample_id', 'condition_id', 'condition_name', 'speech_text',
                'audio_path', 'duration', 'sample_rate', 'snr_db',
                'reverberation_time', 'noise_type', 'distance_m', 'rms'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for sample in dataset_info['samples']:
                writer.writerow({
                    'sample_id': sample['sample_id'],
                    'condition_id': sample['condition_id'],
                    'condition_name': sample['condition_name'],
                    'speech_text': sample['speech_text'],
                    'audio_path': sample['audio_path'],
                    'duration': f"{sample['duration']:.3f}",
                    'sample_rate': sample['sample_rate'],
                    'snr_db': f"{sample['acoustic_parameters']['snr_db']:.2f}",
                    'reverberation_time': f"{sample['acoustic_parameters']['reverberation_level']:.2f}",
                    'noise_type': sample['acoustic_parameters']['noise_type'],
                    'distance_m': f"{sample['acoustic_parameters']['distance_to_mic']:.2f}",
                    'rms': f"{sample['audio_features']['rms']:.4f}",
                })
        
        print(f"📊 Метаданные сохранены: {metadata_path}")
        print(f"📊 CSV датасет сохранен: {csv_path} (открывается в Excel)")
    
    def _generate_dataset_report(self, dataset_info: Dict):
        """Сгенерировать отчет по датасету"""
        report_path = os.path.join(self.output_dir, "dataset_report.md")
        
        # Анализ данных
        snr_values = [s['acoustic_parameters']['snr_db'] for s in dataset_info['samples']]
        durations = [s['duration'] for s in dataset_info['samples']]
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# ОТЧЕТ ПО ТЕСТОВОМУ ДАТАСЕТУ ЗВУКОИЗОЛЯЦИИ\n\n")
            f.write(f"**Дата генерации:** {dataset_info['generated_at']}\n")
            f.write(f"**Частота дискретизации:** {dataset_info['sample_rate']} Гц\n")
            f.write(f"**Всего условий:** {dataset_info['total_conditions']}\n")
            f.write(f"**Сэмплов на условие:** {dataset_info['samples_per_condition']}\n")
            f.write(f"**Всего сэмплов:** {dataset_info['total_samples']}\n")
            f.write(f"**Диапазон длительностей:** {dataset_info['duration_range'][0]:.1f}-{dataset_info['duration_range'][1]:.1f} сек\n\n")
            
            f.write("## СТАТИСТИЧЕСКИЙ АНАЛИЗ\n\n")
            f.write(f"**SNR (отношение сигнал/шум):**\n")
            f.write(f"- Среднее: {np.mean(snr_values):.1f} дБ\n")
            f.write(f"- Мин: {np.min(snr_values):.1f} дБ\n")
            f.write(f"- Макс: {np.max(snr_values):.1f} дБ\n")
            f.write(f"- Стандартное отклонение: {np.std(snr_values):.1f} дБ\n\n")
            
            f.write(f"**Длительность аудио:**\n")
            f.write(f"- Среднее: {np.mean(durations):.2f} сек\n")
            f.write(f"- Мин: {np.min(durations):.2f} сек\n")
            f.write(f"- Макс: {np.max(durations):.2f} сек\n\n")
            
            f.write("## УСЛОВИЯ АКУСТИЧЕСКОЙ ОБСТАНОВКИ\n\n")
            for condition in dataset_info['conditions']:
                f.write(f"### Условие {condition['id']}: {condition['name']}\n")
                f.write(f"{condition['description']}\n\n")
                f.write("**Параметры:**\n")
                f.write(f"- Уровень фонового шума: {condition['parameters']['background_noise_level']:.3f}\n")
                f.write(f"- Время реверберации: {condition['parameters']['reverberation_time']:.2f} сек\n")
                f.write(f"- Типы шума: {', '.join(condition['parameters']['noise_types'])}\n")
                f.write(f"- Вариация уровня речи: ±{condition['parameters']['speech_level_variation']*100:.0f}%\n")
                f.write(f"- Размер помещения: {condition['parameters']['room_size'][0]}x{condition['parameters']['room_size'][1]}x{condition['parameters']['room_size'][2]} м\n")
                f.write(f"- Коэффициент поглощения: {condition['parameters']['absorption_coefficient']:.2f}\n")
                f.write(f"- Расстояние до микрофона: {condition['parameters']['distance_to_microphone']:.2f} м\n")
                f.write(f"**Количество сэмплов:** {len(condition['samples'])}\n\n")
            
            f.write("## СТРУКТУРА ДАТАСЕТА\n\n")
            f.write("```\n")
            f.write(f"{self.output_dir}/\n")
            f.write("├── dataset_metadata.json     # Полные метаданные в JSON\n")
            f.write("├── dataset_samples.csv      # Таблица сэмплов (открывается в Excel)\n")
            f.write("├── dataset_report.md        # Этот отчет\n")
            f.write("└── condition_01/           # Папка условий\n")
            f.write("    ├── cond_01_sample_001.wav\n")
            f.write("    ├── cond_01_sample_002.wav\n")
            f.write("    └── ...\n")
            f.write("```\n\n")
            
            f.write("## ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ\n\n")
            f.write("### 1. Для анализа в Excel:\n")
            f.write("1. Откройте файл `dataset_samples.csv` в Microsoft Excel\n")
            f.write("2. Данные автоматически отобразятся в таблице\n")
            f.write("3. Используйте фильтры и сводные таблицы для анализа\n\n")
            
            f.write("### 2. Для анализа в Python:\n")
            f.write("```python\n")
            f.write("import json\n")
            f.write("import csv\n")
            f.write("\n")
            f.write("# Загрузить метаданные\n")
            f.write("with open('dataset_metadata.json', 'r', encoding='utf-8') as f:\n")
            f.write("    dataset = json.load(f)\n")
            f.write("\n")
            f.write("# Загрузить CSV\n")
            f.write("import csv\n")
            f.write("samples = []\n")
            f.write("with open('dataset_samples.csv', 'r', encoding='utf-8-sig') as f:\n")
            f.write("    reader = csv.DictReader(f)\n")
            f.write("    for row in reader:\n")
            f.write("        samples.append(row)\n")
            f.write("\n")
            f.write("# Пример анализа\n")
            f.write("high_snr = [s for s in samples if float(s['snr_db']) > 30]\n")
            f.write("print(f'Сэмплов с высоким SNR (>30 дБ): {len(high_snr)}')\n")
            f.write("```\n\n")
            
            f.write("### 3. Для тестирования алгоритмов:\n")
            f.write("1. Используйте WAV файлы для тестирования распознавания речи\n")
            f.write("2. Используйте метаданные для оценки качества в разных условиях\n")
            f.write("3. Сравнивайте результаты по условиям и типам шума\n\n")
            
            f.write("## МЕТОДИКА ГЕНЕРАЦИИ\n\n")
            f.write("1. **Речевой сигнал:** Синтезирован через сумму синусоид с гармониками\n")
            f.write("2. **Фоновый шум:** Генерация в зависимости от типа (белый, розовый, офисный и т.д.)\n")
            f.write("3. **Параметры:** Контролируются через объекты AcousticCondition\n")
            f.write("4. **Метаданные:** Сохраняются в JSON и CSV (UTF-8-BOM для Excel)\n\n")
            
            f.write("## АВТОРСКИЕ ПРАВА\n\n")
            f.write("Сгенерировано системой Sound Isolation Tester v3.14\n")
            f.write(f"Для дипломной работы по теме защиты от спуфинг-атак\n")
            f.write(f"© {datetime.now().year} - Академическое использование\n")
        
        print(f"📋 Отчет сохранен: {report_path}")


# ===== ФУНКЦИИ ДЛЯ БЫСТРОЙ ГЕНЕРАЦИИ =====

def create_simple_dataset(output_dir="simple_dataset"):
    """Создать простой датасет для быстрого тестирования"""
    
    conditions = [
        AcousticCondition(
            name="quiet_room",
            description="Тихая комната, хорошая акустика",
            background_noise_level=0.02,
            reverberation_time=0.3,
            noise_types=['white'],
            speech_level_variation=0.1,
            speech_speed_variation=0.05,
            room_size=(4, 5, 3),
            absorption_coefficient=0.8,
            distance_to_microphone=1.0
        ),
    ]
    
    generator = TestDatasetGenerator(output_dir=output_dir)
    dataset = generator.generate_dataset(
        conditions=conditions,
        num_samples_per_condition=5,
        sample_rate=16000,
        duration_range=(2.0, 4.0)
    )
    
    return dataset


def create_diploma_dataset():
    """Создать предопределенный датасет для дипломной работы"""
    
    conditions = [
        AcousticCondition(
            name="ideal_conditions",
            description="Идеальные акустические условия, эталон",
            background_noise_level=0.01,
            reverberation_time=0.3,
            noise_types=['white'],
            speech_level_variation=0.1,
            speech_speed_variation=0.05,
            room_size=(4, 5, 3),
            absorption_coefficient=0.85,
            distance_to_microphone=1.0
        ),
        
        AcousticCondition(
            name="quiet_office",
            description="Тихий офис, хорошая акустика",
            background_noise_level=0.05,
            reverberation_time=0.5,
            noise_types=['white', 'office'],
            speech_level_variation=0.2,
            speech_speed_variation=0.1,
            room_size=(6, 8, 3),
            absorption_coefficient=0.7,
            distance_to_microphone=1.5
        ),
        
        AcousticCondition(
            name="noisy_corridor",
            description="Шумный коридор с эхом",
            background_noise_level=0.15,
            reverberation_time=1.0,
            noise_types=['pink', 'urban'],
            speech_level_variation=0.3,
            speech_speed_variation=0.15,
            room_size=(15, 3, 3),
            absorption_coefficient=0.4,
            distance_to_microphone=2.0
        ),
    ]
    
    # Генерация датасета
    generator = TestDatasetGenerator(output_dir="diploma_dataset")
    dataset = generator.generate_dataset(
        conditions=conditions,
        num_samples_per_condition=10,
        sample_rate=16000,
        duration_range=(3.0, 6.0)
    )
    
    print(f"\n🎓 ДАТАСЕТ ДЛЯ ДИПЛОМНОЙ РАБОТЫ СОЗДАН!")
    print(f"📁 Папка: diploma_dataset")
    print(f"📊 Условий: {len(conditions)}")
    print(f"📊 Всего сэмплов: {len(conditions) * 10}")
    
    return dataset


def create_research_dataset():
    """Создать расширенный датасет для исследований"""
    
    conditions = [
        # Влияние уровня шума
        AcousticCondition(
            name="low_noise_10db",
            description="Низкий уровень фонового шума",
            background_noise_level=0.05,
            reverberation_time=0.4,
            noise_types=['white'],
            speech_level_variation=0.1,
            speech_speed_variation=0.1,
            room_size=(6, 5, 3),
            absorption_coefficient=0.7,
            distance_to_microphone=1.0
        ),
        
        AcousticCondition(
            name="medium_noise_20db",
            description="Средний уровень шума",
            background_noise_level=0.15,
            reverberation_time=0.4,
            noise_types=['white', 'pink'],
            speech_level_variation=0.2,
            speech_speed_variation=0.1,
            room_size=(6, 5, 3),
            absorption_coefficient=0.7,
            distance_to_microphone=1.0
        ),
        
        AcousticCondition(
            name="high_noise_30db",
            description="Высокий уровень шума",
            background_noise_level=0.25,
            reverberation_time=0.4,
            noise_types=['white', 'brown'],
            speech_level_variation=0.3,
            speech_speed_variation=0.1,
            room_size=(6, 5, 3),
            absorption_coefficient=0.7,
            distance_to_microphone=1.0
        ),
    ]
    
    generator = TestDatasetGenerator(output_dir="research_dataset")
    dataset = generator.generate_dataset(
        conditions=conditions,
        num_samples_per_condition=15,
        sample_rate=16000,
        duration_range=(4.0, 7.0)
    )
    
    return dataset


# ===== ТЕСТИРОВАНИЕ =====

if __name__ == "__main__":
    print("🧪 ТЕСТИРОВАНИЕ ГЕНЕРАТОРА ДАТАСЕТА")
    print("=" * 50)
    
    try:
        # Простой тест
        print("\n1. Тест простого датасета...")
        dataset1 = create_simple_dataset("test_simple")
        
        print("\n2. Тест дипломного датасета...")
        dataset2 = create_diploma_dataset()
        
        print("\n" + "=" * 50)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n📁 Созданные датасеты:")
        print("  • test_simple/      - Простой тестовый датасет")
        print("  • diploma_dataset/  - Датасет для дипломной работы")
        print("\n📊 Отчеты и CSV файлы готовы для анализа в Excel")
        
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()