# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sys
import os
import json
import webbrowser
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.append(os.path.dirname(__file__))

try:
    from audio_core import AudioCore
    from ai_analyzer import SoundIsolationAnalyzer
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    messagebox.showerror("Ошибка", f"Не удалось загрузить модули:\n{e}")
    sys.exit(1)

class SimpleSoundTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Sound Isolation Tester - VS2022")
        self.root.geometry("1000x700")
        
        self.center_window()
        
        try:
            self.audio_core = AudioCore()
            self.ai_analyzer = SoundIsolationAnalyzer()
            self.setup_ui()
            self.refresh_devices()
            self.root.after(1000, self.refresh_recordings)
        except Exception as e:
            messagebox.showerror("Ошибка инициализации", f"Не удалось инициализировать аудио систему:\n{e}")
            self.root.destroy()
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def setup_ui(self):
        style = ttk.Style()
        style.configure('Accent.TButton', foreground='white', background='#007acc')
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text="🎯 Тестер звукоизоляции помещений", font=('Segoe UI', 16, 'bold'))
        title_label.pack(pady=10)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        record_frame = ttk.Frame(notebook, padding="10")
        notebook.add(record_frame, text="🎙️ Запись")
        self.setup_record_tab(record_frame)
        
        analysis_frame = ttk.Frame(notebook, padding="10")
        notebook.add(analysis_frame, text="📊 Анализ")
        self.setup_analysis_tab(analysis_frame)
        
        self.create_status_bar(main_frame)
    
    def setup_record_tab(self, parent):
        self.create_device_section(parent)
        self.create_control_section(parent)
        self.create_level_section(parent)
    
    def create_device_section(self, parent):
        device_frame = ttk.LabelFrame(parent, text="Настройка микрофонов", padding="10")
        device_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(device_frame, text="Микрофон СНАРУЖИ комнаты:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.outside_combo = ttk.Combobox(device_frame, width=50, state="readonly")
        self.outside_combo.grid(row=0, column=1, padx=10, pady=5, sticky=tk.EW)
        
        ttk.Label(device_frame, text="Микрофон ВНУТРИ комнаты:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.inside_combo = ttk.Combobox(device_frame, width=50, state="readonly")
        self.inside_combo.grid(row=1, column=1, padx=10, pady=5, sticky=tk.EW)
        
        btn_frame = ttk.Frame(device_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="🔄 Обновить список", command=self.refresh_devices).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🎧 Тест устройств", command=self.test_devices).pack(side=tk.LEFT, padx=5)
        
        device_frame.columnconfigure(1, weight=1)
    
    def create_control_section(self, parent):
        control_frame = ttk.LabelFrame(parent, text="Управление тестом", padding="10")
        control_frame.pack(fill=tk.X, pady=10)
        
        test_name_frame = ttk.Frame(control_frame)
        test_name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(test_name_frame, text="Название теста:").pack(side=tk.LEFT)
        self.test_name_var = tk.StringVar(value=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        ttk.Entry(test_name_frame, textvariable=self.test_name_var, width=30).pack(side=tk.LEFT, padx=5)
        
        duration_frame = ttk.Frame(control_frame)
        duration_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(duration_frame, text="Длительность теста (сек):").pack(side=tk.LEFT)
        self.duration_var = tk.StringVar(value="10")
        duration_spin = ttk.Spinbox(duration_frame, from_=5, to=60, textvariable=self.duration_var, width=10)
        duration_spin.pack(side=tk.LEFT, padx=10)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=15)
        
        self.start_btn = ttk.Button(btn_frame, text="🔴 Начать запись", command=self.start_test, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹️ Остановить", command=self.stop_test, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="📊 Статистика", command=self.show_stats).pack(side=tk.LEFT, padx=5)
    
    def create_level_section(self, parent):
        level_frame = ttk.LabelFrame(parent, text="Уровни звука в реальном времени", padding="10")
        level_frame.pack(fill=tk.X, pady=10)
        
        level_outside_frame = ttk.Frame(level_frame)
        level_outside_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(level_outside_frame, text="СНАРУЖИ:", width=10).pack(side=tk.LEFT)
        self.outside_level = ttk.Progressbar(level_outside_frame, length=400, mode='determinate')
        self.outside_level.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.outside_label = ttk.Label(level_outside_frame, text="0%", width=5)
        self.outside_label.pack(side=tk.RIGHT)
        
        level_inside_frame = ttk.Frame(level_frame)
        level_inside_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(level_inside_frame, text="ВНУТРИ:", width=10).pack(side=tk.LEFT)
        self.inside_level = ttk.Progressbar(level_inside_frame, length=400, mode='determinate')
        self.inside_level.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.inside_label = ttk.Label(level_inside_frame, text="0%", width=5)
        self.inside_label.pack(side=tk.RIGHT)
    
    def setup_analysis_tab(self, parent):
        ttk.Label(parent, text="📁 Управление записями и анализ", font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="🔄 Обновить список", command=self.refresh_recordings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📁 Открыть папку записей", command=self.open_recordings_folder).pack(side=tk.LEFT, padx=5)
        
        list_frame = ttk.LabelFrame(parent, text="Последние записи", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        columns = ("test_name", "timestamp", "duration", "files")
        self.recordings_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        self.recordings_tree.heading("test_name", text="Название теста")
        self.recordings_tree.heading("timestamp", text="Время записи")
        self.recordings_tree.heading("duration", text="Длительность")
        self.recordings_tree.heading("files", text="Файлы")
        
        self.recordings_tree.column("test_name", width=200)
        self.recordings_tree.column("timestamp", width=180)
        self.recordings_tree.column("duration", width=100)
        self.recordings_tree.column("files", width=80)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.recordings_tree.yview)
        self.recordings_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recordings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(action_frame, text="📋 Показать метаданные", command=self.show_metadata).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🧠 ИИ-анализ звукоизоляции", command=self.run_ai_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📊 Быстрый анализ", command=self.quick_analysis).pack(side=tk.LEFT, padx=5)
    
    def create_status_bar(self, parent):
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, padding=(5, 2))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
    
    def refresh_devices(self):
        try:
            devices = self.audio_core.get_audio_devices()
            device_list = [f"{d['index']}: {d['name']} (каналы: {d['channels']})" for d in devices]
            
            self.outside_combo['values'] = device_list
            self.inside_combo['values'] = device_list
            
            if device_list:
                self.outside_combo.current(0)
                if len(device_list) > 1:
                    self.inside_combo.current(1)
                else:
                    self.inside_combo.current(0)
                    
            self.status_var.set(f"Найдено устройств: {len(devices)}")
            
        except Exception as e:
            self.status_var.set(f"Ошибка обновления устройств: {e}")
            messagebox.showerror("Ошибка", f"Не удалось получить список устройств:\n{e}")
    
    def get_selected_devices(self):
        try:
            if not self.outside_combo.get() or not self.inside_combo.get():
                messagebox.showerror("Ошибка", "Выберите оба микрофона!")
                return None, None
                
            outside_idx = int(self.outside_combo.get().split(':')[0])
            inside_idx = int(self.inside_combo.get().split(':')[0])
            return outside_idx, inside_idx
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка выбора устройств:\n{e}")
            return None, None

    def test_devices(self):
        outside_idx, inside_idx = self.get_selected_devices()
        if outside_idx is None:
            return
        
        if outside_idx == inside_idx:
            messagebox.showwarning("Предупреждение", "Выбраны одинаковые устройства!\nДля теста звукоизоляции нужны два РАЗНЫХ микрофона.")
            return
        
        self.status_var.set("Тестирование устройств...")
        
        def test_thread():
            try:
                success = self.audio_core.start_recording(outside_idx, inside_idx, duration=3)
                
                if success:
                    time.sleep(4)
                    stats = self.audio_core.get_recording_stats()
                    self.root.after(0, lambda: self.show_test_results(stats))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось начать запись с выбранных устройств"))
            
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка теста", f"Ошибка при тестировании устройств:\n{e}"))
            finally:
                self.root.after(0, lambda: self.status_var.set("Тестирование завершено"))
        
        threading.Thread(target=test_thread, daemon=True).start()

    def show_test_results(self, stats):
        outside_dev = self.outside_combo.get()
        inside_dev = self.inside_combo.get()
        
        message = (f"📊 Результаты тестирования устройств:\n\n"
                  f"🔊 Устройство СНАРУЖИ:\n{outside_dev}\n"
                  f"   Записано: {stats['outside_samples']} сэмплов\n\n"
                  f"🔇 Устройство ВНУТРИ:\n{inside_dev}\n"
                  f"   Записано: {stats['inside_samples']} сэмплов\n\n"
                  f"⏱️ Длительность: {stats['duration']:.2f} сек\n\n")
        
        if stats['outside_samples'] == 0:
            message += "❌ Внешний микрофон не записал данные!\n"
        elif stats['inside_samples'] == 0:
            message += "❌ Внутренний микрофон не записал данные!\n"
        elif abs(stats['outside_samples'] - stats['inside_samples']) > 1000:
            message += "⚠️ Разница в количестве сэмплов - возможны проблемы синхронизации\n"
        else:
            message += "✅ Оба устройства работают корректно!\n"
        
        messagebox.showinfo("Результаты теста", message)

    def start_test(self):
        outside_idx, inside_idx = self.get_selected_devices()
        if outside_idx is None:
            return
        
        if outside_idx == inside_idx:
            messagebox.showwarning("Предупреждение", "Выбраны одинаковые устройства!\nДля теста звукоизоляции нужны два РАЗНЫХ микрофона.")
            return
        
        duration = int(self.duration_var.get())
        test_name = self.test_name_var.get().strip()
        
        if not test_name:
            test_name = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.test_name_var.set(test_name)
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        def record_thread():
            success = self.audio_core.start_recording(outside_idx, inside_idx, duration, test_name)
            
            if success:
                self.root.after(0, lambda: self.status_var.set(f"Запись... {duration} сек"))
                self.root.after(0, self.start_realtime_update)
            else:
                self.root.after(0, lambda: self.status_var.set("Ошибка записи!"))
                self.root.after(0, self.reset_buttons)
        
        threading.Thread(target=record_thread, daemon=True).start()

    def stop_test(self):
        saved_files = self.audio_core.stop_recording()
        self.status_var.set("Запись остановлена и сохранена")
        self.reset_buttons()
        
        if saved_files.get('outside') and saved_files.get('inside'):
            messagebox.showinfo("Запись завершена", 
                              f"✅ Запись сохранена!\n\n"
                              f"Файлы:\n"
                              f"• {saved_files['outside']['filename']}\n"
                              f"• {saved_files['inside']['filename']}\n\n"
                              f"Папка: {self.audio_core.recordings_folder}")
            
            self.refresh_recordings()
        else:
            messagebox.showwarning("Внимание", "Запись завершена, но некоторые файлы не сохранены!")

    def reset_buttons(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def start_realtime_update(self):
        if self.audio_core.is_recording:
            try:
                levels = self.audio_core.get_audio_levels()
                
                outside_percent = levels['outside'] * 100
                inside_percent = levels['inside'] * 100
                
                self.outside_level['value'] = outside_percent
                self.inside_level['value'] = inside_percent
                
                self.outside_label.config(text=f"{outside_percent:.0f}%")
                self.inside_label.config(text=f"{inside_percent:.0f}%")
                
                self.root.after(100, self.start_realtime_update)
            except Exception as e:
                print(f"Ошибка обновления UI: {e}")
                self.root.after(100, self.start_realtime_update)
        else:
            self.reset_buttons()
            self.status_var.set("Запись завершена")

    def show_stats(self):
        stats = self.audio_core.get_recording_stats()
        messagebox.showinfo("Статистика", 
                          f"📊 Текущая статистика:\n\n"
                          f"Снаружи: {stats['outside_samples']} сэмплов\n"
                          f"Внутри: {stats['inside_samples']} сэмплов\n"
                          f"Длительность: {stats['duration']:.2f} сек\n"
                          f"Время: {stats['timestamp']}")

    def refresh_recordings(self):
        try:
            for item in self.recordings_tree.get_children():
                self.recordings_tree.delete(item)
            
            recordings = self.audio_core.get_recent_recordings()
            
            for recording in recordings:
                test_name = recording.get('test_name', 'unknown')
                timestamp = recording.get('timestamp', '')
                duration = f"{recording.get('duration', 0):.1f}сек"
                
                files = recording.get('files', {})
                file_status = "✅" if files.get('outside') and files.get('inside') else "⚠️"
                
                self.recordings_tree.insert("", "end", values=(
                    test_name, timestamp, duration, file_status
                ))
            
            self.status_var.set(f"Загружено записей: {len(recordings)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить записи:\n{e}")

    def open_recordings_folder(self):
        try:
            recordings_path = os.path.abspath(self.audio_core.recordings_folder)
            webbrowser.open(recordings_path)
            self.status_var.set("Папка записей открыта")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{e}")

    def show_metadata(self):
        selection = self.recordings_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите запись из списка")
            return
        
        try:
            item = selection[0]
            test_name = self.recordings_tree.item(item)['values'][0]
            
            metadata_file = os.path.join(self.audio_core.recordings_folder, f"{test_name}_metadata.json")
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata_window = tk.Toplevel(self.root)
            metadata_window.title(f"Метаданные: {test_name}")
            metadata_window.geometry("600x400")
            
            text_widget = tk.Text(metadata_window, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            formatted_metadata = json.dumps(metadata, ensure_ascii=False, indent=2)
            text_widget.insert(tk.END, formatted_metadata)
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить метаданные:\n{e}")

    def run_ai_analysis(self):
        selection = self.recordings_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите запись из списка")
            return
        
        try:
            item = selection[0]
            test_name = self.recordings_tree.item(item)['values'][0]
            
            outside_path = os.path.join(self.audio_core.recordings_folder, f"{test_name}_outside.wav")
            inside_path = os.path.join(self.audio_core.recordings_folder, f"{test_name}_inside.wav")
            
            if not os.path.exists(outside_path) or not os.path.exists(inside_path):
                messagebox.showerror("Ошибка", f"Аудиофайлы для теста {test_name} не найдены!")
                return
            
            self.status_var.set("Запуск ИИ-анализа...")
            
            def analysis_thread():
                try:
                    analysis_result = self.ai_analyzer.analyze_with_audio_analysis(
                        outside_path, inside_path, test_name
                    )
                    
                    report_path = self.ai_analyzer.save_analysis_report(
                        analysis_result, self.audio_core.recordings_folder
                    )
                    
                    html_path = self.ai_analyzer.generate_html_report(
                        analysis_result, self.audio_core.recordings_folder
                    )
                    
                    self.root.after(0, lambda: self.show_analysis_results(
                        analysis_result, report_path, html_path
                    ))
                    
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Ошибка анализа", f"Не удалось выполнить анализ:\n{e}"
                    ))
                finally:
                    self.root.after(0, lambda: self.status_var.set("Анализ завершен"))
            
            threading.Thread(target=analysis_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить анализ:\n{e}")

    def show_analysis_results(self, analysis_result, report_path, html_path):
        results = analysis_result.get('results', {})
        overall = results.get('overall_assessment', {})
        
        verdict = overall.get('verdict', 'НЕТ ДАННЫХ')
        quality = overall.get('quality', 'неизвестно')
        summary = overall.get('summary', 'Нет данных')
        recommendations = overall.get('recommendations', [])
        
        result_window = tk.Toplevel(self.root)
        result_window.title(f"Результаты анализа: {analysis_result['test_name']}")
        result_window.geometry("600x500")
        
        title_frame = ttk.Frame(result_window, padding="10")
        title_frame.pack(fill=tk.X)
        
        ttk.Label(title_frame, text="🧠 Результаты ИИ-анализа звукоизоляции", 
                  font=('Segoe UI', 14, 'bold')).pack()
        
        verdict_color = overall.get('color', 'gray')
        verdict_frame = ttk.Frame(result_window, padding="10")
        verdict_frame.pack(fill=tk.X, pady=10)
        
        verdict_label = ttk.Label(verdict_frame, text=verdict, 
                                 font=('Segoe UI', 16, 'bold'),
                                 background=verdict_color, 
                                 foreground='white',
                                 padding=10)
        verdict_label.pack(fill=tk.X)
        
        details_frame = ttk.LabelFrame(result_window, text="Детали анализа", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(details_frame, text=f"Качество изоляции: {quality}").pack(anchor=tk.W)
        ttk.Label(details_frame, text=f"Заключение: {summary}").pack(anchor=tk.W)
        
        if recommendations:
            rec_frame = ttk.LabelFrame(details_frame, text="Рекомендации", padding="5")
            rec_frame.pack(fill=tk.X, pady=10)
            
            for rec in recommendations:
                ttk.Label(rec_frame, text=f"• {rec}").pack(anchor=tk.W)
        
        btn_frame = ttk.Frame(result_window)
        btn_frame.pack(fill=tk.X, pady=10)
        
        if html_path and os.path.exists(html_path):
            ttk.Button(btn_frame, text="📄 Открыть HTML отчет", 
                      command=lambda: webbrowser.open(html_path)).pack(side=tk.LEFT, padx=5)
        
        if report_path and os.path.exists(report_path):
            ttk.Button(btn_frame, text="📋 Открыть JSON отчет", 
                      command=lambda: webbrowser.open(report_path)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Закрыть", 
                  command=result_window.destroy).pack(side=tk.RIGHT, padx=5)

    def quick_analysis(self):
        selection = self.recordings_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите запись из списка")
            return
        
        try:
            item = selection[0]
            test_name = self.recordings_tree.item(item)['values'][0]
            
            messagebox.showinfo("Быстрый анализ", 
                              f"Анализ записи: {test_name}\n\n"
                              f"Функция быстрого анализа в разработке.\n"
                              f"Используйте ИИ-анализ для полной оценки.")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить анализ:\n{e}")

def main():
    try:
        root = tk.Tk()
        app = SimpleSoundTester(root)
        root.mainloop()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        messagebox.showerror("Ошибка", f"Критическая ошибка приложения:\n{e}")

if __name__ == "__main__":
    main()