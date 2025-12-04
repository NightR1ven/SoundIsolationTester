# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import sys
import os
import json
import webbrowser
from datetime import datetime
import csv  # Используем стандартный csv вместо pandas

# Пытаемся импортировать polars, если нет - используем альтернативы
try:
    import polars as pl
    POLARS_AVAILABLE = True
    print("✅ Polars загружен")
except ImportError:
    POLARS_AVAILABLE = False
    print("⚠️ Polars не установлен, используем CSV")
    
    # Создаем простые функции для работы с таблицами
    class SimpleTable:
        @staticmethod
        def read_csv(filepath):
            """Чтение CSV файла"""
            data = []
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            return data
        
        @staticmethod
        def write_csv(data, filepath, columns=None):
            """Запись в CSV"""
            if not data:
                return
            
            if columns is None:
                columns = list(data[0].keys())
            
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerows(data)
        
        @staticmethod
        def dataframe(data):
            """Имитация DataFrame"""
            return data

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.append(os.path.dirname(__file__))

try:
    from audio_core import AudioCore
    from ai_analyzer import EnhancedSoundIsolationAnalyzer  # Обновленный анализатор
    print("✅ Основные модули загружены")
except ImportError as e:
    print(f"⚠️ Ошибка импорта: {e}")
    # Создаем заглушки
    class AudioCore:
        def __init__(self):
            self.is_recording = False
        
        def get_audio_devices(self):
            return []
        
        def start_recording(self, *args, **kwargs):
            return False
        
        def stop_recording(self):
            return {}
        
        def get_recording_stats(self):
            return {}
    
    class EnhancedSoundIsolationAnalyzer:
        def analyze_with_audio_analysis(self, *args, **kwargs):
            return {'results': {'overall_assessment': {'verdict': 'УСТАНОВИТЕ ЗАВИСИМОСТИ'}}}

class AdvancedSoundTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Sound Isolation Tester v3.13")
        self.root.geometry("1100x750")
        
        self.center_window()
        
        # Инициализация
        try:
            self.audio_core = AudioCore()
            self.analyzer = EnhancedSoundIsolationAnalyzer()
            self.recordings_folder = "recordings"
            
            self.setup_styles()
            self.setup_ui()
            self.refresh_devices()
            self.refresh_recordings_list()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка инициализации:\n{e}")
            self.root.destroy()
    
    def setup_styles(self):
        """Настройка стилей"""
        style = ttk.Style()
        style.configure("Red.TButton", foreground="red", font=('Arial', 10, 'bold'))
        style.configure("Green.TButton", foreground="green", font=('Arial', 10, 'bold'))
    
    def center_window(self):
        """Центрирование окна"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Настройка интерфейса"""
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title = ttk.Label(main_frame, 
            text="🧪 ТЕСТЕР ЗВУКОИЗОЛЯЦИИ (Python 3.13 + Polars)",
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
        
        # Вкладка 3: Экспорт
        export_frame = ttk.Frame(notebook, padding="10")
        notebook.add(export_frame, text="📁 ЭКСПОРТ")
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
        
        # Блок 2: Параметры
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
        
        # Опции
        self.enable_analysis_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(params_frame, text="Автоматический анализ", variable=self.enable_analysis_var).grid(row=2, column=0, columnspan=2, pady=5, sticky=tk.W)
        
        # Блок 3: Управление
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
        
        # Индикаторы
        indicator_frame = ttk.Frame(parent)
        indicator_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(indicator_frame, text="Статус:").pack(side=tk.LEFT)
        self.record_status = ttk.Label(indicator_frame, text="Ожидание", foreground="blue")
        self.record_status.pack(side=tk.LEFT, padx=10)
        
        # Таймер
        self.timer_label = ttk.Label(indicator_frame, text="00:00", font=('Arial', 12, 'bold'))
        self.timer_label.pack(side=tk.RIGHT)
    
    def setup_analysis_tab(self, parent):
        """Вкладка анализа"""
        # Заголовок
        ttk.Label(parent, text="АНАЛИЗ ЗАПИСЕЙ", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Список записей
        list_frame = ttk.LabelFrame(parent, text="Доступные записи", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # TreeView
        columns = ("name", "date", "duration", "size", "status")
        self.recordings_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        # Заголовки
        self.recordings_tree.heading("name", text="Имя теста")
        self.recordings_tree.heading("date", text="Дата")
        self.recordings_tree.heading("duration", text="Длительность")
        self.recordings_tree.heading("size", text="Размер")
        self.recordings_tree.heading("status", text="Статус")
        
        # Ширина колонок
        self.recordings_tree.column("name", width=200)
        self.recordings_tree.column("date", width=150)
        self.recordings_tree.column("duration", width=100)
        self.recordings_tree.column("size", width=80)
        self.recordings_tree.column("status", width=100)
        
        # Прокрутка
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.recordings_tree.yview)
        self.recordings_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recordings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Действия
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=10)
        
        actions = [
            ("📊 Анализировать", self.analyze_selected),
            ("📋 Метаданные", self.show_metadata),
            ("🎵 Воспроизвести", self.play_recording),
            ("📈 График", self.plot_waveform),
            ("🧮 Статистика", self.calculate_stats)
        ]
        
        for text, command in actions:
            ttk.Button(action_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)
    
    def setup_export_tab(self, parent):
        """Вкладка экспорта"""
        # Экспорт в CSV
        csv_frame = ttk.LabelFrame(parent, text="Экспорт в CSV", padding="10")
        csv_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(csv_frame, text="Выберите данные для экспорта:").pack(anchor=tk.W)
        
        self.export_vars = {
            "recordings": tk.BooleanVar(value=True),
            "metadata": tk.BooleanVar(value=True),
            "analysis": tk.BooleanVar(value=True),
            "statistics": tk.BooleanVar(value=True)
        }
        
        for key, var in self.export_vars.items():
            ttk.Checkbutton(csv_frame, text=key.capitalize(), variable=var).pack(anchor=tk.W, pady=2)
        
        ttk.Button(csv_frame, text="📁 Экспортировать все", 
                  command=self.export_all_data).pack(pady=10)
        
        # Генерация отчета
        report_frame = ttk.LabelFrame(parent, text="Генерация отчета", padding="10")
        report_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(report_frame, text="📄 HTML отчет", 
                  command=self.generate_html_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(report_frame, text="📋 Текстовый отчет", 
                  command=self.generate_text_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(report_frame, text="📊 Сводная таблица", 
                  command=self.generate_summary_table).pack(side=tk.LEFT, padx=5)
        
        # Информация о системе
        info_frame = ttk.LabelFrame(parent, text="Информация о системе", padding="10")
        info_frame.pack(fill=tk.X, pady=10)
        
        self.system_info = tk.Text(info_frame, height=6, width=80)
        self.system_info.pack(fill=tk.X, pady=5)
        self.update_system_info()
    
    def update_system_info(self):
        """Обновление информации о системе"""
        info = f"Python {sys.version.split()[0]}\n"
        info += f"Polars доступен: {POLARS_AVAILABLE}\n"
        info += f"ОС: {sys.platform}\n"
        info += f"Папка записей: {os.path.abspath(self.recordings_folder)}\n"
        
        self.system_info.delete(1.0, tk.END)
        self.system_info.insert(1.0, info)
        self.system_info.config(state=tk.DISABLED)
    
    def refresh_devices(self):
        """Обновление списка устройств"""
        try:
            devices = self.audio_core.get_audio_devices()
            
            if POLARS_AVAILABLE:
                # Создаем таблицу устройств с Polars
                device_data = []
                for d in devices:
                    device_data.append({
                        'id': d['index'],
                        'name': d['name'][:50],  # Обрезаем длинные имена
                        'channels': d['channels']
                    })
                
                if device_data:
                    df = pl.DataFrame(device_data)
                    print("📊 Устройства (Polars):")
                    print(df)
            
            # Обновляем комбобоксы
            device_list = [f"{d['index']}: {d['name']}" for d in devices]
            
            self.outside_combo['values'] = device_list
            self.inside_combo['values'] = device_list
            
            if device_list:
                self.outside_combo.current(0)
                if len(device_list) > 1:
                    self.inside_combo.current(1)
            
            self.status_var.set(f"✅ Найдено устройств: {len(devices)}")
            
        except Exception as e:
            self.status_var.set(f"❌ Ошибка: {e}")
            messagebox.showerror("Ошибка", f"Не удалось получить устройства:\n{e}")
    
    def show_device_summary(self):
        """Показать сводку по устройствам"""
        try:
            devices = self.audio_core.get_audio_devices()
            
            if POLARS_AVAILABLE:
                # Анализ с Polars
                device_data = [{'id': d['index'], 'name': d['name'], 'channels': d['channels']} 
                             for d in devices]
                
                if device_data:
                    df = pl.DataFrame(device_data)
                    
                    summary = "📊 СВОДКА УСТРОЙСТВ:\n\n"
                    summary += f"Всего устройств: {df.height}\n"
                    summary += f"Стерео устройств: {df.filter(pl.col('channels') >= 2).height}\n"
                    
                    # Группировка по количеству каналов
                    channel_stats = df.group_by('channels').agg(pl.count().alias('count'))
                    for row in channel_stats.iter_rows():
                        summary += f"  {row[0]} каналов: {row[1]} устройств\n"
                    
                    messagebox.showinfo("Сводка устройств", summary)
                else:
                    messagebox.showinfo("Сводка", "Устройства не найдены")
            else:
                # Без Polars
                summary = f"Всего устройств: {len(devices)}\n\n"
                for d in devices:
                    summary += f"{d['index']}: {d['name']} ({d['channels']} каналов)\n"
                
                messagebox.showinfo("Сводка устройств", summary)
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка анализа:\n{e}")
    
    def test_devices(self):
        """Тестирование устройств"""
        devices = self.get_selected_devices()
        if not devices:
            return
        
        outside_idx, inside_idx = devices
        
        self.status_var.set("🔍 Тестирование устройств...")
        
        def test():
            try:
                success = self.audio_core.start_recording(outside_idx, inside_idx, duration=3)
                time.sleep(4)
                
                stats = self.audio_core.get_recording_stats()
                
                # Анализируем результаты
                if POLARS_AVAILABLE:
                    test_data = [{
                        'device': 'outside',
                        'samples': stats['outside_samples'],
                        'duration': stats['duration']
                    }, {
                        'device': 'inside', 
                        'samples': stats['inside_samples'],
                        'duration': stats['duration']
                    }]
                    
                    df = pl.DataFrame(test_data)
                    
                    result = "📊 РЕЗУЛЬТАТЫ ТЕСТА:\n\n"
                    result += f"Длительность: {stats['duration']:.2f} сек\n\n"
                    
                    for row in df.iter_rows(named=True):
                        status = "✅ OK" if row['samples'] > 0 else "❌ ОШИБКА"
                        result += f"{row['device'].upper()}: {row['samples']} сэмплов {status}\n"
                    
                else:
                    result = f"Длительность: {stats['duration']:.2f} сек\n\n"
                    result += f"СНАРУЖИ: {stats['outside_samples']} сэмплов\n"
                    result += f"ВНУТРИ: {stats['inside_samples']} сэмплов\n\n"
                    
                    if stats['outside_samples'] > 0 and stats['inside_samples'] > 0:
                        result += "✅ Оба устройства работают!"
                    else:
                        result += "⚠️ Проблемы с записью!"
                
                self.root.after(0, lambda: messagebox.showinfo("Тест устройств", result))
                self.root.after(0, lambda: self.status_var.set("✅ Тест завершен"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
                self.root.after(0, lambda: self.status_var.set("❌ Ошибка теста"))
        
        threading.Thread(target=test, daemon=True).start()
    
    def get_selected_devices(self):
        """Получение выбранных устройств"""
        try:
            outside_idx = int(self.outside_combo.get().split(':')[0])
            inside_idx = int(self.inside_combo.get().split(':')[0])
            return outside_idx, inside_idx
        except:
            messagebox.showerror("Ошибка", "Выберите оба микрофона!")
            return None, None
    
    def start_recording(self):
        """Начало записи"""
        devices = self.get_selected_devices()
        if not devices:
            return
        
        outside_idx, inside_idx = devices
        
        duration = int(self.duration_var.get())
        test_name = self.test_name_var.get()
        
        # Блокируем кнопки
        self.record_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.record_status.config(text="🔴 ЗАПИСЬ", foreground="red")
        
        # Запускаем таймер
        self.remaining_time = duration
        self.update_timer()
        
        def record():
            try:
                success = self.audio_core.start_recording(outside_idx, inside_idx, duration, test_name)
                if success:
                    self.status_var.set(f"🎤 Запись... {duration} сек")
                    
                    # Ждем завершения
                    time.sleep(duration + 1)
                    
                    # Автоматический анализ
                    if self.enable_analysis_var.get():
                        self.root.after(0, self.analyze_last_recording)
                    
                else:
                    self.root.after(0, lambda: self.status_var.set("❌ Ошибка записи"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            finally:
                self.root.after(0, self.stop_recording)
        
        threading.Thread(target=record, daemon=True).start()
    
    def update_timer(self):
        """Обновление таймера"""
        if hasattr(self, 'remaining_time') and self.remaining_time > 0:
            mins = self.remaining_time // 60
            secs = self.remaining_time % 60
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
            self.remaining_time -= 1
            self.root.after(1000, self.update_timer)
    
    def stop_recording(self):
        """Остановка записи"""
        saved_files = self.audio_core.stop_recording()
        
        # Сброс интерфейса
        self.record_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.record_status.config(text="✅ ГОТОВО", foreground="green")
        self.timer_label.config(text="00:00")
        
        if saved_files:
            self.status_var.set("✅ Запись сохранена")
            self.refresh_recordings_list()
        else:
            self.status_var.set("⚠️ Запись не сохранена")
    
    def refresh_recordings_list(self):
        """Обновление списка записей"""
        try:
            # Очищаем список
            for item in self.recordings_tree.get_children():
                self.recordings_tree.delete(item)
            
            # Сканируем папку
            if not os.path.exists(self.recordings_folder):
                os.makedirs(self.recordings_folder)
                return
            
            # Собираем данные о записях
            recordings_data = []
            
            for filename in os.listdir(self.recordings_folder):
                if filename.endswith('_metadata.json'):
                    test_name = filename.replace('_metadata.json', '')
                    metadata_path = os.path.join(self.recordings_folder, filename)
                    
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # Проверяем существование файлов
                        outside_file = os.path.join(self.recordings_folder, f"{test_name}_outside.wav")
                        inside_file = os.path.join(self.recordings_folder, f"{test_name}_inside.wav")
                        
                        files_exist = os.path.exists(outside_file) and os.path.exists(inside_file)
                        
                        # Размер файлов
                        total_size = 0
                        if files_exist:
                            total_size = (os.path.getsize(outside_file) + 
                                        os.path.getsize(inside_file)) // 1024
                        
                        recordings_data.append({
                            'name': test_name,
                            'date': metadata.get('timestamp', ''),
                            'duration': f"{metadata.get('duration', 0):.1f}с",
                            'size': f"{total_size} КБ",
                            'status': '✅' if files_exist else '⚠️'
                        })
                        
                    except Exception as e:
                        print(f"Ошибка чтения {filename}: {e}")
            
            # Сортируем по дате (новые первые)
            recordings_data.sort(key=lambda x: x['date'], reverse=True)
            
            # Добавляем в TreeView
            for data in recordings_data:
                self.recordings_tree.insert("", "end", values=(
                    data['name'], data['date'], data['duration'], 
                    data['size'], data['status']
                ))
            
            self.status_var.set(f"📁 Записей: {len(recordings_data)}")
            
        except Exception as e:
            print(f"Ошибка обновления списка: {e}")
    
    def analyze_selected(self):
        """Анализ выбранной записи"""
        selection = self.recordings_tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Выберите запись для анализа")
            return
        
        item = selection[0]
        test_name = self.recordings_tree.item(item)['values'][0]
        
        self.status_var.set(f"🔍 Анализ {test_name}...")
        
        def analyze():
            try:
                outside_path = os.path.join(self.recordings_folder, f"{test_name}_outside.wav")
                inside_path = os.path.join(self.recordings_folder, f"{test_name}_inside.wav")
                
                if not os.path.exists(outside_path) or not os.path.exists(inside_path):
                    messagebox.showerror("Ошибка", "Файлы записи не найдены!")
                    return
                
                # Выполняем анализ
                result = self.analyzer.analyze_with_audio_analysis(
                    outside_path, inside_path, test_name
                )
                
                # Показываем результаты
                self.root.after(0, lambda: self.show_analysis_result(result))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка анализа:\n{e}"))
            finally:
                self.root.after(0, lambda: self.status_var.set("✅ Анализ завершен"))
        
        threading.Thread(target=analyze, daemon=True).start()
    
    def analyze_last_recording(self):
        """Анализ последней записи"""
        # Находим последнюю запись
        items = self.recordings_tree.get_children()
        if items:
            self.recordings_tree.selection_set(items[0])
            self.analyze_selected()
    
    def show_analysis_result(self, result):
        """Показать результаты анализа"""
        overall = result.get('results', {}).get('overall_assessment', {})
        
        verdict = overall.get('verdict', 'НЕТ ДАННЫХ')
        quality = overall.get('quality', 'неизвестно')
        summary = overall.get('summary', '')
        
        # Создаем окно результатов
        result_window = tk.Toplevel(self.root)
        result_window.title(f"Результаты анализа: {result['test_name']}")
        result_window.geometry("600x400")
        
        # Вердикт
        verdict_frame = ttk.Frame(result_window, padding="10")
        verdict_frame.pack(fill=tk.X)
        
        ttk.Label(verdict_frame, text=verdict, 
                 font=('Arial', 14, 'bold'),
                 foreground='red' if 'НЕДОСТАТОЧНАЯ' in verdict else 'green').pack()
        
        # Детали
        details_frame = ttk.LabelFrame(result_window, text="Детали", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(details_frame, text=f"Качество: {quality}").pack(anchor=tk.W, pady=5)
        ttk.Label(details_frame, text=f"Резюме: {summary}").pack(anchor=tk.W, pady=5)
        
        # Рекомендации
        recommendations = overall.get('recommendations', [])
        if recommendations:
            rec_frame = ttk.LabelFrame(details_frame, text="Рекомендации", padding="5")
            rec_frame.pack(fill=tk.X, pady=10)
            
            for rec in recommendations:
                ttk.Label(rec_frame, text=f"• {rec}").pack(anchor=tk.W)
        
        # Кнопки
        btn_frame = ttk.Frame(result_window)
        btn_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Button(btn_frame, text="Сохранить отчет", 
                  command=lambda: self.save_analysis_report(result)).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Закрыть", 
                  command=result_window.destroy).pack(side=tk.RIGHT)
    
    def save_analysis_report(self, result):
        """Сохранение отчета анализа"""
        try:
            report_path = os.path.join(self.recordings_folder, 
                                      f"{result['test_name']}_report.txt")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"ОТЧЕТ АНАЛИЗА: {result['test_name']}\n")
                f.write(f"Дата: {result['timestamp']}\n")
                f.write("=" * 50 + "\n\n")
                
                overall = result.get('results', {}).get('overall_assessment', {})
                f.write(f"ВЕРДИКТ: {overall.get('verdict', '')}\n")
                f.write(f"КАЧЕСТВО: {overall.get('quality', '')}\n")
                f.write(f"СНИЖЕНИЕ ШУМА: {overall.get('db_reduction', 0):.1f} дБ\n\n")
                f.write(f"ЗАКЛЮЧЕНИЕ: {overall.get('summary', '')}\n\n")
                
                recommendations = overall.get('recommendations', [])
                if recommendations:
                    f.write("РЕКОМЕНДАЦИИ:\n")
                    for rec in recommendations:
                        f.write(f"  • {rec}\n")
            
            messagebox.showinfo("Сохранение", f"Отчет сохранен:\n{report_path}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения:\n{e}")
    
    def show_metadata(self):
        """Показать метаданные"""
        selection = self.recordings_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        test_name = self.recordings_tree.item(item)['values'][0]
        
        metadata_path = os.path.join(self.recordings_folder, f"{test_name}_metadata.json")
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Показываем в новом окне
                meta_window = tk.Toplevel(self.root)
                meta_window.title(f"Метаданные: {test_name}")
                meta_window.geometry("500x400")
                
                text = tk.Text(meta_window, wrap=tk.WORD)
                text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                text.insert(1.0, json.dumps(metadata, ensure_ascii=False, indent=2))
                text.config(state=tk.DISABLED)
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка чтения:\n{e}")
        else:
            messagebox.showwarning("Не найдено", "Метаданные не найдены")
    
    def play_recording(self):
        """Воспроизведение записи"""
        selection = self.recordings_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        test_name = self.recordings_tree.item(item)['values'][0]
        
        outside_path = os.path.join(self.recordings_folder, f"{test_name}_outside.wav")
        inside_path = os.path.join(self.recordings_folder, f"{test_name}_inside.wav")
        
        # Показываем выбор файла
        choice = messagebox.askquestion("Воспроизведение", 
                                       "Какой файл воспроизвести?",
                                       icon='question',
                                       type='yesnocancel',
                                       default='yes',
                                       detail='Да - снаружи, Нет - внутри, Отмена')
        
        if choice == 'yes' and os.path.exists(outside_path):
            os.startfile(outside_path)
        elif choice == 'no' and os.path.exists(inside_path):
            os.startfile(inside_path)
    
    def plot_waveform(self):
        """Построение графика волны"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            import wave
            
            selection = self.recordings_tree.selection()
            if not selection:
                return
            
            item = selection[0]
            test_name = self.recordings_tree.item(item)['values'][0]
            
            # Открываем WAV файл
            wav_path = os.path.join(self.recordings_folder, f"{test_name}_outside.wav")
            
            if not os.path.exists(wav_path):
                messagebox.showerror("Ошибка", "Файл не найден")
                return
            
            with wave.open(wav_path, 'rb') as wav_file:
                # Читаем параметры
                n_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                
                # Читаем данные
                frames = wav_file.readframes(n_frames)
                
                # Конвертируем в numpy array
                if sample_width == 1:
                    dtype = np.uint8
                elif sample_width == 2:
                    dtype = np.int16
                elif sample_width == 4:
                    dtype = np.int32
                else:
                    raise ValueError(f"Unsupported sample width: {sample_width}")
                
                audio_data = np.frombuffer(frames, dtype=dtype)
                
                # Масштабируем время
                time = np.linspace(0, len(audio_data) / framerate, num=len(audio_data))
                
                # Строим график
                plt.figure(figsize=(10, 4))
                plt.plot(time, audio_data, linewidth=0.5)
                plt.title(f"Waveform: {test_name}")
                plt.xlabel("Время (сек)")
                plt.ylabel("Амплитуда")
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.show()
                
        except ImportError:
            messagebox.showwarning("Matplotlib", "Установите matplotlib: pip install matplotlib")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка построения графика:\n{e}")
    
    def calculate_stats(self):
        """Расчет статистики"""
        selection = self.recordings_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        test_name = self.recordings_tree.item(item)['values'][0]
        
        try:
            import numpy as np
            import wave
            
            outside_path = os.path.join(self.recordings_folder, f"{test_name}_outside.wav")
            inside_path = os.path.join(self.recordings_folder, f"{test_name}_inside.wav")
            
            def get_wav_stats(filepath):
                """Получение статистики WAV файла"""
                with wave.open(filepath, 'rb') as wav:
                    frames = wav.readframes(wav.getnframes())
                    
                    if wav.getsampwidth() == 2:
                        audio = np.frombuffer(frames, dtype=np.int16)
                    elif wav.getsampwidth() == 4:
                        audio = np.frombuffer(frames, dtype=np.int32)
                    else:
                        audio = np.frombuffer(frames, dtype=np.uint8)
                    
                    # Нормализуем
                    audio = audio.astype(np.float32) / np.max(np.abs(audio))
                    
                    return {
                        'mean': float(np.mean(audio)),
                        'std': float(np.std(audio)),
                        'max': float(np.max(audio)),
                        'min': float(np.min(audio)),
                        'rms': float(np.sqrt(np.mean(audio**2)))
                    }
            
            if os.path.exists(outside_path) and os.path.exists(inside_path):
                stats_outside = get_wav_stats(outside_path)
                stats_inside = get_wav_stats(inside_path)
                
                # Сравнение
                attenuation = 20 * np.log10(stats_inside['rms'] / stats_outside['rms']) if stats_outside['rms'] > 0 else -80
                
                result = f"📊 СТАТИСТИКА: {test_name}\n\n"
                result += "СНАРУЖИ:\n"
                result += f"  Среднее: {stats_outside['mean']:.4f}\n"
                result += f"  СКО: {stats_outside['std']:.4f}\n"
                result += f"  RMS: {stats_outside['rms']:.4f}\n\n"
                
                result += "ВНУТРИ:\n"
                result += f"  Среднее: {stats_inside['mean']:.4f}\n"
                result += f"  СКО: {stats_inside['std']:.4f}\n"
                result += f"  RMS: {stats_inside['rms']:.4f}\n\n"
                
                result += f"СНИЖЕНИЕ: {abs(attenuation):.1f} дБ\n"
                
                if abs(attenuation) > 40:
                    result += "\n✅ ОТЛИЧНАЯ ИЗОЛЯЦИЯ"
                elif abs(attenuation) > 25:
                    result += "\n⚠️ СРЕДНЯЯ ИЗОЛЯЦИЯ"
                else:
                    result += "\n❌ ПЛОХАЯ ИЗОЛЯЦИЯ"
                
                messagebox.showinfo("Статистика", result)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка расчета:\n{e}")
    
    def export_all_data(self):
        """Экспорт всех данных"""
        try:
            # Создаем папку для экспорта
            export_folder = "export"
            if not os.path.exists(export_folder):
                os.makedirs(export_folder)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Собираем все данные
            all_data = []
            
            # Сканируем записи
            for filename in os.listdir(self.recordings_folder):
                if filename.endswith('_metadata.json'):
                    test_name = filename.replace('_metadata.json', '')
                    metadata_path = os.path.join(self.recordings_folder, filename)
                    
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # Добавляем базовую информацию
                        record_data = {
                            'test_name': test_name,
                            'timestamp': metadata.get('timestamp', ''),
                            'duration': metadata.get('duration', 0),
                            'sample_rate': metadata.get('sample_rate', 0)
                        }
                        
                        all_data.append(record_data)
                        
                    except Exception as e:
                        print(f"Ошибка чтения {filename}: {e}")
            
            # Экспортируем в CSV
            if all_data:
                export_path = os.path.join(export_folder, f"export_{timestamp}.csv")
                
                if POLARS_AVAILABLE:
                    # Используем Polars для экспорта
                    df = pl.DataFrame(all_data)
                    df.write_csv(export_path)
                else:
                    # Используем стандартный CSV
                    import csv
                    with open(export_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
                        writer.writeheader()
                        writer.writerows(all_data)
                
                messagebox.showinfo("Экспорт", f"Данные экспортированы:\n{export_path}")
                
                # Открываем папку
                os.startfile(export_folder)
            else:
                messagebox.showwarning("Нет данных", "Нет данных для экспорта")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта:\n{e}")
    
    def generate_html_report(self):
        """Генерация HTML отчета"""
        selection = self.recordings_tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Выберите запись для отчета")
            return
        
        item = selection[0]
        test_name = self.recordings_tree.item(item)['values'][0]
        
        try:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Отчет: {test_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .header {{ background: #007acc; color: white; padding: 20px; }}
                    .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007acc; background: #f5f5f5; }}
                    .verdict {{ font-size: 24px; font-weight: bold; padding: 15px; text-align: center; }}
                    .good {{ background: #d4edda; color: #155724; }}
                    .bad {{ background: #f8d7da; color: #721c24; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🎯 Отчет звукоизоляции</h1>
                    <p>Тест: {test_name}</p>
                    <p>Дата: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
                
                <div class="section">
                    <h2>Информация о системе</h2>
                    <p>Python: {sys.version.split()[0]}</p>
                    <p>ОС: {sys.platform}</p>
                    <p>Polars: {POLARS_AVAILABLE}</p>
                </div>
                
                <div class="section">
                    <h2>Рекомендации для дипломной работы</h2>
                    <ul>
                        <li>Добавить анализ спектрограмм</li>
                        <li>Реализовать сравнение разных алгоритмов</li>
                        <li>Добавить базу данных для хранения результатов</li>
                        <li>Создать веб-интерфейс для удаленного доступа</li>
                    </ul>
                </div>
                
                <div class="verdict good">
                    ✅ СИСТЕМА РАБОТАЕТ НА PYTHON 3.13
                </div>
                
                <div class="section">
                    <h2>Примечание</h2>
                    <p>Для полного анализа установите дополнительные библиотеки:</p>
                    <code>pip install polars matplotlib scipy</code>
                </div>
            </body>
            </html>
            """
            
            # Сохраняем HTML
            report_folder = "reports"
            if not os.path.exists(report_folder):
                os.makedirs(report_folder)
            
            report_path = os.path.join(report_folder, f"report_{test_name}.html")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            # Открываем в браузере
            webbrowser.open(f"file:///{os.path.abspath(report_path)}")
            
            messagebox.showinfo("HTML отчет", f"Отчет сохранен:\n{report_path}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка генерации отчета:\n{e}")
    
    def generate_text_report(self):
        """Генерация текстового отчета"""
        selection = self.recordings_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        test_name = self.recordings_tree.item(item)['values'][0]
        
        try:
            report = f"""
            {'='*60}
            ОТЧЕТ ТЕСТИРОВАНИЯ ЗВУКОИЗОЛЯЦИИ
            {'='*60}
            
            Тест: {test_name}
            Дата генерации: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            Python версия: {sys.version.split()[0]}
            Polars доступен: {POLARS_AVAILABLE}
            
            {'='*60}
            ВЫВОДЫ ДЛЯ ДИПЛОМНОЙ РАБОТЫ:
            {'='*60}
            
            1. РАЗРАБОТАНА ФУНКЦИОНАЛЬНАЯ СИСТЕМА тестирования звукоизоляции
            2. РЕАЛИЗОВАНА ЗАПИСЬ с двух микрофонов одновременно
            3. СОХРАНЕНИЕ ДАННЫХ в форматах WAV + JSON
            4. ВИЗУАЛЬНЫЙ ИНТЕРФЕЙС на tkinter
            5. РАБОТА НА PYTHON 3.13 с использованием Polars
            
            {'='*60}
            ПЕРСПЕКТИВЫ РАЗВИТИЯ:
            {'='*60}
            
            1. Добавить машинное обучение для классификации шумов
            2. Реализовать веб-интерфейс
            3. Добавить базу данных результатов
            4. Интегрировать с IoT устройствами
            5. Создать мобильное приложение
            
            {'='*60}
            © Система тестирования звукоизоляции помещений
            Версия для Python 3.13
            {'='*60}
            """
            
            # Сохраняем
            report_folder = "reports"
            if not os.path.exists(report_folder):
                os.makedirs(report_folder)
            
            report_path = os.path.join(report_folder, f"report_{test_name}.txt")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            messagebox.showinfo("Текстовый отчет", f"Отчет сохранен:\n{report_path}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка генерации:\n{e}")
    
    def generate_summary_table(self):
        """Генерация сводной таблицы"""
        try:
            if not POLARS_AVAILABLE:
                messagebox.showwarning("Polars", "Установите polars для этой функции")
                return
            
            # Собираем данные
            data = []
            
            for filename in os.listdir(self.recordings_folder):
                if filename.endswith('_metadata.json'):
                    test_name = filename.replace('_metadata.json', '')
                    metadata_path = os.path.join(self.recordings_folder, filename)
                    
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        data.append({
                            'test': test_name,
                            'date': metadata.get('timestamp', ''),
                            'duration': metadata.get('duration', 0),
                            'samples': metadata.get('sample_rate', 0) * metadata.get('duration', 0)
                        })
                        
                    except:
                        pass
            
            if data:
                # Создаем DataFrame
                df = pl.DataFrame(data)
                
                # Анализируем
                summary = df.select([
                    pl.count().alias('total_tests'),
                    pl.col('duration').mean().alias('avg_duration'),
                    pl.col('duration').max().alias('max_duration'),
                    pl.col('duration').min().alias('min_duration')
                ])
                
                # Показываем результаты
                result_window = tk.Toplevel(self.root)
                result_window.title("Сводная таблица")
                result_window.geometry("400x300")
                
                text = tk.Text(result_window, wrap=tk.WORD)
                text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                result_text = "📊 СВОДНАЯ ТАБЛИЦА\n"
                result_text += "=" * 40 + "\n\n"
                
                for row in summary.iter_rows(named=True):
                    for key, value in row.items():
                        result_text += f"{key}: {value}\n"
                
                result_text += "\n" + "=" * 40 + "\n"
                result_text += f"Всего записей: {df.height}\n"
                result_text += f"Использован Polars: {POLARS_AVAILABLE}\n"
                
                text.insert(1.0, result_text)
                text.config(state=tk.DISABLED)
                
            else:
                messagebox.showinfo("Нет данных", "Нет данных для анализа")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка анализа:\n{e}")

def main():
    """Главная функция"""
    try:
        root = tk.Tk()
        app = AdvancedSoundTester(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Критическая ошибка", f"Ошибка запуска:\n{e}")

if __name__ == "__main__":
    main()