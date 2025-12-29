# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import threading
import time
import sys
import os
import json
import webbrowser
from datetime import datetime, timedelta
import csv
import subprocess
import random
import math
import difflib
import re

# Функция для динамического импорта модулей
def import_audio_core():
    """Динамический импорт AudioCore"""
    try:
        from audio_core import AudioCore
        return AudioCore
    except ImportError as e:
        print(f"⚠️ Ошибка импорта AudioCore: {e}")
        # Создаем заглушку
        class AudioCoreStub:
            def __init__(self):
                self.is_recording = False
                print("⚠️ Используется заглушка AudioCore")
            
            def get_audio_devices(self):
                return []
            
            def start_recording(self, *args, **kwargs):
                print("⚠️ Заглушка: запись невозможна")
                return False
            
            def stop_recording(self):
                return {}
            
            def get_recording_stats(self):
                return {}
            
            def get_audio_levels(self):
                return {'outside': 0.0, 'inside': 0.0}
            
            def cleanup(self):
                pass
        
        return AudioCoreStub

def import_ai_analyzer():
    """Динамический импорт анализатора"""
    try:
        from ai_analyzer import EnhancedSoundIsolationAnalyzer
        return EnhancedSoundIsolationAnalyzer
    except ImportError as e:
        print(f"⚠️ Ошибка импорта анализатора: {e}")
        # Создаем заглушку
        class AnalyzerStub:
            def __init__(self):
                self.initialized = False
                
            def analyze_with_audio_analysis(self, *args, **kwargs):
                return {'results': {'overall_assessment': {'verdict': 'УСТАНОВИТЕ ЗАВИСИМОСТИ'}}}
            
            def set_recognition_engine(self, engine_name):
                return False
        
        return AnalyzerStub

def import_speech_recognizer():
    """Динамический импорт распознавателя речи"""
    try:
        # Проверяем, есть ли файл
        if not os.path.exists("speech_recognizer.py"):
            print("⚠️ Файл speech_recognizer.py не найден")
            raise ImportError("Файл не найден")
        
        # Добавляем текущую директорию в путь
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from speech_recognizer import MultiEngineSpeechRecognizer, RecognitionEngine
        return MultiEngineSpeechRecognizer, RecognitionEngine, True
    except ImportError as e:
        print(f"⚠️ Ошибка импорта распознавателя: {e}")
        # Создаем заглушку
        from enum import Enum
        
        class RecognitionEngineStub(Enum):
            WHISPER_TINY = "whisper-tiny"
            WHISPER_BASE = "whisper-base"
            WHISPER_SMALL = "whisper-small"
            WHISPER_MEDIUM = "whisper-medium"
            VOSK_SMALL_RU = "vosk-small-ru"
            VOSK_LARGE_RU = "vosk-large-ru"
        
        class RecognizerStub:
            def __init__(self, models_dir="models"):
                self.supported_engines = [
                    RecognitionEngineStub.WHISPER_TINY,
                    RecognitionEngineStub.WHISPER_SMALL,
                    RecognitionEngineStub.VOSK_SMALL_RU,
                ]
                self.current_engine = None
            
            def set_engine(self, engine):
                print(f"⚠️ Заглушка: установка движка {engine}")
                self.current_engine = engine
                return False
            
            def transcribe(self, *args, **kwargs):
                print("⚠️ Заглушка: распознавание недоступно")
                return None
            
            def analyze_pair(self, *args, **kwargs):
                return {
                    'outside': {'text': 'Распознавание недоступно. Установите модели.'}, 
                    'inside': {'text': 'Распознавание недоступно. Установите модели.'},
                    'comparison': {'wer': 1.0},
                    'engine': 'stub'
                }
            
            def calculate_wer(self, *args, **kwargs):
                return 1.0
        
        return RecognizerStub, RecognitionEngineStub, False

# Импортируем модули
AudioCore = import_audio_core()
EnhancedSoundIsolationAnalyzer = import_ai_analyzer()
MultiEngineSpeechRecognizer, RecognitionEngine, SPEECH_RECOGNITION_AVAILABLE = import_speech_recognizer()

# Пытаемся импортировать dataset_generator, если нет - выводим предупреждение
try:
    from dataset_generator import TestDatasetGenerator, AcousticCondition, create_diploma_dataset
    DATASET_GENERATOR_AVAILABLE = True
except ImportError:
    DATASET_GENERATOR_AVAILABLE = False
    print("⚠️ Модуль dataset_generator не найден")

# Пытаемся импортировать polars, если нет - используем альтернативы
try:
    import polars as pl
    POLARS_AVAILABLE = True
    print("✅ Polars загружен")
except ImportError:
    POLARS_AVAILABLE = False
    print("⚠️ Polars не установлен, используем CSV")

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.append(os.path.dirname(__file__))

class RecordingIndicator(tk.Canvas):
    """Анимированный индикатор записи с барами"""
    
    def __init__(self, parent, width=500, height=120, label="", **kwargs):
        super().__init__(parent, width=width, height=height, **kwargs)
        self.width = width
        self.height = height
        self.label = label
        self.level = 0.0
        self.is_active = False
        self.bars = []
        self.animation_id = None
        
        # Темный фон
        self.create_rectangle(0, 0, width, height, fill="#1a1a2e", outline="")
        
        # Заголовок
        self.title = self.create_text(
            width//2, 20, 
            text=label, 
            font=('Arial', 12, 'bold'),
            fill="white"
        )
        
        # Область для баров
        self.bar_area = self.create_rectangle(
            20, 40, width-20, height-15,
            fill="#16213e", outline="#0f3460", width=2
        )
        
        # Создаем бары (вертикальные полоски)
        bar_width = 10
        bar_spacing = 3
        num_bars = (width - 40) // (bar_width + bar_spacing)
        start_x = 25
        
        for i in range(num_bars):
            x1 = start_x + i * (bar_width + bar_spacing)
            x2 = x1 + bar_width
            bar = self.create_rectangle(
                x1, height-20, x2, height-20,  # Начинаем с минимальной высоты
                fill="#00b894", outline="#00b894"
            )
            self.bars.append(bar)
        
        # Индикатор записи (красный кружок)
        self.record_indicator = self.create_oval(
            width-35, 15, width-20, 30,
            fill="#e74c3c", outline=""
        )
        
        # Текст REC
        self.record_text = self.create_text(
            width-27, 22,
            text="●",
            font=('Arial', 10, 'bold'),
            fill="white"
        )
        
        # Текущий уровень
        self.level_text = self.create_text(
            width//2, height-5,
            text="Уровень: 0%",
            font=('Arial', 9),
            fill="#95a5a6"
        )
    
    def set_active(self, active):
        """Активировать/деактивировать индикатор"""
        self.is_active = active
        if active:
            self.itemconfig(self.record_indicator, fill="#e74c3c")
            self.itemconfig(self.record_text, text="●")
            self._start_animation()
        else:
            self.itemconfig(self.record_indicator, fill="#7f8c8d")
            self.itemconfig(self.record_text, text="○")
            self._stop_animation()
    
    def update_level(self, level):
        """Обновить уровень звука (0.0 - 1.0)"""
        self.level = max(0.0, min(1.0, level))
        
        # Обновляем текст уровня
        self.itemconfig(self.level_text, text=f"Уровень: {int(self.level*100)}%")
    
    def _start_animation(self):
        """Запустить анимацию баров"""
        if self.animation_id:
            self.after_cancel(self.animation_id)
        
        if self.is_active:
            self._animate_bars()
    
    def _stop_animation(self):
        """Остановить анимацию"""
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None
        
        # Сбрасываем все бары
        for bar in self.bars:
            self.coords(bar, self.coords(bar)[0], self.height-20, 
                       self.coords(bar)[2], self.height-20)
            self.itemconfig(bar, fill="#00b894")
    
    def _animate_bars(self):
        """Анимировать бары в зависимости от уровня звука"""
        if not self.is_active:
            return
        
        num_bars = len(self.bars)
        active_bars = int(self.level * num_bars)
        
        # Максимальная высота бара
        max_bar_height = self.height - 60
        
        for i, bar in enumerate(self.bars):
            # Текущие координаты бара
            x1, y1, x2, y2 = self.coords(bar)
            
            if i < active_bars:
                # Этот бар должен быть активным
                target_height = max_bar_height * (i / num_bars) + random.uniform(10, 30)
                target_top = self.height - 20 - target_height
                
                # Добавляем немного случайности для естественного вида
                target_top += random.uniform(-5, 5)
                target_top = max(self.height - 20 - max_bar_height, min(self.height - 25, target_top))
                
                # Плавная анимация к целевой позиции
                current_top = y1
                if abs(current_top - target_top) > 2:
                    new_top = current_top + (target_top - current_top) * 0.3
                else:
                    new_top = target_top
                
                # Обновляем координаты
                self.coords(bar, x1, new_top, x2, self.height-20)
                
                # Цвет в зависимости от высоты
                bar_height = (self.height - 20 - new_top) / max_bar_height
                if bar_height < 0.3:
                    color = "#00b894"  # Зеленый
                elif bar_height < 0.7:
                    color = "#fdcb6e"  # Желтый
                else:
                    color = "#e17055"  # Оранжевый/Красный
                
                self.itemconfig(bar, fill=color, outline=color)
            else:
                # Неактивный бар - опускаем вниз
                current_top = y1
                target_top = self.height - 20
                if current_top < target_top - 1:
                    new_top = current_top + (target_top - current_top) * 0.5
                    self.coords(bar, x1, new_top, x2, self.height-20)
                else:
                    self.coords(bar, x1, self.height-20, x2, self.height-20)
                    self.itemconfig(bar, fill="#00b894", outline="#00b894")
        
        # Продолжаем анимацию
        self.animation_id = self.after(50, self._animate_bars)
    
    def reset(self):
        """Сбросить индикатор"""
        self.level = 0.0
        self.set_active(False)
        self.itemconfig(self.level_text, text="Уровень: 0%")

class AdvancedSoundTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Sound Isolation Tester")
        self.root.geometry("1200x950")  # Увеличили высоту
        
        self.center_window()
        
        # Инициализация
        try:
            # Создаем папки
            self._create_directories()
            
            # Создаем экземпляры классов
            self.audio_core = AudioCore()
            self.analyzer = EnhancedSoundIsolationAnalyzer()
            
            # Инициализация распознавателя
            self.recognizer = None
            if SPEECH_RECOGNITION_AVAILABLE:
                try:
                    self.recognizer = MultiEngineSpeechRecognizer(models_dir="models")
                    self.current_engine = None
                    print("✅ Распознаватель речи инициализирован")
                except Exception as e:
                    print(f"⚠️ Ошибка инициализации распознавателя: {e}")
                    self.recognizer = None
            else:
                print("⚠️ Распознавание речи отключено")
            
            self.recordings_folder = "recordings"
            
            # Создаем папку для записей если не существует
            if not os.path.exists(self.recordings_folder):
                os.makedirs(self.recordings_folder)
            
            self.setup_styles()
            self.setup_ui()
            self.refresh_devices()
            self.refresh_recordings_list()
            
            # Загружаем последнюю конфигурацию
            self.load_config()
            
            # Флаг для мониторинга
            self.monitoring_active = False
            
            # Флаг истечения времени записи
            self.recording_timer_active = False

            # Переменные для генерации датасета
            self.scenario_vars = []
            self.condition_frames = []
            self.dataset_vars = {}
            
            print("✅ Приложение успешно инициализировано")
            
        except Exception as e:
            print(f"❌ Критическая ошибка инициализации: {e}")
            import traceback
            traceback.print_exc()
            
            error_msg = f"Ошибка инициализации:\n\n{str(e)}\n\n"
            error_msg += "Проверьте:\n"
            error_msg += "1. Все файлы находятся в одной папке\n"
            error_msg += "2. Установлены все зависимости (pip install -r requirements.txt)\n"
            error_msg += "3. Для Windows: установлен Microsoft Visual C++ Redistributable"
            
            messagebox.showerror("Ошибка инициализации", error_msg)
    
    def _create_directories(self):
        """Создание необходимых папок"""
        folders = ["models", "models/whisper", "models/vosk", "recordings", "experiments"]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
    
    def center_window(self):
        """Центрирование окна"""
        self.root.update_idletasks()
        width = 1200
        height = 950
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_styles(self):
        """Настройка стилей"""
        style = ttk.Style()
        style.configure("Red.TButton", foreground="red", font=('Arial', 10, 'bold'))
        style.configure("Green.TButton", foreground="green", font=('Arial', 10, 'bold'))
        style.configure("Title.TLabel", font=('Arial', 14, 'bold'))
    
    def setup_ui(self):
        """Настройка интерфейса"""
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title = ttk.Label(main_frame, 
            text="🧪 ТЕСТЕР ЗВУКОИЗОЛЯЦИИ",
            font=('Arial', 14, 'bold'))
        title.pack(pady=10)
        
        # Вкладки
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Вкладка 1: Запись
        record_frame = ttk.Frame(notebook, padding="10")
        notebook.add(record_frame, text="🎙️ ЗАПИСЬ")
        self.setup_record_tab(record_frame)
        
        # Вкладка 2: Анализ
        analysis_frame = ttk.Frame(notebook, padding="10")
        notebook.add(analysis_frame, text="📊 АНАЛИЗ")
        self.setup_analysis_tab(analysis_frame)
        
        # Вкладка 3: Настройки движков
        engine_frame = ttk.Frame(notebook, padding="10")
        notebook.add(engine_frame, text="⚙️ ДВИЖКИ")
        self.setup_engine_tab(engine_frame)
        
        # Вкладка 4: Генерация дата сета
        export_frame = ttk.Frame(notebook, padding="10")
        notebook.add(export_frame, text="📁 ДАТАСЕТ")
        self.setup_export_tab(export_frame)
        
        # Статус
        self.status_var = tk.StringVar(value="✅ Готов к работе")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, padding=5)
        status_bar.pack(fill=tk.X, pady=5)
    
    def setup_record_tab(self, parent):
        """Вкладка записи"""
        # Блок 1: Устройства
        device_frame = ttk.LabelFrame(parent, text="Аудиоустройства", padding="10")
        device_frame.pack(fill=tk.X, pady=10)
        
        # Внешний микрофон
        ttk.Label(device_frame, text="Снаружи:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.outside_combo = ttk.Combobox(device_frame, width=60, state="readonly")
        self.outside_combo.grid(row=0, column=1, padx=10, pady=5)
        
        # Внутренний микрофон
        ttk.Label(device_frame, text="Внутри:", font=('Arial', 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.inside_combo = ttk.Combobox(device_frame, width=60, state="readonly")
        self.inside_combo.grid(row=1, column=1, padx=10, pady=5)
        
        # Кнопки управления устройствами
        btn_frame = ttk.Frame(device_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="🔄 Обновить", command=self.refresh_devices).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🎧 Тест", command=self.test_devices).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 Сводка", command=self.show_device_summary).pack(side=tk.LEFT, padx=5)
        
        device_frame.columnconfigure(1, weight=1)
        
        # Блок 2: Индикаторы записи (появляются при записи)
        self.indicator_frame = ttk.LabelFrame(parent, text="Индикаторы записи", padding="10")
        self.indicator_frame.pack(fill=tk.X, pady=10)
        
        # Скрываем индикаторы по умолчанию
        self.indicator_frame.pack_forget()
        
        # Контейнер для индикаторов
        indicator_container = ttk.Frame(self.indicator_frame)
        indicator_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Индикатор внешнего микрофона
        self.outside_indicator = RecordingIndicator(
            indicator_container, 
            width=550, 
            height=130, 
            label="🎤 ВНЕШНИЙ МИКРОФОН (СНАРУЖИ)"
        )
        self.outside_indicator.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        
        # Индикатор внутреннего микрофона
        self.inside_indicator = RecordingIndicator(
            indicator_container, 
            width=550, 
            height=130, 
            label="🎤 ВНУТРЕННИЙ МИКРОФОН (ВНУТРИ)"
        )
        self.inside_indicator.pack(side=tk.LEFT, padx=10, fill=tk.BOTH, expand=True)
        
        # Блок 3: Параметры теста
        params_frame = ttk.LabelFrame(parent, text="Параметры теста", padding="10")
        params_frame.pack(fill=tk.X, pady=10)
        
        # Название теста
        ttk.Label(params_frame, text="Название:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.test_name_var = tk.StringVar(value=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        ttk.Entry(params_frame, textvariable=self.test_name_var, width=40).grid(row=0, column=1, padx=10, pady=5)
        
        # Длительность
        ttk.Label(params_frame, text="Длительность (сек):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.duration_var = tk.StringVar(value="15")
        ttk.Spinbox(params_frame, from_=5, to=300, textvariable=self.duration_var, width=15).grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # ФРАЗА ДЛЯ ПРОВЕРКИ (НОВОЕ)
        ttk.Label(params_frame, text="Фраза для проверки:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.reference_text_var = tk.StringVar(value="Красный трактор стоит на зеленом поле сорок два")
        self.reference_entry = ttk.Entry(params_frame, textvariable=self.reference_text_var, width=60, font=('Arial', 10))
        self.reference_entry.grid(row=2, column=1, padx=10, pady=5)
        
        # Кнопка для генерации случайной фразы
        ttk.Button(params_frame, text="🎲 Случайная фраза", 
                  command=self.generate_random_phrase, width=20).grid(row=2, column=2, padx=5, pady=5)
        
        # Опции
        self.enable_analysis_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params_frame, text="Автоматический анализ", variable=self.enable_analysis_var).grid(row=3, column=0, columnspan=2, pady=5, sticky=tk.W)
        
        # Включение проверки текста
        self.enable_text_check_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params_frame, text="Проверять соответствие текста (защита от спуфинга)", 
                       variable=self.enable_text_check_var).grid(row=4, column=0, columnspan=2, pady=5, sticky=tk.W)
        
        params_frame.columnconfigure(1, weight=1)
        
        # Блок 4: Управление записью
        control_frame = ttk.LabelFrame(parent, text="Управление записью", padding="10")
        control_frame.pack(fill=tk.X, pady=10)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(expand=True)
        
        self.record_btn = ttk.Button(btn_frame, text="🔴 НАЧАТЬ ЗАПИСЬ", 
                                    command=self.start_recording,
                                    style="Red.TButton",
                                    width=20)
        self.record_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹️ ОСТАНОВИТЬ", 
                                  command=self.stop_recording,
                                  state=tk.DISABLED,
                                  width=20)
        self.stop_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Индикаторы состояния
        indicator_frame = ttk.Frame(parent)
        indicator_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(indicator_frame, text="Статус:").pack(side=tk.LEFT)
        self.record_status = ttk.Label(indicator_frame, text="Ожидание", foreground="blue")
        self.record_status.pack(side=tk.LEFT, padx=10)
        
        # Таймер
        self.timer_label = ttk.Label(indicator_frame, text="00:00 / 00:00", font=('Arial', 12, 'bold'))
        self.timer_label.pack(side=tk.RIGHT)
        
        # Подсказка
        hint_frame = ttk.LabelFrame(parent, text="📝 Инструкция для тестирования", padding="10")
        hint_frame.pack(fill=tk.X, pady=10)
        
        hint_text = "Для защиты от спуфинг-атак:\n1. Установите микрофоны снаружи и внутри помещения\n2. Введите фразу для проверки (или используйте случайную)\n3. Нажмите 'НАЧАТЬ ЗАПИСЬ'\n4. СНАРУЖИ громко произнесите фразу\n5. Система проверит соответствие текста и обнаружит спуфинг-атаки"
        ttk.Label(hint_frame, text=hint_text, justify=tk.LEFT, wraplength=1100).pack(anchor=tk.W)
    
    def generate_random_phrase(self):
        """Сгенерировать случайную фразу для проверки"""
        phrases = [
            "Красный трактор стоит на зеленом поле сорок два",
            "Синий автомобиль едет по широкой дороге семнадцать",
            "Высокое дерево растет возле старого дома восемьдесят три",
            "Быстрая река течет между высокими горами двадцать пять",
            "Большой корабль плывет по синему морю девяносто шесть",
            "Жаркое солнце светит над теплым пляжем тридцать четыре",
            "Стройная береза качается на сильном ветру семьдесят один",
            "Громкий колокол звонит в старой церкви пятьдесят восемь",
            "Пушистый кот спит на мягком диване двадцать девять",
            "Яркая звезда светит в темном небе сто одиннадцать"
        ]
        
        import random
        phrase = random.choice(phrases)
        self.reference_text_var.set(phrase)
        print(f"🎲 Сгенерирована новая фраза: {phrase}")
    
    def refresh_devices(self):
        """Обновить список аудиоустройств"""
        try:
            self.status_var.set("🔄 Поиск аудиоустройств...")
            self.root.update()
            
            devices = self.audio_core.get_audio_devices()
            
            # Очищаем комбобоксы
            self.outside_combo.set('')
            self.inside_combo.set('')
            
            # Заполняем устройствами
            device_names = [f"{i}: {d['name']} ({d['channels']} каналов)" for i, d in enumerate(devices)]
            
            self.outside_combo['values'] = device_names
            self.inside_combo['values'] = device_names
            
            if device_names:
                if len(device_names) >= 1:
                    self.outside_combo.current(0)
                if len(device_names) >= 2:
                    self.inside_combo.current(1)
                
                self.status_var.set(f"✅ Найдено устройств: {len(devices)}")
                return True
            else:
                self.status_var.set("⚠️ Устройства не найдены")
                return False
                
        except Exception as e:
            error_msg = f"❌ Ошибка обновления устройств: {e}"
            self.status_var.set(error_msg)
            messagebox.showerror("Ошибка", error_msg)
            return False
    
    def test_devices(self):
        """Тест выбранных устройств"""
        try:
            outside_idx = self.outside_combo.current()
            inside_idx = self.inside_combo.current()
            
            if outside_idx < 0 or inside_idx < 0:
                messagebox.showwarning("Предупреждение", "Выберите оба устройства")
                return
            
            # Показываем индикаторы для теста
            self.show_indicators()
            self.outside_indicator.set_active(True)
            self.inside_indicator.set_active(True)
            
            # Тестовая анимация
            self._start_test_animation()
            
            # Создаем тестовый поток для проверки устройств
            test_thread = threading.Thread(target=self._perform_device_test, 
                                          args=(outside_idx, inside_idx))
            test_thread.daemon = True
            test_thread.start()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка тестирования: {e}")
            self.hide_indicators()
    
    def _perform_device_test(self, outside_idx, inside_idx):
        """Выполнить тест устройств"""
        try:
            self.status_var.set("🔊 Тестирование устройств...")
            
            # Простая проверка - запись на 2 секунды
            success = self.audio_core.start_recording(
                outside_idx, inside_idx, duration=2, 
                test_name=f"device_test_{datetime.now().strftime('%H%M%S')}"
            )
            
            if success:
                time.sleep(2.5)  # Ждем завершения
                stats = self.audio_core.get_recording_stats()
                
                # Выключаем индикаторы
                self.root.after(0, self.hide_indicators)
                self.root.after(0, lambda: self.outside_indicator.set_active(False))
                self.root.after(0, lambda: self.inside_indicator.set_active(False))
                
                self.status_var.set(f"✅ Тест завершен. Записано: {stats.get('duration', 0):.1f} сек")
                messagebox.showinfo("Тест устройств", 
                                  f"Тест завершен успешно!\n"
                                  f"Снаружи: {stats.get('outside_samples', 0)} сэмплов\n"
                                  f"Внутри: {stats.get('inside_samples', 0)} сэмплов")
            else:
                self.root.after(0, self.hide_indicators)
                self.status_var.set("❌ Ошибка тестирования")
                messagebox.showerror("Ошибка", "Не удалось начать запись")
                
        except Exception as e:
            self.root.after(0, self.hide_indicators)
            self.status_var.set("❌ Ошибка тестирования")
            messagebox.showerror("Ошибка", f"Ошибка теста: {e}")
    
    def _start_test_animation(self):
        """Запустить тестовую анимацию индикаторов"""
        test_start = time.time()
        
        def animate():
            elapsed = time.time() - test_start
            if elapsed < 3:  # 3 секунды анимации
                # Синусоидальная анимация
                level = (math.sin(elapsed * 5) + 1) / 2
                self.outside_indicator.update_level(level * 0.8)
                self.inside_indicator.update_level(level * 0.6)
                self.root.after(50, animate)
            else:
                # Сбрасываем анимацию
                self.outside_indicator.update_level(0)
                self.inside_indicator.update_level(0)
        
        animate()
    
    def show_indicators(self):
        """Показать индикаторы записи"""
        self.indicator_frame.pack(fill=tk.X, pady=10)
        self.root.update()
    
    def hide_indicators(self):
        """Скрыть индикаторы записи"""
        self.indicator_frame.pack_forget()
        self.root.update()
    
    def start_recording(self):
        """Начать запись"""
        try:
            outside_idx = self.outside_combo.current()
            inside_idx = self.inside_combo.current()
        
            if outside_idx < 0 or inside_idx < 0:
                messagebox.showwarning("Предупреждение", "Выберите оба устройства")
                return
        
            test_name = self.test_name_var.get()
            duration = int(self.duration_var.get())
            reference_text = self.reference_text_var.get() if self.enable_text_check_var.get() else None
        
            # ДОБАВЬТЕ ОТЛАДОЧНУЮ ПЕЧАТЬ
            print(f"\n🎤 ==== НАЧАЛО ЗАПИСИ ====")
            print(f"📝 Фраза из UI: '{reference_text}'")
            print(f"✅ Проверка текста включена: {self.enable_text_check_var.get()}")
            print(f"=================================\n")
        
            # Проверка наличия текста для проверки
            if self.enable_text_check_var.get() and not reference_text.strip():
                messagebox.showwarning("Предупреждение", 
                    "Введите фразу для проверки или отключите проверку текста.\n"
                    "Это необходимо для защиты от спуфинг-атак.")
                return
        
            # Обновляем интерфейс
            self.record_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.record_status.config(text="🔴 ИДЕТ ЗАПИСЬ", foreground="red")
            self.status_var.set("🎙️ Запись начата... Произнесите фразу снаружи!")
        
            # Показываем фразу для произнесения
            if reference_text:
                messagebox.showinfo("Произнесите фразу", 
                    f"ВНУТРИ помещения произнесите громко и четко:\n\n"
                    f"📢 '{reference_text}'\n\n"
                    f"Система проверит соответствие текста ВНУТРИ помещения\n"
                    f"для защиты от спуфинг-атак (использования записанной речи).")
        
            # Показываем и активируем индикаторы
            self.show_indicators()
            self.outside_indicator.set_active(True)
            self.inside_indicator.set_active(True)
        
            # Запускаем мониторинг уровней
            self.monitoring_active = True
            self._start_level_monitoring()
        
            # Запускаем запись в отдельном потоке - ИСПРАВЛЕНО!
            self.recording_thread = threading.Thread(
                target=self._perform_recording,
                args=(outside_idx, inside_idx, duration, test_name, reference_text)  # ← ДОБАВИЛИ reference_text!
            )
            self.recording_thread.daemon = True
            self.recording_thread.start()
        
            # Запускаем таймер с указанием общей длительности
            self.start_time = time.time()
            self.recording_duration = duration  # Сохраняем длительность
            self._update_timer()
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка начала записи: {e}")
            self._stop_recording_ui()
    
    def _start_level_monitoring(self):
        """Запустить мониторинг уровней звука"""
        if self.monitoring_active:
            try:
                # Получаем реальные уровни звука
                levels = self.audio_core.get_audio_levels()
                
                # Обновляем индикаторы
                self.outside_indicator.update_level(levels['outside'])
                self.inside_indicator.update_level(levels['inside'])
                
                # Добавляем немного случайности для естественности
                if random.random() < 0.3:  # 30% chance
                    outside_noise = levels['outside'] + random.uniform(-0.05, 0.1)
                    inside_noise = levels['inside'] + random.uniform(-0.03, 0.07)
                    self.outside_indicator.update_level(max(0, min(1, outside_noise)))
                    self.inside_indicator.update_level(max(0, min(1, inside_noise)))
                
            except Exception as e:
                # Если ошибка, используем демо-анимацию
                demo_level = (math.sin(time.time() * 3) + 1) / 2
                self.outside_indicator.update_level(demo_level * 0.8)
                self.inside_indicator.update_level(demo_level * 0.5)
            
            # Продолжаем мониторинг
            self.root.after(100, self._start_level_monitoring)
    
    def _perform_recording(self, outside_idx, inside_idx, duration, test_name, reference_text=None):
        """Выполнить запись с сохранением фразы для проверки спуфинга"""
        try:
            # Сохраняем длительность для проверки
            self.recording_duration = duration
        
            # ДОБАВЬТЕ ЭТУ ОТЛАДОЧНУЮ ПЕЧАТЬ
            print(f"\n🔊 ==== ВЫПОЛНЕНИЕ ЗАПИСИ ====")
            print(f"📝 Передаваемая фраза в audio_core: '{reference_text}'")
            print(f"===================================\n")
        
            success = self.audio_core.start_recording(
                outside_idx, inside_idx, duration, test_name, reference_text
            )
        
            if not success:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось начать запись"))
                self.root.after(0, self._stop_recording_ui)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка записи: {e}"))
            self.root.after(0, self._stop_recording_ui)
    
    def _update_timer(self):
        """Обновление таймера с автоматической остановкой"""
        if hasattr(self, 'start_time') and hasattr(self, 'recording_duration'):
            elapsed = int(time.time() - self.start_time)
            remaining = max(0, self.recording_duration - elapsed)
            
            # Форматируем время
            elapsed_min = elapsed // 60
            elapsed_sec = elapsed % 60
            total_min = self.recording_duration // 60
            total_sec = self.recording_duration % 60
            
            self.timer_label.config(text=f"{elapsed_min:02d}:{elapsed_sec:02d} / {total_min:02d}:{total_sec:02d}")
            
            # Проверяем, не истекло ли время записи
            if elapsed >= self.recording_duration:
                # Автоматически останавливаем запись
                print("⏰ Время записи истекло, останавливаем...")
                self.stop_recording()
                return
            
            # Продолжаем обновление каждую секунду
            self.root.after(1000, self._update_timer)
    
    def stop_recording(self):
        """Остановить запись"""
        try:
            # Останавливаем мониторинг
            self.monitoring_active = False
            
            # Останавливаем запись
            saved_files = self.audio_core.stop_recording()
            
            # Обновляем интерфейс
            self._stop_recording_ui()
            
            # Обновляем список записей
            self.refresh_recordings_list()
            
            # Автоматический анализ если включен
            if self.enable_analysis_var.get() and saved_files:
                outside_path = saved_files.get('outside', {}).get('filepath')
                inside_path = saved_files.get('inside', {}).get('filepath')
                reference_text = self.reference_text_var.get() if self.enable_text_check_var.get() else None
                
                if outside_path and inside_path:
                    test_name = self.test_name_var.get()
                    self._analyze_recording(outside_path, inside_path, test_name, reference_text)
            
            self.status_var.set("✅ Запись завершена")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка остановки записи: {e}")
            self._stop_recording_ui()
    
    def _stop_recording_ui(self):
        """Обновить интерфейс после остановки записи"""
        self.record_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.record_status.config(text="Ожидание", foreground="blue")
        self.timer_label.config(text="00:00 / 00:00")
        
        # Выключаем и скрываем индикаторы
        self.outside_indicator.set_active(False)
        self.inside_indicator.set_active(False)
        self.hide_indicators()
    
    def show_device_summary(self):
        """Показать сводку по устройствам"""
        try:
            devices = self.audio_core.get_audio_devices()
            
            if not devices:
                messagebox.showinfo("Устройства", "Устройства не найдены")
                return
            
            summary = "📊 Сводка по аудиоустройствам:\n\n"
            for i, device in enumerate(devices):
                summary += f"Устройство {i}:\n"
                summary += f"  Название: {device['name']}\n"
                summary += f"  Каналы: {device['channels']}\n"
                summary += f"  Частота: {device.get('sample_rate', 'N/A')} Гц\n"
                summary += "  ---\n"
            
            summary += f"\nВсего устройств: {len(devices)}"
            
            # Создаем отдельное окно для отображения
            summary_window = tk.Toplevel(self.root)
            summary_window.title("Сводка устройств")
            summary_window.geometry("600x400")
            
            text_widget = scrolledtext.ScrolledText(summary_window, wrap=tk.WORD, width=70, height=20)
            text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            text_widget.insert(tk.END, summary)
            text_widget.config(state=tk.DISABLED)
            
            ttk.Button(summary_window, text="Закрыть", command=summary_window.destroy).pack(pady=5)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка получения сводки: {e}")
    
    def setup_analysis_tab(self, parent):
        """Вкладка анализа"""
        # Заголовок
        ttk.Label(parent, text="АНАЛИЗ ЗАПИСЕЙ (с защитой от спуфинга)", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Список записей
        list_frame = ttk.LabelFrame(parent, text="Доступные записи", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # TreeView
        columns = ("name", "date", "duration", "size", "status", "engine", "text_check")
        self.recordings_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        # Заголовки
        self.recordings_tree.heading("name", text="Имя теста")
        self.recordings_tree.heading("date", text="Дата")
        self.recordings_tree.heading("duration", text="Длительность")
        self.recordings_tree.heading("size", text="Размер")
        self.recordings_tree.heading("status", text="Статус")
        self.recordings_tree.heading("engine", text="Движок")
        self.recordings_tree.heading("text_check", text="Проверка текста")
        
        # Ширина колонок
        self.recordings_tree.column("name", width=180)
        self.recordings_tree.column("date", width=140)
        self.recordings_tree.column("duration", width=80)
        self.recordings_tree.column("size", width=70)
        self.recordings_tree.column("status", width=80)
        self.recordings_tree.column("engine", width=100)
        self.recordings_tree.column("text_check", width=120)
        
        # Прокрутка
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.recordings_tree.yview)
        self.recordings_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recordings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Двойной клик для анализа
        self.recordings_tree.bind('<Double-1>', lambda e: self.analyze_selected())
        
        # Действия
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=10)
        
        actions = [
            ("🎤 Распознать речь", self.recognize_speech),
            ("📋 Отчет", self.generate_report),
            ("🎵 Воспроизвести", self.play_recording),
            ("🗑️ Удалить запись", self.delete_recording)
        ]
        
        for text, command in actions:
            ttk.Button(action_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)
        
        # Область результатов
        result_frame = ttk.LabelFrame(parent, text="Результаты анализа", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=10, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self.result_text.config(state=tk.DISABLED)
    
    def setup_engine_tab(self, parent):
        """Вкладка настройки движков распознавания"""
        # Выбор движка
        engine_frame = ttk.LabelFrame(parent, text="Движок распознавания речи (ОФФЛАЙН)", padding="10")
        engine_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(engine_frame, text="Выберите модель:", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Список доступных движков
        self.engine_combo = ttk.Combobox(engine_frame, width=40, state="readonly")
        
        # Загружаем список движков
        engines = self._get_available_engines()
        self.engine_combo['values'] = engines
        
        if engines:
            self.engine_combo.current(0)
        
        self.engine_combo.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Кнопки
        btn_frame = ttk.Frame(engine_frame)
        btn_frame.grid(row=0, column=2, padx=10)
        
        ttk.Button(btn_frame, text="Выбрать", command=self.select_engine).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🔄 Проверить", command=self.check_available_models).pack(side=tk.LEFT, padx=2)
        
        # Статус движка
        self.engine_status_var = tk.StringVar(value="Движок не выбран")
        ttk.Label(engine_frame, textvariable=self.engine_status_var, foreground="blue").grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Кнопка загрузки моделей
        ttk.Button(engine_frame, text="📥 Загрузить модели", 
                  command=self.download_models).grid(row=2, column=0, columnspan=3, pady=10)
        
        # Описание движков
        desc_frame = ttk.LabelFrame(parent, text="Доступные офлайн модели", padding="10")
        desc_frame.pack(fill=tk.X, pady=10)
        
        descriptions = """

1. 🎯 Whisper Small (оптимальная) - 500 МБ
   • Международная модель OpenAI
   • Хорошее качество для русского языка
   • Баланс скорости и точности

2. 🇷🇺 Vosk Small RU (русская) - 40 МБ
   • Специализирована для русского языка
   • Очень быстрая
   • Маленький размер

Все модели работают полностью ОФФЛАЙН без API ключей!"""
        
        desc_label = ttk.Label(desc_frame, text=descriptions, justify=tk.LEFT)
        desc_label.pack(anchor=tk.W)
        
        # Тест распознавания
        test_frame = ttk.LabelFrame(parent, text="Тест распознавания", padding="10")
        test_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(test_frame, text="Тестовый аудиофайл:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.test_audio_path = tk.StringVar()
        ttk.Entry(test_frame, textvariable=self.test_audio_path, width=40).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(test_frame, text="Обзор...", command=self.browse_test_audio).grid(row=0, column=2, padx=5)
        
        ttk.Button(test_frame, text="🧪 Тест распознавания", command=self.test_recognition).grid(row=1, column=0, columnspan=3, pady=10)
        
        # Результаты теста
        self.test_result_text = scrolledtext.ScrolledText(test_frame, height=6, width=60, wrap=tk.WORD)
        self.test_result_text.grid(row=2, column=0, columnspan=3, pady=5, sticky="nsew")
        test_frame.columnconfigure(1, weight=1)
    
    def _get_available_engines(self):
        """Получение списка доступных движков"""
        engines = []
    
        # Проверяем наличие моделей
        # Whisper
        whisper_models = []
        for model in ["tiny", "base", "small", "medium"]:
            if os.path.exists(f"models/whisper/{model}.pt"):
                whisper_models.append(f"whisper-{model}")
    
        # Vosk
        vosk_models = []
        for model in ["small-ru", "large-ru"]:
            if os.path.exists(f"models/vosk/{model}"):
                vosk_models.append(f"vosk-{model}")
    
        # Добавляем все доступные
        engines.extend(whisper_models)
        engines.extend(vosk_models)
    
        # Если нет моделей, показываем инструкцию
        if not engines:
            engines = ["⚠️ Нет моделей. Загрузите модели!"]
    
        return engines
    
    def check_available_models(self):
        """Проверка доступных моделей"""
        available = []
        missing = []
        
        # Проверяем Whisper
        for model in ["tiny", "small", "medium"]:
            path = f"models/whisper/{model}.pt"
            if os.path.exists(path):
                available.append(f"whisper-{model}")
            else:
                missing.append(f"whisper-{model}")
        
        # Проверяем Vosk
        for model in ["small-ru"]:
            path = f"models/vosk/{model}"
            if os.path.exists(path):
                available.append(f"vosk-{model}")
            else:
                missing.append(f"vosk-{model}")
        
        # Показываем результат
        result = "✅ Доступные модели:\n"
        for model in available:
            result += f"  • {model}\n"
        
        if missing:
            result += "\n❌ Отсутствующие модели:\n"
            for model in missing:
                result += f"  • {model}\n"
        
        result += f"\n📊 Всего: {len(available)} из 2 моделей\n"
        
        if len(available) >= 2:
            result += "🎉 Все модели готовы!"
        else:
            result += "⚠️ Загрузите недостающие модели через 'Загрузить модели'"
        
        messagebox.showinfo("Проверка моделей", result)
        
        # Обновляем список в комбобоксе
        engines = self._get_available_engines()
        self.engine_combo['values'] = engines
        if engines and "⚠️" not in engines[0]:
            self.engine_combo.current(0)
    
    def setup_export_tab(self, parent):
        """Вкладка генерации тестового датасета"""
    
        if not DATASET_GENERATOR_AVAILABLE:
            ttk.Label(parent, text="❌ Модуль генерации датасета не найден", 
                    font=('Arial', 12, 'bold')).pack(pady=50)
            ttk.Label(parent, text="Создайте файл dataset_generator.py с кодом из предыдущего сообщения",
                    wraplength=800).pack(pady=20)
            return
    
        # Заголовок
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=10)
    
        ttk.Label(title_frame, 
            text="ГЕНЕРАЦИЯ ТЕСТОВОГО ДАТАСЕТА", 
            font=('Arial', 14, 'bold')).pack()
    
        ttk.Label(title_frame, 
            text="Создание речевых записей с имитацией акустической обстановки защищаемого помещения",
            font=('Arial', 10)).pack(pady=5)
    
        # Вкладки
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
    
        # Вкладка 1: Быстрая генерация
        quick_frame = ttk.Frame(notebook, padding="15")
        notebook.add(quick_frame, text="🚀 БЫСТРАЯ ГЕНЕРАЦИЯ")
        self.setup_quick_generation_tab(quick_frame)
    
        # Вкладка 2: Тестовый датасет
        diploma_frame = ttk.Frame(notebook, padding="15")
        notebook.add(diploma_frame, text="ТЕСТОВЫЙ ДАТАСЕТ")
        self.setup_diploma_dataset_tab(diploma_frame)
    
    def update_system_info(self):
        """Обновление информации о системе"""
        info = f"🧪 Sound Isolation Tester - Защита от спуфинг-атак\n"
        info += f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        info += f"🐍 Python: {sys.version.split()[0]}\n"
        info += f"💻 ОС: {sys.platform}\n"
        info += f"📁 Папка проекта: {os.path.abspath('.')}\n"
        
        # Подсчет записей
        if os.path.exists(self.recordings_folder):
            wav_files = [f for f in os.listdir(self.recordings_folder) if f.endswith('.wav')]
            info += f"🎙️ Записей: {len(wav_files) // 2}\n"
        else:
            info += f"🎙️ Записей: папка не найдена\n"
    
        # Проверка моделей
        info += "\n🔍 Проверка моделей:\n"
        models_found = 0
    
        # Whisper
        for model in ["tiny", "small", "medium"]:
            if os.path.exists(f"models/whisper/{model}.pt"):
                info += f"  ✅ Whisper {model}\n"
                models_found += 1
            else:
                info += f"  ❌ Whisper {model} (отсутствует)\n"
    
        # Vosk
        if os.path.exists("models/vosk/small-ru"):
            info += f"  ✅ Vosk small-ru\n"
            models_found += 1
        else:
            info += f"  ❌ Vosk small-ru (отсутствует)\n"
    
        info += f"\n📊 Всего моделей: {models_found}/2\n"
    
        if models_found >= 2:
            info += "✅ Все модели готовы!"
        else:
            info += "⚠️ Загрузите недостающие модели!"
    
        self.system_info.delete(1.0, tk.END)
        self.system_info.insert(1.0, info)
        self.system_info.config(state=tk.DISABLED)
    
    def _analyze_recording(self, outside_path, inside_path, test_name, reference_text=None):
        """Анализ записи"""
        try:
            self.status_var.set("📊 Анализ записи...")
            
            analysis = self.analyzer.analyze_with_audio_analysis(
                outside_path, inside_path, test_name,
                reference_text=reference_text,
                enable_speech_recognition=bool(self.recognizer)
            )
            
            # Показываем результаты
            self._display_analysis_results(analysis)
            
            self.status_var.set("✅ Анализ завершен")
            
        except Exception as e:
            self.status_var.set("❌ Ошибка анализа")
            messagebox.showwarning("Предупреждение", f"Ошибка анализа: {e}")
    
    def _display_analysis_results(self, analysis):
        """Отобразить результаты анализа для аттестации помещения"""
        try:
            overall = analysis.get('results', {}).get('overall_assessment', {})
            isolation = analysis.get('results', {}).get('isolation_assessment', {})
            audio = analysis.get('results', {}).get('audio_analysis', {})
            speech = analysis.get('results', {}).get('speech_recognition', {})
        
            result_text = "=" * 70 + "\n"
            result_text += f"АТТЕСТАЦИЯ ЗВУКОИЗОЛЯЦИИ ПОМЕЩЕНИЯ\n"
            result_text += f"Тест: {analysis.get('test_name', 'N/A')}\n"
            result_text += f"Время: {analysis.get('timestamp', 'N/A')}\n"
            result_text += "=" * 70 + "\n\n"
        
            # 1. ПРОВЕРКА ЭТАЛОНА (внутренняя запись)
            result_text += "🔍 ПРОВЕРКА ВНУТРИ ПОМЕЩЕНИЯ:\n"
            result_text += "-" * 40 + "\n"
        
            if isolation and 'inside_reference_check' in isolation:
                inside_check = isolation['inside_reference_check']
                if inside_check.get('valid', False):
                    result_text += "✅ Речь распознана корректно\n"
                else:
                    result_text += "⚠️ Проблемы с распознаванием!\n"
            
                if 'match_score' in inside_check:
                    result_text += f"   Совпадение с текстом: {inside_check.get('match_score', 0)*100:.1f}%\n"
                if 'confidence' in inside_check:
                    result_text += f"   Уверенность распознавания: {inside_check.get('confidence', 0)*100:.1f}%\n"
            
                if 'recognized' in inside_check and inside_check['recognized']:
                    recognized = inside_check['recognized']
                    if len(recognized) > 100:
                        recognized = recognized[:100] + "..."
                    result_text += f"   Распознанный текст: \"{recognized}\"\n"
            else:
                result_text += "ℹ️ Проверка не выполнена\n"
        
            result_text += "\n"
        
            # 2. ОЦЕНКА ЗВУКОИЗОЛЯЦИИ
            result_text += "📊 ОЦЕНКА ЗВУКОИЗОЛЯЦИИ ПОМЕЩЕНИЯ:\n"
            result_text += "-" * 40 + "\n"
        
            # 2.1 Оценка по громкости
            if audio and 'level_comparison' in audio:
                level_data = audio['level_comparison']
                attenuation = level_data.get('attenuation_db', 0)
                inside_rms = level_data.get('inside_rms', 0)
                outside_rms = level_data.get('outside_rms', 0)
            
                result_text += f"🎚️ УРОВНИ ГРОМКОСТИ:\n"
                result_text += f"   • Внутри (источник): {inside_rms:.4f}\n"
                result_text += f"   • Снаружи (измерение): {outside_rms:.4f}\n"
                result_text += f"   • Ослабление звука: {attenuation:.1f} дБ\n"
            
                if 'level_reduction_ratio' in level_data:
                    reduction = level_data['level_reduction_ratio'] * 100
                    result_text += f"   • Звука вышло наружу: {reduction:.1f}%\n"
            
                result_text += "\n"
        
            # 2.2 Оценка по распознаванию речи
            if isolation and 'isolation_metrics' in isolation:
                iso_metrics = isolation['isolation_metrics']
            
                result_text += f"🗣️ ОЦЕНКА ПО РАСПОЗНАВАНИЮ РЕЧИ:\n"
            
                if 'inside_similarity' in iso_metrics and 'outside_similarity' in iso_metrics:
                    inside_sim = iso_metrics['inside_similarity'] * 100
                    outside_sim = iso_metrics['outside_similarity'] * 100
                    result_text += f"   • Сходство с эталоном внутри: {inside_sim:.1f}%\n"
                    result_text += f"   • Сходство с эталоном снаружи: {outside_sim:.1f}%\n"
                
                    if inside_sim > 0:
                        efficiency = (1 - (outside_sim / inside_sim)) * 100
                        result_text += f"   • Эффективность изоляции: {efficiency:.1f}%\n"
            
                if 'words_total' in iso_metrics:
                    total = iso_metrics['words_total']
                    inside_words = iso_metrics.get('words_understood_inside', 0)
                    outside_words = iso_metrics.get('words_understood_outside', 0)
                    lost_words = iso_metrics.get('words_lost', 0)
                
                    result_text += f"\n   📝 АНАЛИЗ СЛОВ:\n"
                    result_text += f"   • Всего слов в фразе: {total}\n"
                    result_text += f"   • Слов распознано внутри: {inside_words}/{total} ({inside_words/total*100:.0f}%)\n"
                    result_text += f"   • Слов распознано снаружи: {outside_words}/{total} ({outside_words/total*100:.0f}%)\n"
                    result_text += f"   • Слов потеряно при изоляции: {lost_words}\n"
            
                if 'leakage_percentage' in iso_metrics:
                    leakage = iso_metrics['leakage_percentage']
                    result_text += f"\n   🔄 УТЕЧКА РЕЧИ: {leakage:.1f}%\n"
            
                result_text += "\n"
        
            # 3. ВЕРДИКТ
            result_text += "🏆 ВЕРДИКТ АТТЕСТАЦИИ:\n"
            result_text += "-" * 40 + "\n"
            verdict = overall.get('verdict', 'Н/Д')
            color = overall.get('color', 'black')
        
            # Создаем цветные метки
            if "ОТЛИЧНАЯ" in verdict:
                result_text += f"🎉 {verdict}\n"
            elif "ХОРОШАЯ" in verdict:
                result_text += f"✅ {verdict}\n"
            elif "УДОВЛЕТВОРИТЕЛЬНАЯ" in verdict:
                result_text += f"⚠️ {verdict}\n"
            elif "СЛАБАЯ" in verdict or "НЕЭФФЕКТИВНАЯ" in verdict:
                result_text += f"❌ {verdict}\n"
            else:
                result_text += f"{verdict}\n"
        
            result_text += f"\n📋 Сводка: {overall.get('summary', 'Н/Д')}\n"
        
            if 'isolation_score' in overall:
                result_text += f"🏅 Общая оценка: {overall.get('isolation_score', 0):.1f}/100\n"
        
            if 'composite_grade' in overall:
                result_text += f"📈 Оценка: {overall.get('composite_grade', 'Н/Д')}\n"
        
            result_text += "\n"
        
            # 4. РЕКОМЕНДАЦИИ
            recommendations = overall.get('recommendations', [])
            if recommendations:
                result_text += "💡 РЕКОМЕНДАЦИИ:\n"
                result_text += "-" * 40 + "\n"
                for i, rec in enumerate(recommendations, 1):
                    # Добавляем эмодзи в зависимости от типа рекомендации
                    if "усилить" in rec.lower() or "установить" in rec.lower() or "проверить" in rec.lower():
                        result_text += f"🔧 {i}. {rec}\n"
                    elif "обнаружена" in rec.lower() or "требуется" in rec.lower():
                        result_text += f"⚠️ {i}. {rec}\n"
                    elif "соответствует" in rec.lower() or "отличная" in rec.lower():
                        result_text += f"✅ {i}. {rec}\n"
                    else:
                        result_text += f"{i}. {rec}\n"
        
            result_text += "\n" + "=" * 70 + "\n"
            result_text += f"💡 ПРИМЕЧАНИЕ ДЛЯ ЭКСПЕРТА:\n"
            result_text += f"   Для точной аттестации рекомендуется:\n"
            result_text += f"   1. Провести 3-5 измерений в разных точках\n"
            result_text += f"   2. Использовать разные фразы для тестирования\n"
            result_text += f"   3. Учесть фоновый шум помещения\n"
            result_text += "=" * 70
        
            # Отображаем в интерфейсе
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result_text)
        
            # Настраиваем цвет вердикта
            start_line = result_text.split('\n').index("ВЕРДИКТ АТТЕСТАЦИИ:") + 2
            line_start = f"{start_line}.0"
            line_end = f"{start_line}.end"
        
            self.result_text.tag_add("verdict", line_start, line_end)
            self.result_text.tag_config("verdict", foreground=color, font=('Arial', 11, 'bold'))
        
            # Добавляем цвет для заголовков
            self.result_text.tag_add("header", "1.0", "1.end")
            self.result_text.tag_config("header", font=('Arial', 12, 'bold'), foreground='darkblue')
        
            self.result_text.config(state=tk.DISABLED)
        
        except Exception as e:
            print(f"Ошибка отображения результатов: {e}")
            import traceback
            traceback.print_exc()
        
            # Показываем хотя бы ошибку
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Ошибка отображения результатов: {str(e)}")
            self.result_text.config(state=tk.DISABLED)
    
    def refresh_recordings_list(self):
        """Обновить список записей"""
        try:
            # Очищаем дерево
            for item in self.recordings_tree.get_children():
                self.recordings_tree.delete(item)
            
            # Получаем список записей
            recordings = self._get_recordings_list()
            
            # Добавляем записи в дерево
            for rec in recordings:
                self.recordings_tree.insert("", tk.END, values=(
                    rec.get('test_name', 'N/A'),
                    rec.get('timestamp', 'N/A'),
                    rec.get('duration', 'N/A'),
                    rec.get('size', 'N/A'),
                    rec.get('status', 'N/A'),
                    rec.get('engine', 'N/A'),
                    rec.get('text_check', 'N/A')
                ))
            
        except Exception as e:
            print(f"Ошибка обновления списка записей: {e}")
    
    def _get_recordings_list(self):
        """Получить список записей"""
        recordings = []
        
        try:
            # Сканируем папку recordings
            for file in os.listdir(self.recordings_folder):
                if file.endswith('_metadata.json'):
                    metadata_path = os.path.join(self.recordings_folder, file)
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            
                            # Определяем статус проверки текста
                            text_check_status = "❓ Нет данных"
                            analysis_file = os.path.join(self.recordings_folder, 
                                                        f"{metadata.get('test_name', '')}_analysis.json")
                            if os.path.exists(analysis_file):
                                with open(analysis_file, 'r', encoding='utf-8') as af:
                                    analysis_data = json.load(af)
                                    text_val = analysis_data.get('results', {}).get('text_validation', {})
                                    if text_val:
                                        text_check_status = "✅ Проверен" if text_val.get('valid') else "❌ Не совпадает"
                            
                            # Формируем информацию о записи
                            rec_info = {
                                'test_name': metadata.get('test_name', file.replace('_metadata.json', '')),
                                'timestamp': metadata.get('timestamp', 'N/A'),
                                'duration': f"{metadata.get('duration', 0):.1f} сек",
                                'size': self._get_recording_size(metadata),
                                'status': '✅' if metadata.get('analysis_ready', False) else '⚠️',
                                'engine': metadata.get('analysis_engine', 'N/A'),
                                'text_check': text_check_status
                            }
                            recordings.append(rec_info)
                            
                    except Exception as e:
                        print(f"Ошибка чтения {file}: {e}")
            
            # Сортируем по дате (сначала новые)
            recordings.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
        except Exception as e:
            print(f"Ошибка получения списка записей: {e}")
        
        return recordings
    
    def _get_recording_size(self, metadata):
        """Получить размер записи"""
        try:
            files = metadata.get('files', {})
            total_size = 0
            
            for channel in ['outside', 'inside']:
                file_info = files.get(channel, {})
                filepath = file_info.get('filepath')
                if filepath and os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
            
            # Конвертируем в КБ/МБ
            if total_size > 1024 * 1024:
                return f"{total_size / (1024 * 1024):.1f} МБ"
            else:
                return f"{total_size / 1024:.0f} КБ"
                
        except:
            return "N/A"
    
    def analyze_selected(self):
        """Анализ выбранной записи"""
        try:
            selection = self.recordings_tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите запись для анализа")
                return
            
            # Получаем данные выбранной записи
            item = self.recordings_tree.item(selection[0])
            test_name = item['values'][0]
            
            # Находим файлы записи
            outside_path = os.path.join(self.recordings_folder, f"{test_name}_outside.wav")
            inside_path = os.path.join(self.recordings_folder, f"{test_name}_inside.wav")
            
            if not os.path.exists(outside_path) or not os.path.exists(inside_path):
                messagebox.showerror("Ошибка", "Файлы записи не найдены")
                return
            
            # Читаем метаданные для получения текста
            reference_text = None
            metadata_path = os.path.join(self.recordings_folder, f"{test_name}_metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    reference_text = metadata.get('reference_text')
            
            # Выполняем анализ
            self.status_var.set("📊 Анализ записи...")
            
            analysis = self.analyzer.analyze_with_audio_analysis(
                outside_path, inside_path, test_name,
                reference_text=reference_text,
                enable_speech_recognition=bool(self.recognizer)
            )
            
            # Отображаем результаты
            self._display_analysis_results(analysis)
            
            self.status_var.set("✅ Анализ завершен")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка анализа: {e}")
    
    def recognize_speech(self):
        """Распознавание речи для оценки звукоизоляции помещения с проверкой спуфинга"""
        try:
            if not self.recognizer:
                messagebox.showwarning("Предупреждение", 
                    "Модуль распознавания речи недоступен.\n"
                    "1. Установите модели через вкладку 'Движки'\n"
                    "2. Выберите движок распознавания")
                return
    
            selection = self.recordings_tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите запись для распознавания")
                return
    
            # Получаем данные выбранной записи
            item = self.recordings_tree.item(selection[0])
            test_name = item['values'][0]
    
            # Находим файлы записи
            outside_path = os.path.join(self.recordings_folder, f"{test_name}_outside.wav")
            inside_path = os.path.join(self.recordings_folder, f"{test_name}_inside.wav")
    
            if not os.path.exists(outside_path) or not os.path.exists(inside_path):
                messagebox.showerror("Ошибка", "Файлы записи не найдены")
                return
    
            # Получаем эталонный текст из метаданных
            reference_text = None
            metadata_path = os.path.join(self.recordings_folder, f"{test_name}_metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    reference_text = metadata.get('reference_text')
    
            # Если фразы нет в метаданных, запрашиваем её у пользователя
            need_spoofing_check = False
            if not reference_text:
                # Спрашиваем, нужно ли проверять спуфинг
                check_spoofing = messagebox.askyesno(
                    "Проверка спуфинга",
                    "Хотите проверить запись на спуфинг-атаку?\n\n"
                    "Для этого нужно ввести фразу, которая должна быть произнесена в записи."
                )
            
                if check_spoofing:
                    reference_text = simpledialog.askstring("Введите фразу для проверки", 
                        "Введите эталонный текст для проверки спуфинга:\n"
                        "(фраза, которая должна быть произнесена в записи)")
                
                    if not reference_text:
                        messagebox.showinfo("Информация", 
                            "Проверка спуфинга отменена. Выполняется только распознавание речи.")
                    else:
                        need_spoofing_check = True
            else:
                # Фраза есть в метаданных - автоматически проверяем спуфинг
                need_spoofing_check = True
    
            # Распознавание речи
            self.status_var.set("🎤 Распознавание речи для оценки изоляции...")
    
            # Показываем прогресс
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Распознавание речи" + (" с проверкой спуфинга" if need_spoofing_check else ""))
            progress_window.geometry("400x200")
            progress_window.transient(self.root)
            progress_window.grab_set()
    
            # Центрируем
            progress_window.update_idletasks()
            x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
            y = (self.root.winfo_screenheight() // 2) - (200 // 2)
            progress_window.geometry(f'400x200+{x}+{y}')
    
            ttk.Label(progress_window, text="🔄 Распознавание речи..." + 
                     ("\n(с проверкой спуфинга)" if need_spoofing_check else ""),
                    font=('Arial', 12, 'bold')).pack(pady=20)
    
            progress_var = tk.StringVar(value="Начинаю распознавание...")
            ttk.Label(progress_window, textvariable=progress_var).pack()
    
            # Запускаем в отдельном потоке
            result_container = []
            spoofing_result_container = []
    
            def recognize_thread():
                try:
                    # Распознаем речь в обоих файлах
                    progress_var.set("Распознаю внутреннюю запись...")
                    inside_result = self.recognizer.transcribe(inside_path)
                
                    progress_var.set("Распознаю внешнюю запись...")
                    outside_result = self.recognizer.transcribe(outside_path)
                
                    # Получаем результаты сравнения
                    result = self.recognizer.analyze_pair(outside_path, inside_path, reference_text)
                    result_container.append(result)
                
                    # Если нужно проверить спуфинг
                    if need_spoofing_check and reference_text and inside_result:
                        progress_var.set("Проверка спуфинга...")
                    
                        # Сравниваем распознанную речь с эталоном
                        match_score = self._calculate_text_match(inside_result.text, reference_text)
                        passed = match_score >= 0.8  # 80% порог
                    
                        spoofing_result = {
                            'performed': True,
                            'success': True,
                            'test_name': test_name,
                            'reference_text': reference_text,
                            'recognized_text': inside_result.text,
                            'match_score': match_score,
                            'match_percent': match_score * 100,
                            'passed': passed,
                            'threshold': 0.8,
                            'confidence': inside_result.confidence if hasattr(inside_result, 'confidence') else 0,
                            'engine': result.get('engine', 'N/A')
                        }
                        spoofing_result_container.append(spoofing_result)
                
                    progress_var.set("✅ Распознавание завершено")
                    time.sleep(1)
                    progress_window.destroy()
                
                except Exception as e:
                    progress_var.set(f"❌ Ошибка: {str(e)[:50]}")
                    result_container.append({'error': str(e)})
                    time.sleep(2)
                    progress_window.destroy()
    
            threading.Thread(target=recognize_thread, daemon=True).start()
    
            # Ждем завершения
            self.root.wait_window(progress_window)
    
            if not result_container:
                messagebox.showerror("Ошибка", "Распознавание не выполнено")
                return
    
            result = result_container[0]
    
            if 'error' in result:
                messagebox.showerror("Ошибка", f"Ошибка распознавания: {result['error']}")
                self.status_var.set("❌ Ошибка распознавания")
                return
    
            # ПРАВИЛЬНАЯ ЛОГИКА ДЛЯ АТТЕСТАЦИИ ПОМЕЩЕНИЯ:
            # 1. Получаем распознанные тексты
            inside_text = result.get('inside', {}).get('text', '')
            outside_text = result.get('outside', {}).get('text', '')
            inside_confidence = result.get('inside', {}).get('confidence', 0)
            outside_confidence = result.get('outside', {}).get('confidence', 0)
    
            # 2. Проверяем эталон (внутри должен хорошо распознаваться)
            inside_validation = None
            if reference_text:
                inside_validation = self.analyzer._validate_spoken_text(
                    inside_text, reference_text, inside_confidence
                )
        
            # 3. Оцениваем изоляцию помещения
            # Создаем структуру, похожую на speech_analysis
            speech_analysis = {
                'inside': {'text': inside_text, 'confidence': inside_confidence},
                'outside': {'text': outside_text, 'confidence': outside_confidence},
                'comparison': result.get('comparison', {})
            }
    
            # Получаем аудиоанализ для правильного расчета дБ
            audio_analysis = self.analyzer._perform_audio_analysis(outside_path, inside_path)
    
            # Оцениваем изоляцию помещения
            isolation_assessment = self.analyzer._assess_room_isolation(
                speech_analysis, reference_text, audio_analysis
            )
    
            # 4. Отображаем результаты для аттестации с проверкой спуфинга
            result_text = "=" * 70 + "\n"
            result_text += f"ОЦЕНКА ЗВУКОИЗОЛЯЦИИ ПО РАСПОЗНАВАНИЮ РЕЧИ\n"
            result_text += f"Тест: {test_name}\n"
            result_text += f"Движок: {result.get('engine', 'N/A')}\n"
        
            # Добавляем информацию о проверке спуфинга
            if spoofing_result_container:
                spoofing_result = spoofing_result_container[0]
                result_text += f"Проверка спуфинга: {'✅ ВКЛЮЧЕНА' if spoofing_result.get('success') else '❌ ОШИБКА'}\n"
            elif reference_text:
                result_text += f"Проверка спуфинга: ℹ️ ВЫПОЛНЕНА (через анализатор)\n"
            else:
                result_text += f"Проверка спуфинга: ⚠️ НЕ ВЫПОЛНЕНА (нет эталонной фразы)\n"
            
            result_text += "=" * 70 + "\n\n"
    
            # 4.1 Проверка эталона (внутри) и спуфинга
            result_text += "🔍 ПРОВЕРКА АУДИО ВНУТРИ ПОМЕЩЕНИЯ:\n"
            result_text += "-" * 40 + "\n"
        
            # Если есть проверка спуфинга, показываем её
            if spoofing_result_container:
                spoofing_result = spoofing_result_container[0]
                if spoofing_result.get('success'):
                    if spoofing_result.get('passed'):
                        result_text += "✅ СПУФИНГ-АТАКА НЕ ОБНАРУЖЕНА\n"
                    else:
                        result_text += "❌ ВОЗМОЖНА СПУФИНГ-АТАКА!\n"
                
                    result_text += f"   Совпадение с эталоном: {spoofing_result.get('match_percent', 0):.1f}%\n"
                    result_text += f"   Порог прохождения: {spoofing_result.get('threshold', 0)*100}%\n"
                    result_text += f"   Уверенность распознавания: {spoofing_result.get('confidence', 0)*100:.1f}%\n"
                
                    # Показываем фразы
                    ref_text = spoofing_result.get('reference_text', '')
                    if len(ref_text) > 80:
                        ref_text = ref_text[:77] + "..."
                    result_text += f"   Эталонная фраза: \"{ref_text}\"\n"
                
                    rec_text = spoofing_result.get('recognized_text', '')
                    if len(rec_text) > 80:
                        rec_text = rec_text[:77] + "..."
                    result_text += f"   Распознанная фраза: \"{rec_text}\"\n"
                
                    # Рекомендации по спуфингу
                    if not spoofing_result.get('passed', False):
                        result_text += "\n   ⚠️ РЕКОМЕНДАЦИИ ПО СПУФИНГУ:\n"
                        if spoofing_result.get('match_percent', 0) >= 60:
                            result_text += "   • Возможны ошибки распознавания\n"
                            result_text += "   • Повторите запись с более четкой речью\n"
                        else:
                            result_text += "   • Высокая вероятность спуфинг-атаки\n"
                            result_text += "   • Проверьте источник звука\n"
                            result_text += "   • Убедитесь, что используется живая речь\n"
            elif inside_validation:
                if inside_validation.get('valid', False):
                    result_text += "✅ Речь распознана корректно\n"
                else:
                    result_text += "⚠️ Проблемы с распознаванием!\n"
        
                result_text += f"   Совпадение с текстом: {inside_validation.get('match_score', 0)*100:.1f}%\n"
                result_text += f"   Уверенность распознавания: {inside_validation.get('confidence', 0)*100:.1f}%\n"
        
                if 'recognized' in inside_validation and inside_validation['recognized']:
                    recognized = inside_validation['recognized']
                    if len(recognized) > 80:
                        recognized = recognized[:80] + "..."
                    result_text += f"   Распознанный текст: \"{recognized}\"\n"
            else:
                result_text += "ℹ️ Проверка эталона не выполнена\n"
    
            result_text += "\n"
    
            # 4.2 Что распознано внутри и снаружи
            result_text += "📝 РАСПОЗНАННЫЕ ТЕКСТЫ:\n"
            result_text += "-" * 40 + "\n"
    
            result_text += f"🎤 ВНУТРИ: \n"
            if inside_text:
                if len(inside_text) > 100:
                    inside_display = inside_text[:100] + "..."
                else:
                    inside_display = inside_text
                result_text += f"   \"{inside_display}\"\n"
                result_text += f"   Уверенность: {inside_confidence:.2f}\n"
                result_text += f"   Слов: {len(inside_text.split())}\n"
            else:
                result_text += "   ❌ Не распознано\n"
    
            result_text += f"\n📡 СНАРУЖИ (тест изоляции):\n"
            if outside_text:
                if len(outside_text) > 100:
                    outside_display = outside_text[:100] + "..."
                else:
                    outside_display = outside_text
                result_text += f"   \"{outside_display}\"\n"
                result_text += f"   Уверенность: {outside_confidence:.2f}\n"
                result_text += f"   Слов: {len(outside_text.split())}\n"
            else:
                result_text += "   ✅ Не распознано (хорошая изоляция!)\n"
    
            result_text += "\n"
    
            # 4.3 Оценка изоляции
            result_text += "📊 ОЦЕНКА ЗВУКОИЗОЛЯЦИИ ПО РАСПОЗНАВАНИЮ:\n"
            result_text += "-" * 40 + "\n"
    
            if isolation_assessment and 'isolation_metrics' in isolation_assessment:
                iso_metrics = isolation_assessment['isolation_metrics']
        
                # Оценка по сходству текстов
                if 'inside_similarity' in iso_metrics and 'outside_similarity' in iso_metrics:
                    inside_sim = iso_metrics['inside_similarity'] * 100
                    outside_sim = iso_metrics['outside_similarity'] * 100
            
                    result_text += f"   Сходство с эталоном:\n"
                    result_text += f"   • Внутри: {inside_sim:.1f}%\n"
                    result_text += f"   • Снаружи: {outside_sim:.1f}%\n"
            
                    if inside_sim > 0:
                        efficiency = (1 - (outside_sim / inside_sim)) * 100
                        result_text += f"   • Эффективность изоляции: {efficiency:.1f}%\n\n"
                
                        if efficiency > 70:
                            result_text += f"   🎉 ОТЛИЧНАЯ изоляция!\n"
                        elif efficiency > 50:
                            result_text += f"   ✅ ХОРОШАЯ изоляция\n"
                        elif efficiency > 30:
                            result_text += f"   ⚠️ УДОВЛЕТВОРИТЕЛЬНАЯ изоляция\n"
                        else:
                            result_text += f"   ❌ СЛАБАЯ изоляция\n"
        
                # Оценка по словам
                if 'words_total' in iso_metrics:
                    total = iso_metrics['words_total']
                    inside_words = iso_metrics.get('words_understood_inside', 0)
                    outside_words = iso_metrics.get('words_understood_outside', 0)
                    lost_words = iso_metrics.get('words_lost', 0)
            
                    result_text += f"\n   📝 АНАЛИЗ СЛОВ:\n"
                    result_text += f"   • Всего слов: {total}\n"
                    result_text += f"   • Распознано внутри: {inside_words}/{total} ({inside_words/total*100:.0f}%)\n"
                    result_text += f"   • Распознано снаружи: {outside_words}/{total} ({outside_words/total*100:.0f}%)\n"
                    result_text += f"   • Слов потеряно: {lost_words}\n"
            
                    if lost_words == 0 and outside_words == 0:
                        result_text += f"   🎉 Идеальная изоляция - снаружи ничего не слышно!\n"
                    elif lost_words > total * 0.5:
                        result_text += f"   ✅ Хорошая изоляция - потеряно более половины слов\n"
                    elif lost_words > 0:
                        result_text += f"   ⚠️ Умеренная изоляция\n"
                    else:
                        result_text += f"   ❌ Слабая изоляция - все слова слышны снаружи\n"
        
                # Оценка по дБ (из аудиоанализа)
                if 'attenuation_db' in iso_metrics:
                    attenuation = iso_metrics['attenuation_db']
                    result_text += f"\n   🔊 ОСЛАБЛЕНИЕ ЗВУКА: {attenuation:.1f} дБ\n"
            
                    if attenuation >= 50:
                        result_text += f"   🎉 Отличная звукоизоляция!\n"
                    elif attenuation >= 40:
                        result_text += f"   ✅ Хорошая звукоизоляция\n"
                    elif attenuation >= 30:
                        result_text += f"   ⚠️ Удовлетворительная изоляция\n"
                    elif attenuation >= 20:
                        result_text += f"   ⚠️ Слабая изоляция\n"
                    else:
                        result_text += f"   ❌ Неэффективная изоляция\n"
    
            # 4.4 Сравнительные метрики
            if 'comparison' in result:
                comparison = result['comparison']
                if 'wer' in comparison:
                    wer = comparison['wer']
                    result_text += f"\n📈 СРАВНИТЕЛЬНЫЕ МЕТРИКИ:\n"
                    result_text += f"-" * 40 + "\n"
                    result_text += f"   WER (ошибок на слово): {wer:.2%}\n"
            
                    if wer > 0.8:
                        result_text += f"   ✅ Отличная изоляция (высокий WER)\n"
                    elif wer > 0.6:
                        result_text += f"   ✅ Хорошая изоляция\n"
                    elif wer > 0.4:
                        result_text += f"   ⚠️ Умеренная изоляция\n"
                    else:
                        result_text += f"   ❌ Слабая изоляция (низкий WER)\n"
            
                    if comparison.get('leakage_detected', False):
                        result_text += f"   ⚠️ ОБНАРУЖЕНА УТЕЧКА РЕЧИ!\n"
    
            # 4.5 Рекомендации (обновленные с учетом спуфинга)
            result_text += "\n💡 РЕКОМЕНДАЦИИ:\n"
            result_text += "-" * 40 + "\n"
    
            # Добавляем рекомендации по спуфингу
            if spoofing_result_container:
                spoofing_result = spoofing_result_container[0]
                if spoofing_result.get('passed', False):
                    result_text += "1. 🛡️ Спуфинг-атака НЕ обнаружена\n"
                else:
                    result_text += "1. ⚠️ ВОЗМОЖНА СПУФИНГ-АТАКА\n"
                    result_text += "   • Проверьте источник звука\n"
                    result_text += "   • Убедитесь в использовании живой речи\n"
                    result_text += "   • Повторите тест с новой фразой\n"
        
            # Стандартные рекомендации по изоляции
            if isolation_assessment and 'isolation_metrics' in isolation_assessment:
                iso_metrics = isolation_assessment['isolation_metrics']
        
                if 'attenuation_db' in iso_metrics:
                    attenuation = iso_metrics['attenuation_db']
            
                    if attenuation < 30:
                        result_text += "2. 🔧 Усилить изоляцию стен и перекрытий\n"
                        result_text += "3. 🔧 Установить звукопоглощающие материалы\n"
                        result_text += "4. 🔧 Проверить герметичность окон и дверей\n"
                    elif attenuation < 40:
                        result_text += "2. ✅ Изоляция удовлетворительная\n"
                        result_text += "3. 🔧 Рассмотреть дополнительную звукоизоляцию\n"
                    else:
                        result_text += "2. 🎉 Изоляция соответствует нормам\n"
                        result_text += "3. ✅ Поддерживать текущее состояние\n"
        
                if 'words_lost' in iso_metrics:
                    lost_words = iso_metrics['words_lost']
                    if lost_words == 0:
                        result_text += "4. 🎉 Идеальная изоляция речи!\n"
                    elif lost_words < 3:
                        result_text += "4. ✅ Хорошая изоляция речи\n"
                    else:
                        result_text += "4. ⚠️ Рекомендуется улучшить изоляцию речи\n"
    
            result_text += "\n" + "=" * 70 + "\n"
            result_text += "💡 Для точной аттестации:\n"
            result_text += "   • Проведите 3-5 измерений\n"
            result_text += "   • Используйте разные фразы\n"
            result_text += "   • Учтите фоновый шум\n"
        
            # Добавляем примечание о спуфинге
            if need_spoofing_check and spoofing_result_container:
                spoofing_result = spoofing_result_container[0]
                result_text += "\n🛡️ Защита от спуфинга:\n"
                result_text += "   • Всегда используйте уникальные фразы\n"
                result_text += "   • Проверяйте соответствие текста\n"
                result_text += "   • Анализируйте технические показатели\n"
            
            result_text += "=" * 70
    
            # Отображаем в интерфейсе
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result_text)
    
            # Настраиваем форматирование
            # Жирный заголовок
            self.result_text.tag_add("header", "1.0", "1.end")
            self.result_text.tag_config("header", font=('Arial', 12, 'bold'), foreground='darkblue')
    
            # Цветные разделы
            import re
            lines = result_text.split('\n')
            for i, line in enumerate(lines, 1):
                if "ПРОВЕРКА АУДИО" in line:
                    self.result_text.tag_add(f"section{i}", f"{i}.0", f"{i}.end")
                    color = "darkgreen"
                    if spoofing_result_container:
                        spoofing_result = spoofing_result_container[0]
                        if not spoofing_result.get('passed', False):
                            color = "darkred"
                    self.result_text.tag_config(f"section{i}", font=('Arial', 11, 'bold'), foreground=color)
                elif "РАСПОЗНАННЫЕ ТЕКСТЫ" in line:
                    self.result_text.tag_add(f"section{i}", f"{i}.0", f"{i}.end")
                    self.result_text.tag_config(f"section{i}", font=('Arial', 11, 'bold'), foreground='darkblue')
                elif "ОЦЕНКА ЗВУКОИЗОЛЯЦИИ" in line:
                    self.result_text.tag_add(f"section{i}", f"{i}.0", f"{i}.end")
                    self.result_text.tag_config(f"section{i}", font=('Arial', 11, 'bold'), foreground='darkred')
                elif "СРАВНИТЕЛЬНЫЕ МЕТРИКИ" in line:
                    self.result_text.tag_add(f"section{i}", f"{i}.0", f"{i}.end")
                    self.result_text.tag_config(f"section{i}", font=('Arial', 11, 'bold'), foreground='purple')
                elif "РЕКОМЕНДАЦИИ" in line:
                    self.result_text.tag_add(f"section{i}", f"{i}.0", f"{i}.end")
                    self.result_text.tag_config(f"section{i}", font=('Arial', 11, 'bold'), foreground='darkorange')
    
            self.result_text.config(state=tk.DISABLED)
    
            # Показываем отдельное окно с результатом проверки спуфинга
            if spoofing_result_container:
                self.root.after(500, lambda: self._show_detailed_spoofing_result(
                    spoofing_result_container[0], test_name
                ))
    
            self.status_var.set("✅ Распознавание завершено, оценка изоляции готова" + 
                               (" (проверка спуфинга выполнена)" if spoofing_result_container else ""))
    
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка распознавания: {e}")
            import traceback
            traceback.print_exc()
            self.status_var.set("❌ Ошибка распознавания")
    
    def check_spoofing(self):
        """Проверка записи на спуфинг-атаки"""
        try:
            selection = self.recordings_tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите запись для проверки")
                return
            
            # Получаем данные выбранной записи
            item = self.recordings_tree.item(selection[0])
            test_name = item['values'][0]
            
            # Находим файлы записи
            outside_path = os.path.join(self.recordings_folder, f"{test_name}_outside.wav")
            
            if not os.path.exists(outside_path):
                messagebox.showerror("Ошибка", "Файл записи не найден")
                return
            
            # Проверяем спуфинг
            from spoof_detector import SpoofingDetector
            detector = SpoofingDetector()
            
            self.status_var.set("🛡️ Проверка на спуфинг...")
            
            spoof_result = detector.analyze_for_spoofing(outside_path)
            
            # Отображаем результаты
            result_text = "=" * 60 + "\n"
            result_text += f"ПРОВЕРКА НА СПУФИНГ-АТАКИ: {test_name}\n"
            result_text += "=" * 60 + "\n\n"
            
            if spoof_result:
                if spoof_result['is_spoofing_suspected']:
                    result_text += "❌ ОБНАРУЖЕНА ВОЗМОЖНАЯ СПУФИНГ-АТАКА!\n\n"
                    result_text += f"Тип атаки: {spoof_result['suspected_attack_type']}\n"
                    result_text += f"Уверенность: {spoof_result['confidence']*100:.1f}%\n\n"
                    
                    result_text += "Метрики анализа:\n"
                    for key, value in spoof_result['metrics'].items():
                        result_text += f"  • {key}: {value:.3f}\n"
                    
                    result_text += "\nПредупреждения:\n"
                    for warning in spoof_result['warnings']:
                        result_text += f"  ⚠️ {warning}\n"
                    
                    result_text += "\n💡 Рекомендации:\n"
                    result_text += "  • Проверьте источник звука\n"
                    result_text += "  • Убедитесь, что используется живая речь\n"
                    result_text += "  • Проверьте уровень громкости\n"
                    result_text += "  • Исключите использование музыки или шума\n"
                else:
                    result_text += "✅ СПУФИНГ-АТАКИ НЕ ОБНАРУЖЕНЫ\n\n"
                    result_text += "Метрики анализа:\n"
                    for key, value in spoof_result['metrics'].items():
                        result_text += f"  • {key}: {value:.3f}\n"
            else:
                result_text += "❌ Ошибка проверки спуфинга\n"
            
            result_text += "\n" + "=" * 60
            
            # Отображаем в интерфейсе
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result_text)
            self.result_text.config(state=tk.DISABLED)
            
            self.status_var.set("✅ Проверка спуфинга завершена")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка проверки спуфинга: {e}")
    
    def delete_recording(self):
        """Удалить выбранную запись"""
        try:
            selection = self.recordings_tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
                return
            
            # Подтверждение
            item = self.recordings_tree.item(selection[0])
            test_name = item['values'][0]
            
            confirm = messagebox.askyesno(
                "Подтверждение удаления",
                f"Вы уверены, что хотите удалить запись '{test_name}'?\n"
                f"Все связанные файлы будут удалены безвозвратно."
            )
            
            if not confirm:
                return
            
            # Удаляем файлы
            files_to_delete = [
                os.path.join(self.recordings_folder, f"{test_name}_outside.wav"),
                os.path.join(self.recordings_folder, f"{test_name}_inside.wav"),
                os.path.join(self.recordings_folder, f"{test_name}_metadata.json"),
                os.path.join(self.recordings_folder, f"{test_name}_analysis.json")
            ]
            
            deleted_count = 0
            for filepath in files_to_delete:
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                    except Exception as e:
                        print(f"Ошибка удаления {filepath}: {e}")
            
            # Обновляем список
            self.refresh_recordings_list()
            
            messagebox.showinfo("Успех", f"Удалено записей: {deleted_count}/4")
            self.status_var.set("🗑️ Запись удалена")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка удаления: {e}")
    
    def generate_report(self):
        """Сгенерировать отчет по выбранной записи с данными распознавания"""
        try:
            # 1. Проверяем, есть ли выбранная запись
            selection = self.recordings_tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите запись для отчета")
                return
    
            # 2. Получаем название теста
            item = self.recordings_tree.item(selection[0])
            test_name = item['values'][0]
    
            # 3. Парсим данные ИЗ ТЕКСТА РЕЗУЛЬТАТОВ в интерфейсе
            report_data = self._parse_results_from_displayed_text(test_name)
    
            # 4. Если нет данных в интерфейсе, спрашиваем, распознать ли речь
            if not report_data['has_speech_data']:
                response = messagebox.askyesno(
                    "Нет данных распознавания",
                    "В результатах анализа нет данных распознавания речи.\n\n"
                    "Хотите сначала выполнить распознавание речи?"
                )
            
                if response:
                    # Запускаем распознавание
                    self.recognize_speech()
                    # Ждем немного и пытаемся снова
                    self.root.after(2000, lambda: self.generate_report())
                    return
                else:
                    # Создаем отчет без данных распознавания
                    report_data = self._create_basic_report_data(test_name)
    
            # 5. Показываем окно выбора формата
            self._show_format_selection_dialog(test_name, report_data)
    
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка генерации отчета: {e}")
            import traceback
            traceback.print_exc()

    def _parse_results_from_displayed_text(self, test_name):
        """Парсить данные распознавания из текста, отображаемого в интерфейсе"""
        report_data = {
            'test_name': test_name,
            'has_speech_data': False,
            'has_spoofing_data': False,
            'has_analysis_data': False,
            'speech_results': {},
            'spoofing_results': {},
            'analysis_results': {},
            'parsed_sections': [],
            'metadata': self._load_test_metadata(test_name)
        }

        try:
            # Получаем весь текст из поля результатов
            result_text = self.result_text.get("1.0", tk.END)

            if not result_text or result_text.strip() == "":
                print("⚠️ Текст результатов пуст")
                return report_data

            # Разбиваем на строки для анализа
            lines = result_text.split('\n')

            print(f"🔍 Анализирую {len(lines)} строк...")

            # Проходим по всем строкам и ищем нужные данные
            for i, line in enumerate(lines):
                line = line.strip()

                # ============ РАСПОЗНАННЫЕ ТЕКСТЫ И УВЕРЕННОСТЬ ============
                if line == "📝 РАСПОЗНАННЫЕ ТЕКСТЫ:":
                    report_data['parsed_sections'].append('speech')
                    # Ищем следующие строки с данными
                    j = i + 1
                    while j < len(lines) and not lines[j].startswith("📊"):
                        line_text = lines[j].strip()
                    
                        # Текст внутри помещения
                        if "🎤 ВНУТРИ:" in line_text:
                            # Ищем текст на следующей строке
                            if j + 1 < len(lines):
                                inside_line = lines[j + 1].strip()
                                if inside_line and not inside_line.startswith("Уверенность:"):
                                    # Убираем кавычки если есть
                                    inside_text = inside_line.strip('"').strip()
                                    if inside_text and inside_text != "❌ Не распознано":
                                        report_data['speech_results']['inside_text'] = inside_text
                                        report_data['has_speech_data'] = True
                    
                        # Уверенность внутри
                        elif "Уверенность:" in line_text and j > 0 and "🎤 ВНУТРИ" in lines[j-1]:
                            confidence = line_text.split(":")[1].strip()
                            report_data['speech_results']['inside_confidence'] = confidence
                            report_data['has_speech_data'] = True
                    
                        # Текст снаружи помещения
                        elif "📡 СНАРУЖИ" in line_text:
                            # Ищем текст на следующей строке
                            if j + 1 < len(lines):
                                outside_line = lines[j + 1].strip()
                                if outside_line and not outside_line.startswith("Уверенность:"):
                                    # Убираем кавычки если есть
                                    outside_text = outside_line.strip('"').strip()
                                    if outside_text and outside_text != "❌ Не распознано":
                                        report_data['speech_results']['outside_text'] = outside_text
                                        report_data['has_speech_data'] = True
                    
                        # Уверенность снаружи
                        elif "Уверенность:" in line_text and j > 0 and "📡 СНАРУЖИ" in lines[j-1]:
                            confidence = line_text.split(":")[1].strip()
                            report_data['speech_results']['outside_confidence'] = confidence
                            report_data['has_speech_data'] = True
                    
                        j += 1
            
                # ============ ПРОВЕРКА СПУФИНГА ============
                elif line.startswith("🔍 ПРОВЕРКА АУДИО ВНУТРИ ПОМЕЩЕНИЯ:"):
                    report_data['parsed_sections'].append('spoofing')
                    j = i + 1
                    while j < len(lines) and not lines[j].startswith("📝"):
                        if "Совпадение с эталоном:" in lines[j]:
                            match = lines[j].split(":")[1].strip()
                            report_data['spoofing_results']['match_score'] = match
                            report_data['has_spoofing_data'] = True
                    
                        elif "Порог прохождения:" in lines[j]:
                            threshold = lines[j].split(":")[1].strip()
                            report_data['spoofing_results']['threshold'] = threshold
                    
                        elif "Уверенность распознавания:" in lines[j]:
                            confidence = lines[j].split(":")[1].strip()
                            report_data['spoofing_results']['confidence'] = confidence
                    
                        elif "Эталонная фраза:" in lines[j]:
                            # Берем текст в кавычках
                            import re
                            match = re.search(r'"(.*?)"', lines[j])
                            if match:
                                report_data['spoofing_results']['reference_text'] = match.group(1)
                    
                        elif "Распознанная фраза:" in lines[j]:
                            # Берем текст в кавычках
                            import re
                            match = re.search(r'"(.*?)"', lines[j])
                            if match:
                                report_data['spoofing_results']['recognized_text'] = match.group(1)
                    
                        j += 1
            
                # ============ АНАЛИЗ ЗВУКОИЗОЛЯЦИИ ============
                elif line.startswith("📊 ОЦЕНКА ЗВУКОИЗОЛЯЦИИ"):
                    report_data['parsed_sections'].append('analysis')
                    j = i + 1
                    while j < len(lines) and not lines[j].startswith("📈"):
                        if "Ослабление звука:" in lines[j]:
                            # Ищем число с "дБ"
                            import re
                            match = re.search(r'(\d+\.?\d*)\s*дБ', lines[j])
                            if match:
                                report_data['analysis_results']['attenuation_db'] = match.group(1)
                                report_data['has_analysis_data'] = True
                    
                        elif "Эффективность изоляции:" in lines[j]:
                            # Ищем число с "%"
                            import re
                            match = re.search(r'(\d+\.?\d*)\s*%', lines[j])
                            if match:
                                report_data['analysis_results']['isolation_efficiency'] = match.group(1)
                    
                        elif "Всего слов в фразе:" in lines[j]:
                            words = lines[j].split(":")[1].strip()
                            report_data['analysis_results']['total_words'] = words
                    
                        elif "Слов потеряно при изоляции:" in lines[j]:
                            lost = lines[j].split(":")[1].strip()
                            report_data['analysis_results']['lost_words'] = lost
                    
                        j += 1
        
            # ============ АЛЬТЕРНАТИВНЫЙ ПОИСК (регулярные выражения) ============
            if not report_data['has_speech_data']:
                # Пробуем найти через регулярные выражения
                import re
            
                # Ищем текст внутри помещения
                inside_match = re.search(r'🎤 ВНУТРИ:\s*\n\s*"([^"]+)"', result_text, re.IGNORECASE)
                if inside_match:
                    report_data['speech_results']['inside_text'] = inside_match.group(1).strip()
                    report_data['has_speech_data'] = True
            
                # Ищем текст снаружи помещения
                outside_match = re.search(r'📡 СНАРУЖИ.*?:\s*\n\s*"([^"]+)"', result_text, re.IGNORECASE | re.DOTALL)
                if outside_match:
                    report_data['speech_results']['outside_text'] = outside_match.group(1).strip()
                    report_data['has_speech_data'] = True
        
            # ============ ЛОГИРОВАНИЕ РЕЗУЛЬТАТОВ ПАРСИНГА ============
            print(f"📊 Результаты парсинга для {test_name}:")
            print(f"  • Данные речи: {report_data['has_speech_data']}")
            print(f"  • Данные спуфинга: {report_data['has_spoofing_data']}")
            print(f"  • Данные анализа: {report_data['has_analysis_data']}")
            print(f"  • Разделы: {report_data['parsed_sections']}")
        
            if report_data['has_speech_data']:
                print(f"  • Внутри: '{report_data['speech_results'].get('inside_text', 'Нет')}'")
                print(f"  • Снаружи: '{report_data['speech_results'].get('outside_text', 'Нет')}'")
    
        except Exception as e:
            print(f"❌ Ошибка парсинга текста: {e}")
            import traceback
            traceback.print_exc()
    
        return report_data
    
    def _create_basic_report_data(self, test_name):
        """Создать базовые данные отчета без распознавания"""
        metadata = self._load_test_metadata(test_name)
    
        return {
            'test_name': test_name,
            'has_speech_data': False,
            'has_spoofing_data': False,
            'has_analysis_data': False,
            'speech_results': {},
            'spoofing_results': {},
            'analysis_results': {},
            'parsed_sections': ['basic'],
            'metadata': metadata
        }

    def _create_report_file(self, test_name, format_type, report_data):
        """Создать файл отчета в указанном формате"""
        try:
            # Создаем папку reports если не существует
            reports_folder = "reports"
            os.makedirs(reports_folder, exist_ok=True)
        
            # Запрашиваем место сохранения
            if format_type == "html":
                ext = ".html"
                filetypes = [("HTML файлы", "*.html"), ("Все файлы", "*.*")]
                # Предлагаем сохранить в папке reports по умолчанию
                initial_dir = reports_folder
                initial_file = f"{test_name}_report{ext}"
            elif format_type == "excel":
                ext = ".xlsx"
                filetypes = [("Excel файлы", "*.xlsx"), ("Все файлы", "*.*")]
                initial_dir = reports_folder
                initial_file = f"{test_name}_report{ext}"
            elif format_type == "csv":
                ext = ".csv"
                filetypes = [("CSV файлы", "*.csv"), ("Все файлы", "*.*")]
                initial_dir = reports_folder
                initial_file = f"{test_name}_report{ext}"
            elif format_type == "json":
                ext = ".json"
                filetypes = [("JSON файлы", "*.json"), ("Все файлы", "*.*")]
                initial_dir = reports_folder
                initial_file = f"{test_name}_report{ext}"
            else:
                ext = ".txt"
                filetypes = [("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
                initial_dir = reports_folder
                initial_file = f"{test_name}_report{ext}"
        
            filename = filedialog.asksaveasfilename(
                defaultextension=ext,
                filetypes=filetypes,
                initialdir=initial_dir,
                initialfile=initial_file
            )
        
            if not filename:
                return
        
            # Загружаем метаданные из файла
            metadata = self._load_test_metadata(test_name)
        
            # Создаем отчет в выбранном формате
            if format_type == "html":
                self._create_html_report(metadata, filename, report_data)
            elif format_type == "excel":
                self._create_excel_report(metadata, filename, report_data)
            elif format_type == "csv":
                self._create_csv_report(metadata, filename, report_data)
            elif format_type == "json":
                self._create_json_report(metadata, filename, report_data)
            else:
                self._create_text_report(metadata, filename, report_data)
        
            # Показываем результат
            messagebox.showinfo("Успех", f"Отчет сохранен:\n{filename}")
            self.status_var.set(f"📋 Отчет создан: {os.path.basename(filename)}")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка создания отчета: {e}")
    
    def _create_html_report(self, metadata, filename, report_data):
        """Создать HTML отчет"""
        # Убедимся, что metadata - это словарь, а не строка
        if isinstance(metadata, str):
            # Если передана строка (например, имя файла), загружаем метаданные
            metadata = self._load_test_metadata(metadata)

        # Получаем данные из метаданных
        test_name = metadata.get('test_name', 'Неизвестный тест') if isinstance(metadata, dict) else 'Неизвестный тест'
        timestamp = metadata.get('timestamp', 'Нет данных') if isinstance(metadata, dict) else 'Нет данных'
        duration = metadata.get('duration', 0) if isinstance(metadata, dict) else 0
        sample_rate = metadata.get('sample_rate', 0) if isinstance(metadata, dict) else 0
        reference_text = metadata.get('reference_text', 'Не задан') if isinstance(metadata, dict) else 'Не задан'

        # Используем report_data для заполнения данных распознавания
        speech_section = ""
        if report_data['has_speech_data']:
            speech_results = report_data['speech_results']
        
            # Получаем тексты и уверенности
            inside_text = speech_results.get('inside_text', 'Н/Д')
            inside_confidence = speech_results.get('inside_confidence', 'Н/Д')
            outside_text = speech_results.get('outside_text', 'Н/Д')
            outside_confidence = speech_results.get('outside_confidence', 'Н/Д')
        
            # Форматируем для отображения
            inside_display = f'"{inside_text}"' if inside_text != 'Н/Д' else 'Н/Д'
            outside_display = f'"{outside_text}"' if outside_text != 'Н/Д' else 'Н/Д'
        
            speech_section = f'''
            <div class="info-card">
                <h2>🎤 РЕЗУЛЬТАТЫ РАСПОЗНАВАНИЯ РЕЧИ</h2>
                <table>
                    <tr>
                        <th>Параметр</th>
                        <th>Значение</th>
                    </tr>
                    <tr>
                        <td>Текст внутри помещения</td>
                        <td>{inside_display}</td>
                    </tr>
                    <tr>
                        <td>Текст снаружи помещения</td>
                        <td>{outside_display}</td>
                    </tr>
                </table>
            </div>
            '''
        else:
            speech_section = '''
            <div class="info-card">
                <h2>🎤 РЕЗУЛЬТАТЫ РАСПОЗНАВАНИЯ РЕЧИ</h2>
                <table>
                    <tr>
                        <th>Параметр</th>
                        <th>Значение</th>
                    </tr>
                    <tr>
                        <td>Текст внутри помещения</td>
                        <td>Н/Д (данные распознавания отсутствуют)</td>
                    </tr>
                    <tr>
                        <td>Уверенность внутри</td>
                        <td>Н/Д</td>
                    </tr>
                    <tr>
                        <td>Текст снаружи помещения</td>
                        <td>Н/Д</td>
                    </tr>
                    <tr>
                        <td>Уверенность снаружи</td>
                        <td>Н/Д</td>
                    </tr>
                </table>
            </div>
            '''
    
        spoofing_section = ""
        if report_data['has_spoofing_data']:
            spoofing_results = report_data['spoofing_results']
            spoofing_section = f'''
            <div class="info-card">
                <h2>🛡️ РЕЗУЛЬТАТЫ ПРОВЕРКИ СПУФИНГА</h2>
                <table>
                    <tr>
                        <th>Параметр</th>
                        <th>Значение</th>
                    </tr>
                    <tr>
                        <td>Совпадение с эталоном</td>
                        <td>{spoofing_results.get('match_score', 'Н/Д')}</td>
                    </tr>
                    <tr>
                        <td>Порог прохождения</td>
                        <td>{spoofing_results.get('threshold', 'Н/Д')}</td>
                    </tr>
                    <tr>
                        <td>Уверенность распознавания</td>
                        <td>{spoofing_results.get('confidence', 'Н/Д')}</td>
                    </tr>
                </table>
            </div>
            '''
    
        analysis_section = ""
        if report_data['has_analysis_data']:
            analysis_results = report_data['analysis_results']
            analysis_section = f'''
            <div class="info-card">
                <h2>📊 РЕЗУЛЬТАТЫ АНАЛИЗА ЗВУКОИЗОЛЯЦИИ</h2>
                <table>
                    <tr>
                        <th>Параметр</th>
                        <th>Значение</th>
                    </tr>
                    <tr>
                        <td>Ослабление звука</td>
                        <td>{analysis_results.get('attenuation_db', 'Н/Д')} дБ</td>
                    </tr>
                    <tr>
                        <td>Эффективность изоляции</td>
                        <td>{analysis_results.get('isolation_efficiency', 'Н/Д')}</td>
                    </tr>
                    <tr>
                        <td>Всего слов в фразе</td>
                        <td>{analysis_results.get('total_words', 'Н/Д')}</td>
                    </tr>
                    <tr>
                        <td>Слов потеряно при изоляции</td>
                        <td>{analysis_results.get('lost_words', 'Н/Д')}</td>
                    </tr>
                </table>
            </div>
            '''
    
        # Полный HTML
        html_content = f'''<!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Отчет по тесту звукоизоляции - {test_name}</title>
        <style>
            /* Стили остаются без изменений */
            @media print {{
                @page {{
                    margin: 2cm;
                    size: A4;
                }}
                body {{
                    font-size: 12pt;
                }}
                .page-break {{
                    page-break-before: always;
                }}
                .no-print {{
                    display: none;
                }}
            }}
        
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
        
            body {{
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 210mm;
                margin: 0 auto;
                padding: 20mm;
                background-color: #f9f9f9;
            }}
        
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 3px solid #2c3e50;
            }}
        
            .header h1 {{
                color: #2c3e50;
                font-size: 24pt;
                margin-bottom: 10px;
            }}
        
            .header .subtitle {{
                color: #7f8c8d;
                font-size: 14pt;
            }}
        
            .info-card {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-left: 5px solid #3498db;
            }}
        
            .result-card {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-left: 5px solid #2ecc71;
            }}
        
            .verdict-card {{
                background: white;
                border-radius: 8px;
                padding: 30px;
                margin: 30px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                text-align: center;
                border: 2px solid #e74c3c;
            }}
        
            .verdict-card h2 {{
                color: #e74c3c;
                font-size: 20pt;
                margin-bottom: 15px;
            }}
        
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }}
        
            .metric-item {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                text-align: center;
                border: 1px solid #dee2e6;
            }}
        
            .metric-value {{
                font-size: 24pt;
                font-weight: bold;
                color: #2c3e50;
                margin: 10px 0;
            }}
        
            .metric-label {{
                color: #6c757d;
                font-size: 11pt;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
        
            h2 {{
                color: #2c3e50;
                margin: 25px 0 15px 0;
                padding-bottom: 10px;
                border-bottom: 2px solid #ecf0f1;
                font-size: 18pt;
            }}
        
            h3 {{
                color: #34495e;
                margin: 20px 0 10px 0;
                font-size: 14pt;
            }}
        
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                font-size: 11pt;
            }}
        
            table th {{
                background: #2c3e50;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: bold;
            }}
        
            table td {{
                padding: 12px;
                border-bottom: 1px solid #ddd;
            }}
        
            table tr:nth-child(even) {{
                background: #f8f9fa;
            }}
        
            .recommendations {{
                background: #fff3cd;
                border-left: 5px solid #ffc107;
                padding: 20px;
                margin: 20px 0;
                border-radius: 6px;
            }}
        
            .recommendations ul {{
                padding-left: 20px;
                margin: 10px 0;
            }}
        
            .recommendations li {{
                margin: 8px 0;
            }}
        
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #ecf0f1;
                text-align: center;
                color: #7f8c8d;
                font-size: 10pt;
            }}
        
            .print-button {{
                display: block;
                width: 200px;
                margin: 30px auto;
                padding: 12px 24px;
                background: #3498db;
                color: white;
                text-align: center;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                cursor: pointer;
                border: none;
                font-size: 12pt;
            }}
        
            .print-button:hover {{
                background: #2980b9;
            }}
        
            .badge {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 10pt;
                font-weight: bold;
                margin: 0 5px;
            }}
        
            .badge-success {{
                background: #d4edda;
                color: #155724;
            }}
        
            .badge-warning {{
                background: #fff3cd;
                color: #856404;
            }}
        
            .badge-danger {{
                background: #f8d7da;
                color: #721c24;
            }}
        
            .grade {{
                font-size: 32pt;
                font-weight: bold;
                color: #2c3e50;
                text-align: center;
                margin: 20px 0;
            }}
        
            .text-validation {{
                background: #e8f4fd;
                border-left: 5px solid #3498db;
                padding: 20px;
                margin: 20px 0;
                border-radius: 6px;
            }}
        
            .text-validation.success {{
                background: #d4edda;
                border-left: 5px solid #28a745;
            }}
        
            .text-validation.warning {{
                background: #fff3cd;
                border-left: 5px solid #ffc107;
            }}
        
            .text-validation.danger {{
                background: #f8d7da;
                border-left: 5px solid #dc3545;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 ОТЧЕТ ПО ТЕСТУ ЗВУКОИЗОЛЯЦИИ</h1>
            <div class="subtitle">Защита от спуфинг-атак - Sound Isolation Tester v3.14</div>
        </div>
    
        <div class="info-card">
            <h2>📋 ИНФОРМАЦИЯ О ТЕСТЕ</h2>
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-label">Название теста</div>
                    <div class="metric-value">{test_name}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Дата и время</div>
                    <div class="metric-value">{timestamp}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Длительность</div>
                    <div class="metric-value">{duration:.1f} сек</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Частота дискретизации</div>
                    <div class="metric-value">{sample_rate} Гц</div>
                </div>
            </div>
        </div>
    
        {speech_section}
        {spoofing_section}
        {analysis_section}
    
        <div class="info-card">
            <h2>🔧 ТЕХНИЧЕСКИЕ ДАННЫЕ</h2>
            <table>
                <tr>
                    <th>Параметр</th>
                    <th>Значение</th>
                </tr>
                <tr>
                    <td>Фраза для проверки</td>
                    <td>"{reference_text}"</td>
                </tr>
                <tr>
                    <td>Дата создания отчета</td>
                    <td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td>
                </tr>
                <tr>
                    <td>Версия приложения</td>
                    <td>Sound Isolation Tester v3.14</td>
                </tr>
            </table>
        </div>
    
        <div class="footer">
            <p>Отчет сгенерирован автоматически. Для печати нажмите Ctrl+P</p>
            <p>Все данные конфиденциальны и предназначены только для академического использования</p>
        </div>
    
        <button class="print-button no-print" onclick="window.print()">🖨️ Печать отчета</button>
    
        <script>
            window.onload = function() {{
                // Автоматическое открытие диалога печати (можно закомментировать если не нужно)
                // setTimeout(() => {{ window.print(); }}, 1000);
            }};
        </script>
    </body>
    </html>'''
    
        # Сохраняем HTML файл
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
        print(f"✅ HTML отчет сохранен: {filename}")
    
    
    def _create_text_report(self, metadata, analysis_data, filename):
        """Создать текстовый отчет"""
        report = "=" * 70 + "\n"
        report += "ОТЧЕТ О ТЕСТЕ ЗВУКОИЗОЛЯЦИИ (с защитой от спуфинг-атак)\n"
        report += "=" * 70 + "\n\n"
        
        report += f"Имя теста: {metadata.get('test_name', 'N/A')}\n"
        report += f"Дата и время: {metadata.get('timestamp', 'N/A')}\n"
        report += f"Частота дискретизации: {metadata.get('sample_rate', 'N/A')} Гц\n"
        report += f"Длительность: {metadata.get('duration', 0):.2f} сек\n"
        report += f"Фраза для проверки: {metadata.get('reference_text', 'Не задана')}\n\n"
        
        if analysis_data:
            results = analysis_data.get('results', {})
            overall = results.get('overall_assessment', {})
            text_validation = results.get('text_validation', {})
            
            report += "ПРОВЕРКА ЗАЩИТЫ ОТ СПУФИНГА:\n"
            report += "-" * 40 + "\n"
            if text_validation:
                if text_validation.get('valid', False):
                    report += "✅ Текст успешно проверен\n"
                else:
                    report += "❌ Текст НЕ соответствует!\n"
                    report += "   ВНИМАНИЕ: Возможна спуфинг-атака!\n"
                report += f"   Заданный текст: {text_validation.get('reference', 'N/A')}\n"
                report += f"   Распознанный текст: {text_validation.get('recognized', 'N/A')}\n"
                report += f"   Совпадение: {text_validation.get('match_score', 0)*100:.1f}%\n"
            else:
                report += "⚠️ Проверка текста не выполнена\n"
            report += "\n"
            
            report += "РЕЗУЛЬТАТЫ АНАЛИЗА:\n"
            report += "-" * 40 + "\n"
            report += f"Вердикт: {overall.get('verdict', 'Н/Д')}\n"
            report += f"Оценка: {overall.get('grade', 'Н/Д')}\n"
            report += f"Сводка: {overall.get('summary', 'Н/Д')}\n\n"
            
            # Рекомендации
            recommendations = overall.get('recommendations', [])
            if recommendations:
                report += "РЕКОМЕНДАЦИИ:\n"
                report += "-" * 40 + "\n"
                for i, rec in enumerate(recommendations, 1):
                    report += f"{i}. {rec}\n"
                report += "\n"
        
        report += "ТЕХНИЧЕСКИЕ ДАННЫЕ:\n"
        report += "-" * 40 + "\n"
        if 'files' in metadata:
            files = metadata['files']
            for channel, data in files.items():
                report += f"{channel.upper()}:\n"
                report += f"  Файл: {data.get('filename', 'N/A')}\n"
                report += f"  Размер: {data.get('filesize_mb', 0):.2f} МБ\n"
                report += f"  Сэмплов: {data.get('samples', 0):,}\n"
        
        report += "\n" + "=" * 70 + "\n"
        report += "СИСТЕМНАЯ ИНФОРМАЦИЯ:\n"
        report += "-" * 40 + "\n"
        report += f"Дата создания отчета: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Версия приложения: Sound Isolation Tester v3.14 (защита от спуфинг-атак)\n"
        report += f"Операционная система: {sys.platform}\n"
        report += f"Версия Python: {sys.version.split()[0]}\n"
        
        report += "\n" + "=" * 70 + "\n"
        report += "ПРИМЕЧАНИЕ:\n"
        report += "-" * 40 + "\n"
        report += "Для защиты от спуфинг-атек:\n"
        report += "• Всегда используйте уникальные фразы для каждого теста\n"
        report += "• Произносите фразу громко и четко\n"
        report += "• Проверяйте соответствие распознанного текста заданному\n"
        report += "• Анализируйте технические показатели на наличие аномалий\n"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
    
    def play_recording(self):
        """Воспроизвести выбранную запись"""
        try:
            selection = self.recordings_tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите запись для воспроизведения")
                return
            
            # Получаем данные выбранной записи
            item = self.recordings_tree.item(selection[0])
            test_name = item['values'][0]
            
            # Находим файлы записи
            outside_path = os.path.join(self.recordings_folder, f"{test_name}_outside.wav")
            inside_path = os.path.join(self.recordings_folder, f"{test_name}_inside.wav")
            
            if not os.path.exists(outside_path) or not os.path.exists(inside_path):
                messagebox.showerror("Ошибка", "Файлы записи не найдены")
                return
            
            # Запрашиваем какой канал воспроизводить
            channel = messagebox.askquestion(
                "Выбор канала",
                "Какой канал воспроизвести?",
                detail="'Да' - Снаружи\n'Нет' - Внутри\n'Отмена' - Оба",
                type=messagebox.YESNOCANCEL
            )
            
            if channel == messagebox.YES:
                file_to_play = outside_path
                channel_name = "СНАРУЖИ"
            elif channel == messagebox.NO:
                file_to_play = inside_path
                channel_name = "ВНУТРИ"
            else:
                # Воспроизводим оба
                file_to_play = None
            
            if file_to_play:
                # Воспроизводим один файл
                self._play_audio_file(file_to_play, channel_name)
            else:
                # Воспроизводим оба файла (последовательно)
                self._play_audio_file(outside_path, "СНАРУЖИ")
                time.sleep(1)
                self._play_audio_file(inside_path, "ВНУТРИ")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка воспроизведения: {e}")
    
    def _play_audio_file(self, filepath, channel_name):
        """Воспроизвести аудиофайл"""
        try:
            # Проверяем платформу
            if sys.platform == "win32":
                # Windows
                os.startfile(filepath)
            elif sys.platform == "darwin":
                # macOS
                subprocess.call(["open", filepath])
            else:
                # Linux
                subprocess.call(["xdg-open", filepath])
            
            self.status_var.set(f"🎵 Воспроизведение: {channel_name}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось воспроизвести файл: {e}")
    
    def select_engine(self):
        """Выбрать движок распознавания"""
        try:
            engine_name = self.engine_combo.get()
            
            if not engine_name or "⚠️" in engine_name:
                messagebox.showwarning("Предупреждение", 
                    "Нет доступных моделей!\n"
                    "Загрузите модели через кнопку 'Загрузить модели'")
                return
            
            if self.recognizer:
                # Преобразуем строку в Enum
                try:
                    engine = RecognitionEngine(engine_name)
                except ValueError:
                    # Если движок не в Enum, пробуем создать из строки
                    if engine_name.startswith("whisper-"):
                        engine = RecognitionEngine(engine_name)
                    elif engine_name.startswith("vosk-"):
                        engine = RecognitionEngine(engine_name)
                    else:
                        raise ValueError(f"Неизвестный движок: {engine_name}")
                
                # Устанавливаем движок
                success = self.recognizer.set_engine(engine)
                
                if success:
                    self.current_engine = engine
                    self.engine_status_var.set(f"✅ Выбран: {engine_name}")
                    self.status_var.set(f"Движок установлен: {engine_name}")
                    
                    # Обновляем анализатор
                    self.analyzer.set_recognition_engine(engine_name)
                else:
                    self.engine_status_var.set(f"❌ Ошибка загрузки: {engine_name}")
                    messagebox.showerror("Ошибка", f"Не удалось загрузить движок: {engine_name}")
            else:
                messagebox.showwarning("Предупреждение", 
                    "Модуль распознавания недоступен.\n"
                    "Установите зависимости: pip install vosk whisper")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка выбора движка: {e}")
    
    def download_models(self):
        """Загрузить модели распознавания"""
        try:
            # Показываем информационное окно
            info_window = tk.Toplevel(self.root)
            info_window.title("Загрузка моделей")
            info_window.geometry("500x300")
            info_window.transient(self.root)
            info_window.grab_set()
            
            # Центрируем
            info_window.update_idletasks()
            x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
            y = (self.root.winfo_screenheight() // 2) - (300 // 2)
            info_window.geometry(f'500x300+{x}+{y}')
            
            # Контент
            ttk.Label(info_window, text="📥 ЗАГРУЗКА МОДЕЛЕЙ", 
                     font=('Arial', 12, 'bold')).pack(pady=10)
            
            info_text = """Для загрузки моделей выполните:

1. Запустите скрипт download_models.py:
   • Откройте командную строку/терминал
   • Перейдите в папку с проектом
   • Выполните: python download_models.py

2. Или выполните вручную:
   • pip install vosk whisper
   • Загрузите модели Whisper:
     https://github.com/openai/whisper
   • Загрузите модели Vosk:
     https://alphacephei.com/vosk/models"""
            
            text_widget = scrolledtext.ScrolledText(info_window, wrap=tk.WORD, 
                                                   width=60, height=12)
            text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            text_widget.insert(tk.END, info_text)
            text_widget.config(state=tk.DISABLED)
            
            def open_download_script():
                try:
                    if os.path.exists("download_models.py"):
                        subprocess.Popen([sys.executable, "download_models.py"])
                    else:
                        messagebox.showwarning("Предупреждение", 
                            "Файл download_models.py не найден\n"
                            "Скачайте его из архива проекта")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось запустить скрипт: {e}")
            
            # Кнопки
            btn_frame = ttk.Frame(info_window)
            btn_frame.pack(pady=10)
            
            ttk.Button(btn_frame, text="🚀 Запустить скрипт", 
                      command=open_download_script).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="❌ Закрыть", 
                      command=info_window.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {e}")
    
    def browse_test_audio(self):
        """Выбрать тестовый аудиофайл"""
        filename = filedialog.askopenfilename(
            title="Выберите аудиофайл",
            filetypes=[("WAV файлы", "*.wav"), ("Все файлы", "*.*")]
        )
        
        if filename:
            self.test_audio_path.set(filename)
    
    def test_recognition(self):
        """Тест распознавания речи"""
        try:
            audio_path = self.test_audio_path.get()
            
            if not audio_path or not os.path.exists(audio_path):
                messagebox.showwarning("Предупреждение", "Выберите аудиофайл для теста")
                return
            
            if not self.recognizer or not self.current_engine:
                messagebox.showwarning("Предупреждение", 
                    "Сначала выберите движок распознавания")
                return
            
            # Выполняем распознавание
            self.status_var.set("🧪 Тест распознавания...")
            
            result = self.recognizer.transcribe(audio_path)
            
            # Отображаем результаты
            self.test_result_text.delete(1.0, tk.END)
            
            if result and result.text:
                result_text = f"✅ РАСПОЗНАНО УСПЕШНО\n\n"
                result_text += f"Движок: {result.engine}\n"
                result_text += f"Текст: {result.text}\n"
                result_text += f"Уверенность: {result.confidence:.2f}\n"
                result_text += f"Время обработки: {result.processing_time:.1f} сек\n"
                
                if result.words:
                    result_text += f"\nСлова: {len(result.words)}\n"
                    for i, word in enumerate(result.words[:10]):  # Показываем первые 10 слов
                        result_text += f"  {i+1}. {word.get('word', '')}\n"
                    if len(result.words) > 10:
                        result_text += f"  ... и еще {len(result.words) - 10} слов\n"
            else:
                result_text = "❌ РАСПОЗНАНИЕ НЕ УДАЛОСЬ\n\n"
                result_text += "Возможные причины:\n"
                result_text += "1. Аудиофайл поврежден\n"
                result_text += "2. В файле нет речи\n"
                result_text += "3. Модель не загружена корректно\n"
                result_text += "4. Неправильный формат файла\n"
            
            self.test_result_text.insert(tk.END, result_text)
            self.status_var.set("✅ Тест завершен")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка теста распознавания: {e}")
    
    def load_config(self):
        """Загрузить конфигурацию"""
        try:
            config_file = "config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Восстанавливаем настройки
                if 'last_engine' in config:
                    # Пытаемся установить последний движок
                    pass
                
                print("✅ Конфигурация загружена")
                
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфигурации: {e}")
    
    def save_config(self):
        """Сохранить конфигурацию"""
        try:
            config = {
                'last_engine': self.current_engine.value if self.current_engine else None,
                'save_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'app_version': '3.14'
            }
            
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print("✅ Конфигурация сохранена")
            
        except Exception as e:
            print(f"⚠️ Ошибка сохранения конфигурации: {e}")

    def setup_quick_generation_tab(self, parent):
        """Быстрая генерация датасета"""
    
        # Описание
        desc_text = """Быстро создайте тестовый датасет с предустановленными условиями.
        Идеально для первичного тестирования и демонстрации."""
    
        ttk.Label(parent, text=desc_text, wraplength=700, justify=tk.LEFT).pack(pady=10)
    
        # Предустановленные сценарии
        scenarios_frame = ttk.LabelFrame(parent, text="📋 ПРЕДУСТАНОВЛЕННЫЕ СЦЕНАРИИ", padding="10")
        scenarios_frame.pack(fill=tk.X, pady=10)
    
        self.scenario_vars = []
        scenarios = [
            ("Тихая комната", "Низкий шум, хорошая акустика", True),
            ("Офисное помещение", "Умеренный шум, разговоры на фоне", False),
            ("Коридор с эхом", "Средний шум, реверберация", False),
        ]
    
        for i, (name, desc, default) in enumerate(scenarios):
            frame = ttk.Frame(scenarios_frame)
            frame.pack(fill=tk.X, pady=2)
        
            var = tk.BooleanVar(value=default)
            ttk.Checkbutton(frame, text=name, variable=var).pack(side=tk.LEFT, padx=5)
            ttk.Label(frame, text=desc, foreground="gray").pack(side=tk.LEFT, padx=20)
            self.scenario_vars.append((name, var))
    
        # Параметры генерации
        params_frame = ttk.LabelFrame(parent, text="⚙️ ПАРАМЕТРЫ ГЕНЕРАЦИИ", padding="10")
        params_frame.pack(fill=tk.X, pady=10)
    
        # Количество сэмплов
        ttk.Label(params_frame, text="Сэмплов на сценарий:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.samples_per_scenario = tk.IntVar(value=10)
        ttk.Spinbox(params_frame, from_=5, to=100, textvariable=self.samples_per_scenario, width=10).grid(row=0, column=1, padx=10, pady=5)
    
        # Имя датасета
        ttk.Label(params_frame, text="Имя датасета:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.dataset_name_var = tk.StringVar(value=f"dataset_{datetime.now().strftime('%Y%m%d_%H%M')}")
        ttk.Entry(params_frame, textvariable=self.dataset_name_var, width=30).grid(row=1, column=1, padx=10, pady=5)
    
        params_frame.columnconfigure(1, weight=1)
    
        # Кнопка генерации
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=20)
    
        ttk.Button(btn_frame, text="🚀 СГЕНЕРИРОВАТЬ ДАТАСЕТ", 
                command=self.generate_quick_dataset, width=25,
                style="Green.TButton").pack(pady=10)
    
        # Прогресс
        self.progress_var = tk.StringVar(value="Готов к генерации")
        ttk.Label(parent, textvariable=self.progress_var, foreground="blue").pack()

    def setup_diploma_dataset_tab(self, parent):
        """Предустановленный датасет для тестирования"""
    
        # Описание
        desc_text = """🎓 Специально подготовленный датасет для тестирования.
    Включает 2 различных акустических условий с 10 сэмплами каждое.
    Идеально для сравнительного анализа и исследования."""
    
        ttk.Label(parent, text=desc_text, wraplength=700, justify=tk.LEFT).pack(pady=10)
    
        # Условия тестого датасета
        conditions_frame = ttk.LabelFrame(parent, text="📊 УСЛОВИЯ В ДАТАСЕТЕ", padding="10")
        conditions_frame.pack(fill=tk.X, pady=10)
    
        conditions = [
            ("1. Ideal Conditions", "Идеальные условия (эталон)", "Низкий шум, хорошая акустика"),
            ("2. Quiet Office", "Тихий офис", "Умеренный шум, фоновая речь"),
        ]
    
        for name, desc, params in conditions:
            frame = ttk.Frame(conditions_frame)
            frame.pack(fill=tk.X, pady=3)
        
            ttk.Label(frame, text=name, font=('Arial', 10, 'bold'), width=20).pack(side=tk.LEFT, padx=5)
            ttk.Label(frame, text=desc, width=25).pack(side=tk.LEFT, padx=5)
            ttk.Label(frame, text=params, foreground="green").pack(side=tk.LEFT, padx=5)
    
        # Статистика
        stats_frame = ttk.LabelFrame(parent, text="📈 СТАТИСТИКА ДАТАСЕТА", padding="10")
        stats_frame.pack(fill=tk.X, pady=10)
    
        stats = [
            ("Всего сэмплов:", "20 (2 условия × 10 сэмплов)"),
            ("Длительность:", "3-6 секунд каждый"),
            ("Частота дискретизации:", "16 кГц (стандарт для распознавания)"),
            ("Общий объем:", "≈ 10-20 МБ"),
            ("Форматы:", "WAV аудио + CSV (UTF-8) + JSON"),
            ("Кодировка CSV:", "UTF-8-BOM (открывается в Excel)")
        ]
    
        for label, value in stats:
            frame = ttk.Frame(stats_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=label, font=('Arial', 9, 'bold'), width=25).pack(side=tk.LEFT)
            ttk.Label(frame, text=value).pack(side=tk.LEFT)
    
        # Кнопка генерации
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=20)
    
        ttk.Button(btn_frame, text="СГЕНЕРИРОВАТЬ ТЕСТОВЫЙ ДАТАСЕТ", 
                command=self.generate_diploma_dataset, width=30,
                style="Green.TButton").pack()

    def generate_quick_dataset(self):
        """Быстрая генерация датасета"""
        try:
            # Собираем выбранные сценарии
            selected_scenarios = []
            for name, var in self.scenario_vars:
                if var.get():
                    selected_scenarios.append(name)
        
            if not selected_scenarios:
                messagebox.showwarning("Предупреждение", "Выберите хотя бы один сценарий")
                return
        
            # Параметры
            samples_per = self.samples_per_scenario.get()
            dataset_name = self.dataset_name_var.get()
        
            # Создаем условия на основе сценариев
            from dataset_generator import AcousticCondition
        
            conditions = []
            scenario_params = {
                "Тихая комната": {
                    'name': 'quiet_room',
                    'noise': 0.02, 'reverb': 0.3, 'types': ['white'], 
                    'room': (4, 5, 3), 'absorption': 0.8, 'distance': 1.0
                },
                "Офисное помещение": {
                    'name': 'office',
                    'noise': 0.08, 'reverb': 0.5, 'types': ['white', 'office'], 
                    'room': (6, 8, 3), 'absorption': 0.6, 'distance': 1.5
                },
                "Коридор с эхом": {
                    'name': 'corridor',
                    'noise': 0.12, 'reverb': 1.2, 'types': ['pink'], 
                    'room': (15, 3, 3), 'absorption': 0.3, 'distance': 2.0
                },
            }
        
            for scenario in selected_scenarios:
                if scenario in scenario_params:
                    params = scenario_params[scenario]
                    condition = AcousticCondition(
                        name=params['name'],  # Английское название
                        description=f"Сценарий: {scenario}",
                        background_noise_level=params['noise'],
                        reverberation_time=params['reverb'],
                        noise_types=params['types'],
                        speech_level_variation=0.2,
                        speech_speed_variation=0.1,
                        room_size=params['room'],
                        absorption_coefficient=params['absorption'],
                        distance_to_microphone=params['distance']
                    )
                    conditions.append(condition)
        
            # Создаем генератор
            from dataset_generator import TestDatasetGenerator
            generator = TestDatasetGenerator(output_dir=dataset_name)
        
            # Запускаем в отдельном потоке с прогрессом
            self.progress_var.set("🔄 Начинаю генерацию датасета...")
        
            threading.Thread(
                target=self._generate_dataset_thread,
                args=(generator, conditions, samples_per, "быстрый")
            ).start()
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка генерации: {e}")
            import traceback
            traceback.print_exc()
            self.progress_var.set("❌ Ошибка генерации")

    def generate_diploma_dataset(self):
        """Генерация тестого датасета"""
        try:
            confirm = messagebox.askyesno(
                "Подтверждение",
                "Сгенерировать тестовый датасет?\n\n"
                "• 2 различных акустических условий\n"
                "• 10 сэмплов на каждое условие\n"
                "• Итого 20 аудиофайлов\n\n"
                "Это может занять несколько секунд."
            )
        
            if not confirm:
                return
        
            self.status_var.set("Генерация тестового датасета...")
        
            # Запускаем в отдельном потоке
            threading.Thread(
                target=self._generate_diploma_dataset_thread
            ).start()
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка генерации: {e}")

    def _generate_dataset_thread(self, generator, conditions, samples_per, dataset_type):
        """Поток генерации датасета"""
        try:
            # Генерируем датасет
            dataset_info = generator.generate_dataset(
                conditions=conditions,
                num_samples_per_condition=samples_per,
                sample_rate=16000,
                duration_range=(3.0, 6.0)
            )
        
            # Обновляем интерфейс
            self.root.after(0, lambda: self._dataset_generation_complete(
                dataset_info, dataset_type
            ))
        
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Ошибка",
                f"Ошибка генерации датасета: {e}"
            ))
            self.root.after(0, lambda: self.progress_var.set("❌ Ошибка генерации"))

    def _generate_diploma_dataset_thread(self):
        """Поток генерации тестового датасета"""
        try:
            from dataset_generator import create_diploma_dataset
        
            # Генерируем датасет
            dataset_info = create_diploma_dataset()
        
            self.root.after(0, lambda: self._dataset_generation_complete(
                dataset_info, "тестовый"
            ))
        
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "Ошибка",
                f"Ошибка генерации тестового датасета: {e}"
            ))

    def _dataset_generation_complete(self, dataset_info, dataset_type):
        """Завершение генерации датасета"""
        try:
            total_samples = len(dataset_info['samples'])
            conditions = len(dataset_info['conditions'])
        
            messagebox.showinfo(
                "✅ Успех",
                f"{dataset_type.capitalize()} датасет успешно сгенерирован!\n\n"
                f"📊 Статистика:\n"
                f"• Условий: {conditions}\n"
                f"• Сэмплов: {total_samples}\n"
                f"• Папка: {dataset_info.get('output_dir', 'test_datasets')}/\n\n"
                f"📁 Созданные файлы:\n"
                f"• dataset_metadata.json\n"
                f"• dataset_samples.csv\n"
                f"• Папки с аудиофайлами"
            )
        
            self.status_var.set(f"✅ Датасет создан: {total_samples} сэмплов")
            self.progress_var.set(f"✅ Датасет создан")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка завершения: {e}")

    def _calculate_text_match(self, recognized, reference):
        """Вычисление процента совпадения текста для проверки спуфинга"""
        try:
            import difflib
            import re
        
            if not recognized or not reference:
                return 0.0
        
            # Очищаем текст
            def clean_text(text):
                text = str(text).lower()
                text = text.replace('ё', 'е')
                # Удаляем знаки препинания и лишние пробелы
                text = re.sub(r'[^\w\s]', '', text)
                text = ' '.join(text.split())
                return text
        
            clean_rec = clean_text(recognized)
            clean_ref = clean_text(reference)
        
            # Используем SequenceMatcher для сравнения
            matcher = difflib.SequenceMatcher(None, clean_rec, clean_ref)
            similarity = matcher.ratio()
        
            # Дополнительная проверка по ключевым словам
            ref_words = set(clean_ref.split())
            rec_words = set(clean_rec.split())
        
            if ref_words:
                word_match = len(ref_words.intersection(rec_words)) / len(ref_words)
                # Комбинируем оба метода
                final_score = (similarity * 0.7) + (word_match * 0.3)
            else:
                final_score = similarity
        
            return min(max(final_score, 0.0), 1.0)
        
        except Exception as e:
            print(f"Ошибка сравнения текстов: {e}")
            return 0.0

    def _show_detailed_spoofing_result(self, spoofing_result, test_name):
        """Показать детальные результаты проверки спуфинга в отдельном окне"""
        try:
            result_window = tk.Toplevel(self.root)
            result_window.title(f"Результат проверки спуфинга: {test_name}")
            result_window.geometry("600x500")
        
            # Центрируем
            result_window.update_idletasks()
            x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
            y = (self.root.winfo_screenheight() // 2) - (500 // 2)
            result_window.geometry(f'600x500+{x}+{y}')
        
            # Заголовок
            if spoofing_result.get('passed', False):
                title_text = "✅ СПУФИНГ-АТАКА НЕ ОБНАРУЖЕНА"
                title_color = "green"
            else:
                title_text = "⚠️ ВОЗМОЖНА СПУФИНГ-АТАКА"
                title_color = "red"
            
            ttk.Label(result_window, text=title_text, 
                     font=('Arial', 14, 'bold'), foreground=title_color).pack(pady=10)
        
            # Информация о тесте
            info_frame = ttk.LabelFrame(result_window, text="📋 ИНФОРМАЦИЯ", padding="10")
            info_frame.pack(fill=tk.X, padx=10, pady=5)
        
            ttk.Label(info_frame, text=f"Тест: {test_name}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Движок распознавания: {spoofing_result.get('engine', 'N/A')}").pack(anchor=tk.W)
        
            # Результат проверки
            result_frame = ttk.LabelFrame(result_window, text="📊 РЕЗУЛЬТАТ ПРОВЕРКИ", padding="10")
            result_frame.pack(fill=tk.X, padx=10, pady=5)
        
            match_percent = spoofing_result.get('match_percent', 0)
            threshold = spoofing_result.get('threshold', 0.8) * 100
        
            # Прогресс бар для наглядности
            progress_frame = ttk.Frame(result_frame)
            progress_frame.pack(fill=tk.X, pady=5)
        
            ttk.Label(progress_frame, text=f"Совпадение: {match_percent:.1f}%").pack(side=tk.LEFT)
            ttk.Label(progress_frame, text=f"Порог: {threshold:.0f}%", 
                     foreground="gray").pack(side=tk.RIGHT)
        
            # Сам прогресс бар
            progress_bar = ttk.Progressbar(result_frame, length=500, mode='determinate')
            progress_bar.pack(fill=tk.X, pady=5)
            progress_bar['value'] = min(match_percent, 100)
        
            # Цвет прогресс бара
            if match_percent >= 80:
                style_name = "green.Horizontal.TProgressbar"
            elif match_percent >= 60:
                style_name = "yellow.Horizontal.TProgressbar"
            else:
                style_name = "red.Horizontal.TProgressbar"
        
            # Создаем стили для цветных прогресс баров
            style = ttk.Style()
            style.configure("green.Horizontal.TProgressbar", 
                           background='green', troughcolor='lightgray')
            style.configure("yellow.Horizontal.TProgressbar", 
                           background='orange', troughcolor='lightgray')
            style.configure("red.Horizontal.TProgressbar", 
                           background='red', troughcolor='lightgray')
        
            progress_bar.configure(style=style_name)
        
            # Дополнительные метрики
            metrics_frame = ttk.Frame(result_frame)
            metrics_frame.pack(fill=tk.X, pady=10)
        
            ttk.Label(metrics_frame, text=f"Уверенность распознавания: {spoofing_result.get('confidence', 0)*100:.1f}%").pack(anchor=tk.W)
        
            # Фразы
            phrases_frame = ttk.LabelFrame(result_window, text="📝 СРАВНЕНИЕ ФРАЗ", padding="10")
            phrases_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
            # Эталонная фраза
            ttk.Label(phrases_frame, text="Эталонная фраза:", 
                     font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
            ref_frame = ttk.Frame(phrases_frame)
            ref_frame.pack(fill=tk.X, pady=(0, 10))
        
            ref_text = scrolledtext.ScrolledText(ref_frame, height=2, wrap=tk.WORD)
            ref_text.pack(fill=tk.X)
            ref_text.insert(tk.END, spoofing_result.get('reference_text', ''))
            ref_text.config(state=tk.DISABLED)
        
            # Распознанная фраза
            ttk.Label(phrases_frame, text="Распознанная фраза:", 
                     font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
            rec_frame = ttk.Frame(phrases_frame)
            rec_frame.pack(fill=tk.BOTH, expand=True)
        
            rec_text = scrolledtext.ScrolledText(rec_frame, height=3, wrap=tk.WORD)
            rec_text.pack(fill=tk.BOTH, expand=True)
            rec_text.insert(tk.END, spoofing_result.get('recognized_text', ''))
            rec_text.config(state=tk.DISABLED)
        
            # Интерпретация
            interpretation_frame = ttk.LabelFrame(result_window, text="💡 ИНТЕРПРЕТАЦИЯ", padding="10")
            interpretation_frame.pack(fill=tk.X, padx=10, pady=5)
        
            if spoofing_result.get('passed', False):
                interpretation = "✅ Речь соответствует эталонной фразе.\n" \
                               "Спуфинг-атака маловероятна."
            else:
                if match_percent >= 60:
                    interpretation = "⚠️ Умеренное несоответствие.\n" \
                                   "Возможны ошибки распознавания или плохое качество записи."
                else:
                    interpretation = "❌ Высокое несоответствие.\n" \
                                   "Возможна спуфинг-атака или речь не соответствует фразе."
        
            ttk.Label(interpretation_frame, text=interpretation, 
                     justify=tk.LEFT).pack(anchor=tk.W)
        
            # Рекомендации
            if not spoofing_result.get('passed', False):
                rec_frame = ttk.LabelFrame(result_window, text="🔧 РЕКОМЕНДАЦИИ", padding="10")
                rec_frame.pack(fill=tk.X, padx=10, pady=5)
            
                recommendations = []
                if match_percent >= 60:
                    recommendations = [
                        "• Повторите запись с более четким произношением",
                        "• Увеличьте громкость речи",
                        "• Уменьшите фоновый шум",
                        "• Используйте более простую фразу"
                    ]
                else:
                    recommendations = [
                        "• Проверьте источник звука (возможна записанная речь)",
                        "• Убедитесь, что используется живая речь",
                        "• Повторите тест с новой уникальной фразой",
                        "• Проверьте микрофон и настройки записи"
                    ]
            
                for rec in recommendations:
                    ttk.Label(rec_frame, text=rec, justify=tk.LEFT).pack(anchor=tk.W)
        
            # Кнопки
            btn_frame = ttk.Frame(result_window)
            btn_frame.pack(pady=10)
        
            def save_result():
                filename = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON файлы", "*.json"), ("Текстовые файлы", "*.txt")],
                    initialfile=f"{test_name}_spoofing_result.json"
                )
            
                if filename:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(spoofing_result, f, ensure_ascii=False, indent=2)
                    messagebox.showinfo("Успех", f"Результат сохранен в {filename}")
        
            ttk.Button(btn_frame, text="💾 Сохранить результат", 
                      command=save_result).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="❌ Закрыть", 
                      command=result_window.destroy).pack(side=tk.LEFT, padx=5)
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка отображения результатов спуфинга: {e}")

    def _parse_results_to_report_data(self, result_text, test_name):
        """Преобразовать текст результатов в структурированные данные для отчета"""
        report_data = {
            'test_name': test_name,
            'has_speech_data': False,
            'has_spoofing_data': False,
            'speech_results': {},
            'spoofing_results': {},
            'analysis_results': {},
            'parsed_sections': []
        }
        
        try:
            lines = result_text.split('\n')
            
            # Ищем и извлекаем разные типы данных
            for i, line in enumerate(lines):
                # 1. Распознанные тексты
                if 'ВНУТРИ:' in line and i+1 < len(lines):
                    inside_text = lines[i+1].strip().strip('"')
                    if inside_text and 'Не распознано' not in inside_text:
                        report_data['has_speech_data'] = True
                        report_data['speech_results']['inside_text'] = inside_text
                
                elif 'СНАРУЖИ' in line and i+1 < len(lines):
                    outside_text = lines[i+1].strip().strip('"')
                    if outside_text:
                        report_data['has_speech_data'] = True
                        report_data['speech_results']['outside_text'] = outside_text
                
                # 2. Уверенность распознавания
                elif 'Уверенность:' in line:
                    confidence = line.split(':')[1].strip()
                    if 'ВНУТРИ' in lines[i-1]:
                        report_data['speech_results']['inside_confidence'] = confidence
                    elif 'СНАРУЖИ' in lines[i-1]:
                        report_data['speech_results']['outside_confidence'] = confidence
                
                # 3. Совпадение с эталоном (для спуфинга)
                elif 'Совпадение с эталоном:' in line:
                    report_data['has_spoofing_data'] = True
                    report_data['spoofing_results']['match_percent'] = line.split(':')[1].strip()
                
                # 4. Ослабление звука (для звукоизоляции)
                elif 'Ослабление звука:' in line:
                    report_data['analysis_results']['attenuation_db'] = line.split(':')[1].strip()
                
                # 5. Эффективность изоляции
                elif 'Эффективность изоляции:' in line:
                    report_data['analysis_results']['isolation_efficiency'] = line.split(':')[1].strip()
            
            # Записываем, какие разделы были найдены
            if report_data['has_speech_data']:
                report_data['parsed_sections'].append('speech')
            if report_data['has_spoofing_data']:
                report_data['parsed_sections'].append('spoofing')
            if report_data['analysis_results']:
                report_data['parsed_sections'].append('analysis')
                
        except Exception as e:
            print(f"Ошибка парсинга результатов: {e}")
        
        return report_data

    def _show_format_selection_dialog(self, test_name, report_data):
        """Показать диалог выбора формата отчета"""
        format_window = tk.Toplevel(self.root)
        format_window.title("Выбор формата отчета")
        format_window.geometry("500x400")  # Увеличил высоту
        format_window.transient(self.root)
        format_window.grab_set()
    
        # Центрируем окно
        format_window.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        format_window.geometry(f'500x400+{x}+{y}')
    
        # Заголовок
        ttk.Label(format_window, text="📄 ВЫБЕРИТЕ ФОРМАТ ОТЧЕТА", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
    
        # Информация о доступных данных
        info_frame = ttk.LabelFrame(format_window, text="📊 ДОСТУПНЫЕ ДАННЫЕ", padding="10")
        info_frame.pack(fill=tk.X, padx=20, pady=10)
    
        info_text = f"Тест: {test_name}\n\n"
    
        if report_data['has_speech_data']:
            info_text += "✅ Данные распознавания речи\n"
            inside_text = report_data['speech_results'].get('inside_text', '')
            if inside_text:
                if len(inside_text) > 40:
                    info_text += f"   • Внутри: \"{inside_text[:40]}...\"\n"
                else:
                    info_text += f"   • Внутри: \"{inside_text}\"\n"
        
            outside_text = report_data['speech_results'].get('outside_text', '')
            if outside_text:
                if len(outside_text) > 40:
                    info_text += f"   • Снаружи: \"{outside_text[:40]}...\"\n"
                else:
                    info_text += f"   • Снаружи: \"{outside_text}\"\n"
    
        if report_data['has_spoofing_data']:
            info_text += "✅ Данные проверки спуфинга\n"
            if 'match_score' in report_data['spoofing_results']:
                info_text += f"   • Совпадение: {report_data['spoofing_results']['match_score']}\n"
    
        if report_data['has_analysis_data']:
            info_text += "✅ Данные анализа звукоизоляции\n"
            if 'attenuation_db' in report_data['analysis_results']:
                info_text += f"   • Ослабление: {report_data['analysis_results']['attenuation_db']} дБ\n"
            if 'isolation_efficiency' in report_data['analysis_results']:
                info_text += f"   • Эффективность: {report_data['analysis_results']['isolation_efficiency']}\n"
    
        if not any([report_data['has_speech_data'], 
                    report_data['has_spoofing_data'], 
                    report_data['has_analysis_data']]):
            info_text += "⚠️ Только базовые метаданные\n"
            info_text += "Сначала выполните 'Распознать речь'\n"
    
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack()
    
        # Выбор формата
        format_var = tk.StringVar(value="html")
    
        formats_frame = ttk.LabelFrame(format_window, text="📁 ФОРМАТЫ ОТЧЕТА", padding="10")
        formats_frame.pack(fill=tk.X, padx=20, pady=10)
    
        formats = [
            ("📄 HTML - красивый, для печати", "html"),
        ]
    
        for text, value in formats:
            ttk.Radiobutton(formats_frame, text=text, 
                           value=value, variable=format_var).pack(anchor=tk.W, pady=2)
    
        # Кнопка создания
        def create_report():
            if not any([report_data['has_speech_data'], 
                        report_data['has_spoofing_data'], 
                        report_data['has_analysis_data']]):
                messagebox.showwarning("Нет данных", 
                    "Сначала выполните анализ или распознавание речи")
                format_window.destroy()
                return
        
            format_window.destroy()
            self._create_report_file(test_name, format_var.get(), report_data)
    
        ttk.Button(format_window, text="📄 Создать отчет", 
                  command=create_report, width=20).pack(pady=15)
    
        ttk.Button(format_window, text="❌ Отмена", 
              command=format_window.destroy).pack()

    def _load_test_metadata(self, test_name):
        """Загрузить метаданные теста"""
        metadata_path = os.path.join(self.recordings_folder, f"{test_name}_metadata.json")
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Возвращаем базовые метаданные если файл не найден
        return {
            'test_name': test_name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'duration': 0,
            'sample_rate': 16000,
            'reference_text': 'Не задана'
        }

    def on_closing(self):
        """Обработчик закрытия окна"""
        try:
            # Останавливаем мониторинг
            self.monitoring_active = False
            
            # Сохраняем конфигурацию
            self.save_config()
            
            # Очищаем ресурсы
            if hasattr(self, 'audio_core'):
                self.audio_core.cleanup()
            
            # Закрываем приложение
            self.root.destroy()
            
        except Exception as e:
            print(f"Ошибка при закрытии: {e}")
            self.root.destroy()

    

def main():
    """Главная функция"""
    try:
        root = tk.Tk()
        app = AdvancedSoundTester(root)
        
        # Обработчик закрытия окна
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        root.mainloop()
        
    except Exception as e:
        import traceback
        error_msg = f"Критическая ошибка запуска:\n\n{str(e)}\n\n"
        error_msg += "Трассировка:\n"
        error_msg += traceback.format_exc()
        
        print(error_msg)
        
        # Пытаемся показать сообщение об ошибке
        try:
            tk.Tk().withdraw()  # Скрываем основное окно
            messagebox.showerror("Критическая ошибка", 
                f"Ошибка запуска:\n\n{str(e)[:200]}...\n\n"
                f"Проверьте:\n"
                f"1. Все файлы в одной папке\n"
                f"2. Установлены зависимости: pip install -r requirements.txt\n"
                f"3. Проверьте консоль для подробной информации")
        except:
            pass

if __name__ == "__main__":
    main()