# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime

class EnhancedSoundIsolationAnalyzer:
    """Анализатор звукоизоляции для Python 3.13"""
    
    def __init__(self):
        self.initialized = False
        
        # Пытаемся загрузить библиотеки
        try:
            import numpy as np
            self.np = np
            print("✅ NumPy загружен")
            self.initialized = True
        except ImportError:
            print("⚠️ NumPy не установлен, базовый анализ")
        
        try:
            import polars as pl
            self.pl = pl
            print("✅ Polars загружен")
        except ImportError:
            print("⚠️ Polars не установлен")
    
    def analyze_with_audio_analysis(self, outside_audio_path, inside_audio_path, test_name):
        """Анализ аудио"""
        try:
            analysis = {
                'test_name': test_name,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'analysis_type': 'basic_analysis',
                'results': {}
            }
            
            # Базовый анализ файлов
            outside_stats = self._get_file_stats(outside_audio_path)
            inside_stats = self._get_file_stats(inside_audio_path)
            
            if self.initialized:
                # Более продвинутый анализ с NumPy
                import wave
                
                # Чтение WAV файлов
                def read_wav_data(filepath):
                    with wave.open(filepath, 'rb') as wav:
                        frames = wav.readframes(wav.getnframes())
                        if wav.getsampwidth() == 2:
                            data = self.np.frombuffer(frames, dtype=self.np.int16)
                        else:
                            data = self.np.frombuffer(frames, dtype=self.np.uint8)
                        return data.astype(self.np.float32) / self.np.max(self.np.abs(data))
                
                try:
                    outside_data = read_wav_data(outside_audio_path)
                    inside_data = read_wav_data(inside_audio_path)
                    
                    # Расчет метрик
                    outside_rms = self.np.sqrt(self.np.mean(outside_data**2))
                    inside_rms = self.np.sqrt(self.np.mean(inside_data**2))
                    
                    if outside_rms > 0:
                        db_reduction = 20 * self.np.log10(inside_rms / outside_rms)
                        attenuation = abs(db_reduction)
                    else:
                        attenuation = 80
                    
                    # Определение качества
                    if attenuation >= 45:
                        quality = "отличная"
                        verdict = "ОТЛИЧНАЯ ИЗОЛЯЦИЯ"
                        color = "green"
                    elif attenuation >= 30:
                        quality = "хорошая"
                        verdict = "ХОРОШАЯ ИЗОЛЯЦИЯ"
                        color = "lightgreen"
                    elif attenuation >= 20:
                        quality = "удовлетворительная"
                        verdict = "СРЕДНЯЯ ИЗОЛЯЦИЯ"
                        color = "yellow"
                    else:
                        quality = "плохая"
                        verdict = "НЕДОСТАТОЧНАЯ ИЗОЛЯЦИЯ"
                        color = "red"
                    
                    analysis['results']['level_comparison'] = {
                        'outside_rms': float(outside_rms),
                        'inside_rms': float(inside_rms),
                        'attenuation_db': float(attenuation)
                    }
                    
                    analysis['results']['overall_assessment'] = {
                        'verdict': verdict,
                        'color': color,
                        'quality': quality,
                        'db_reduction': float(attenuation),
                        'summary': f"Звукоизоляция: {quality}. Снижение шума: {attenuation:.1f} дБ",
                        'recommendations': self._get_recommendations(attenuation)
                    }
                    
                except Exception as e:
                    print(f"⚠️ Ошибка продвинутого анализа: {e}")
            
            else:
                # Базовый анализ без NumPy
                analysis['results']['overall_assessment'] = {
                    'verdict': 'БАЗОВЫЙ АНАЛИЗ',
                    'color': 'gray',
                    'quality': 'неизвестно',
                    'summary': 'Установите NumPy для полного анализа',
                    'recommendations': ['Установите: pip install numpy polars']
                }
            
            return analysis
            
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
            return self._create_error_report(test_name, str(e))
    
    def _get_file_stats(self, filepath):
        """Получение статистики файла"""
        try:
            size = os.path.getsize(filepath) // 1024  # КБ
            return {'size_kb': size, 'exists': True}
        except:
            return {'size_kb': 0, 'exists': False}
    
    def _get_recommendations(self, attenuation):
        """Получение рекомендаций"""
        recommendations = []
        
        if attenuation < 20:
            recommendations.append("Усилить изоляцию стен и окон")
            recommendations.append("Установить звукопоглощающие материалы")
            recommendations.append("Проверить наличие щелей и зазоров")
        elif attenuation < 35:
            recommendations.append("Добавить уплотнители на двери и окна")
            recommendations.append("Рассмотреть ковровое покрытие")
        else:
            recommendations.append("Изоляция соответствует нормам")
        
        return recommendations
    
    def _create_error_report(self, test_name, error_message):
        """Создание отчета об ошибке"""
        return {
            'test_name': test_name,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'analysis_type': 'error',
            'error': error_message,
            'results': {
                'overall_assessment': {
                    'verdict': 'ОШИБКА АНАЛИЗА',
                    'color': 'red',
                    'quality': 'неизвестно',
                    'recommendations': ['Проверить аудиофайлы', 'Установить все зависимости'],
                    'summary': 'Произошла ошибка при анализе'
                }
            }
        }


