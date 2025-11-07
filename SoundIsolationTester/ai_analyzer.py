# -*- coding: utf-8 -*-
import os
import json
import librosa
import numpy as np
from datetime import datetime

class SoundIsolationAnalyzer:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
    
    def analyze_with_audio_analysis(self, outside_audio_path, inside_audio_path, test_name):
        """Локальный анализ аудио с помощью librosa"""
        try:
            print("🔍 Запуск анализа звукоизоляции...")
            
            y_outside, sr_outside = librosa.load(outside_audio_path, sr=None)
            y_inside, sr_inside = librosa.load(inside_audio_path, sr=None)
            
            analysis = {
                'test_name': test_name,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'analysis_type': 'local_audio_analysis',
                'results': {}
            }
            
            rms_outside = np.sqrt(np.mean(y_outside**2))
            rms_inside = np.sqrt(np.mean(y_inside**2))
            
            if rms_outside > 0:
                db_reduction = 20 * np.log10(rms_inside / rms_outside)
            else:
                db_reduction = -80
            
            analysis['results']['level_comparison'] = {
                'outside_rms': float(rms_outside),
                'inside_rms': float(rms_inside),
                'db_reduction': float(db_reduction),
                'isolation_quality': self._get_isolation_quality(abs(db_reduction))
            }
            
            analysis['results']['frequency_analysis'] = self._analyze_frequencies(y_outside, y_inside, sr_outside)
            analysis['results']['speech_intelligibility'] = self._analyze_speech_intelligibility(y_inside, sr_inside)
            analysis['results']['overall_assessment'] = self._generate_overall_assessment(analysis['results'])
            
            return analysis
            
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
            return self._create_basic_report(test_name, str(e))
    
    def _analyze_frequencies(self, y_outside, y_inside, sr):
        """Анализ частотных характеристик"""
        stft_outside = np.abs(librosa.stft(y_outside))
        stft_inside = np.abs(librosa.stft(y_inside))
        
        freqs = librosa.fft_frequencies(sr=sr)
        
        low_freq_mask = (freqs >= 50) & (freqs < 250)
        mid_freq_mask = (freqs >= 250) & (freqs < 2000) 
        high_freq_mask = (freqs >= 2000) & (freqs < 8000)
        
        def get_band_reduction(stft_out, stft_in, mask):
            if np.sum(stft_out[mask]) > 0:
                return 20 * np.log10(np.mean(stft_in[mask]) / np.mean(stft_out[mask]))
            return -80
        
        low_reduction = get_band_reduction(stft_outside, stft_inside, low_freq_mask)
        mid_reduction = get_band_reduction(stft_outside, stft_inside, mid_freq_mask)
        high_reduction = get_band_reduction(stft_outside, stft_inside, high_freq_mask)
        
        return {
            'low_freq_reduction': low_reduction,
            'mid_freq_reduction': mid_reduction,
            'high_freq_reduction': high_reduction,
            'low_freq_performance': self._get_frequency_performance(low_reduction),
            'mid_freq_performance': self._get_frequency_performance(mid_reduction),
            'high_freq_performance': self._get_frequency_performance(high_reduction)
        }
    
    def _analyze_speech_intelligibility(self, y_inside, sr):
        """Оценка разборчивости речи"""
        speech_band = librosa.effects.preemphasis(y_inside)
        speech_energy = np.mean(speech_band**2)
        
        if speech_energy < 1e-6:
            intelligibility = "очень низкая"
        elif speech_energy < 1e-4:
            intelligibility = "низкая" 
        elif speech_energy < 1e-2:
            intelligibility = "средняя"
        else:
            intelligibility = "высокая"
            
        return {
            'speech_energy': float(speech_energy),
            'level': intelligibility,
            'words_understandable': intelligibility in ["средняя", "высокая"]
        }
    
    def _get_isolation_quality(self, db_reduction):
        """Определение качества изоляции по снижению в дБ"""
        if db_reduction >= 45:
            return "отличная"
        elif db_reduction >= 35:
            return "хорошая"
        elif db_reduction >= 25:
            return "удовлетворительная"
        else:
            return "плохая"
    
    def _get_frequency_performance(self, reduction):
        """Оценка эффективности по частотному диапазону"""
        abs_reduction = abs(reduction)
        if abs_reduction >= 40:
            return "отличная"
        elif abs_reduction >= 30:
            return "хорошая"
        elif abs_reduction >= 20:
            return "удовлетворительная"
        else:
            return "недостаточная"
    
    def _generate_overall_assessment(self, results):
        """Генерация общей оценки"""
        level = results['level_comparison']
        freq = results['frequency_analysis']
        speech = results['speech_intelligibility']
        
        quality = level['isolation_quality']
        db_reduction = abs(level['db_reduction'])
        
        if quality == "отличная":
            verdict = "КОМНАТА ЗВУКОНЕПРОНИЦАЕМА"
            color = "green"
        elif quality == "хорошая":
            verdict = "ХОРОШАЯ ЗВУКОИЗОЛЯЦИЯ" 
            color = "lightgreen"
        elif quality == "удовлетворительная":
            verdict = "УДОВЛЕТВОРИТЕЛЬНАЯ ИЗОЛЯЦИЯ"
            color = "yellow"
        else:
            verdict = "НЕДОСТАТОЧНАЯ ЗВУКОИЗОЛЯЦИЯ"
            color = "red"
        
        recommendations = []
        if freq['low_freq_reduction'] > -25:
            recommendations.append("Улучшить изоляцию низких частот (уплотнить стыки, добавить массу)")
        if speech['words_understandable']:
            recommendations.append("Речь разборчива - усилить изоляцию в речевом диапазоне")
        if not recommendations:
            recommendations.append("Изоляция соответствует требованиям")
        
        return {
            'verdict': verdict,
            'color': color,
            'quality': quality,
            'db_reduction': db_reduction,
            'recommendations': recommendations,
            'summary': f"Звукоизоляция: {quality}. Снижение шума: {db_reduction:.1f} дБ"
        }
    
    def _create_basic_report(self, test_name, error_message=""):
        """Создание базового отчета при ошибках"""
        return {
            'test_name': test_name,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'analysis_type': 'error',
            'error': error_message,
            'results': {
                'overall_assessment': {
                    'verdict': 'АНАЛИЗ НЕ УДАЛСЯ',
                    'color': 'red',
                    'quality': 'неизвестно',
                    'recommendations': ['Проверить аудиофайлы', 'Повторить тест'],
                    'summary': 'Произошла ошибка при анализе'
                }
            }
        }
    
    def save_analysis_report(self, analysis_result, output_folder):
        """Сохранение отчета анализа"""
        try:
            filename = f"{analysis_result['test_name']}_analysis_report.json"
            filepath = os.path.join(output_folder, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Отчет анализа сохранен: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Ошибка сохранения отчета: {e}")
            return None
    
    def generate_html_report(self, analysis_result, output_folder):
        """Генерация HTML отчета"""
        try:
            template = self._create_html_template(analysis_result)
            filename = f"{analysis_result['test_name']}_report.html"
            filepath = os.path.join(output_folder, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template)
            
            print(f"✅ HTML отчет сохранен: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Ошибка генерации HTML отчета: {e}")
            return None
    
    def _create_html_template(self, analysis):
        """Создание HTML шаблона отчета"""
        results = analysis.get('results', {})
        overall = results.get('overall_assessment', {})
        level = results.get('level_comparison', {})
        freq = results.get('frequency_analysis', {})
        speech = results.get('speech_intelligibility', {})
        
        color = overall.get('color', 'gray')
        verdict = overall.get('verdict', 'НЕТ ДАННЫХ')
        quality = overall.get('quality', 'неизвестно')
        db_reduction = level.get('db_reduction', 0)
        
        return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет звукоизоляции - {analysis['test_name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .verdict {{ text-align: center; padding: 20px; margin: 20px 0; border-radius: 8px; background: {color}; color: white; font-size: 24px; font-weight: bold; }}
        .metric {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007acc; }}
        .recommendations {{ background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; }}
        .summary {{ background: #d1ecf1; padding: 15px; border-radius: 5px; border-left: 4px solid #17a2b8; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Отчет звукоизоляции помещения</h1>
            <p>Тест: <strong>{analysis['test_name']}</strong></p>
            <p>Время анализа: {analysis['timestamp']}</p>
        </div>
        
        <div class="verdict">
            {verdict}
        </div>
        
        <div class="metric">
            <h3>📊 Основные метрики</h3>
            <p><strong>Качество изоляции:</strong> {quality}</p>
            <p><strong>Снижение шума:</strong> {abs(db_reduction):.1f} дБ</p>
            <p><strong>Тип анализа:</strong> {analysis['analysis_type']}</p>
        </div>
        
        <div class="metric">
            <h3>🎵 Частотный анализ</h3>
            <p><strong>Низкие частоты:</strong> {freq.get('low_freq_performance', 'Нет данных')}</p>
            <p><strong>Средние частоты:</strong> {freq.get('mid_freq_performance', 'Нет данных')}</p>
            <p><strong>Высокие частоты:</strong> {freq.get('high_freq_performance', 'Нет данных')}</p>
        </div>
        
        <div class="metric">
            <h3>🗣️ Разборчивость речи</h3>
            <p><strong>Уровень:</strong> {speech.get('level', 'Нет данных')}</p>
            <p><strong>Слова разборчивы:</strong> {'Да' if speech.get('words_understandable') else 'Нет'}</p>
        </div>
        
        <div class="recommendations">
            <h3>💡 Рекомендации</h3>
            <ul>
                {"".join(f"<li>{rec}</li>" for rec in overall.get('recommendations', []))}
            </ul>
        </div>
        
        <div class="summary">
            <h3>📝 Заключение</h3>
            <p>{overall.get('summary', 'Нет данных')}</p>
        </div>
    </div>
</body>
</html>
        """



