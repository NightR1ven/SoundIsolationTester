# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
import numpy as np

class EnhancedSoundIsolationAnalyzer:
    """Анализатор звукоизоляции с расширенными метриками"""
    
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
        
        # Инициализация распознавателя (если доступен)
        self.recognizer = None
        try:
            from speech_recognizer import MultiEngineSpeechRecognizer, RecognitionEngine
            self.recognizer = MultiEngineSpeechRecognizer()
            print("✅ Модуль распознавания загружен")
        except ImportError:
            print("⚠️ Модуль распознавания недоступен")
    
    def analyze_with_audio_analysis(self, outside_audio_path, inside_audio_path, test_name, 
                                   reference_text=None, enable_speech_recognition=True):
        """Анализ аудио с распознаванием речи"""
        try:
            analysis = {
                'test_name': test_name,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'analysis_type': 'advanced_analysis',
                'results': {
                    'audio_analysis': {},
                    'speech_recognition': {},
                    'detailed_metrics': {},
                    'overall_assessment': {}
                }
            }
            
            # 1. Базовый анализ аудио
            audio_analysis = self._perform_audio_analysis(outside_audio_path, inside_audio_path)
            analysis['results']['audio_analysis'] = audio_analysis
            
            # 2. Распознавание речи (если включено и доступно)
            if enable_speech_recognition and self.recognizer:
                speech_analysis = self._perform_speech_recognition(
                    outside_audio_path, inside_audio_path, reference_text
                )
                analysis['results']['speech_recognition'] = speech_analysis
                
                # Интегрируем результаты
                integrated = self._integrate_analyses(audio_analysis, speech_analysis)
                analysis['results']['detailed_metrics'] = integrated
            else:
                analysis['results']['detailed_metrics'] = self._create_basic_metrics(audio_analysis)
            
            # 3. Итоговая оценка
            overall = self._calculate_overall_assessment(analysis['results']['detailed_metrics'])
            analysis['results']['overall_assessment'] = overall
            
            return analysis
            
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
            return self._create_error_report(test_name, str(e))
    
    def _perform_audio_analysis(self, outside_path, inside_path):
        """Анализ аудио характеристик"""
        analysis = {
            'file_stats': {
                'outside': self._get_file_stats(outside_path),
                'inside': self._get_file_stats(inside_path)
            },
            'level_comparison': {},
            'spectral_analysis': {},
            'basic_metrics': {}
        }
        
        if self.initialized:
            try:
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
                
                outside_data = read_wav_data(outside_path)
                inside_data = read_wav_data(inside_path)
                
                # Расчет RMS
                outside_rms = self.np.sqrt(self.np.mean(outside_data**2))
                inside_rms = self.np.sqrt(self.np.mean(inside_data**2))
                
                # Ослабление в дБ
                if outside_rms > 0:
                    db_reduction = 20 * self.np.log10(inside_rms / outside_rms)
                    attenuation = abs(db_reduction)
                else:
                    attenuation = 80
                
                # Дополнительные метрики
                analysis['level_comparison'] = {
                    'outside_rms': float(outside_rms),
                    'inside_rms': float(inside_rms),
                    'attenuation_db': float(attenuation),
                    'reduction_ratio': float(outside_rms / inside_rms) if inside_rms > 0 else 0
                }
                
                # Спектральный анализ
                if len(outside_data) > 0 and len(inside_data) > 0:
                    spectral_metrics = self._calculate_spectral_metrics(outside_data, inside_data)
                    analysis['spectral_analysis'] = spectral_metrics
                
                # Базовые метрики
                analysis['basic_metrics'] = {
                    'outside_max': float(self.np.max(np.abs(outside_data))),
                    'inside_max': float(self.np.max(np.abs(inside_data))),
                    'outside_mean': float(self.np.mean(np.abs(outside_data))),
                    'inside_mean': float(self.np.mean(np.abs(inside_data))),
                    'outside_std': float(self.np.std(outside_data)),
                    'inside_std': float(self.np.std(inside_data)),
                    'correlation': float(self.np.corrcoef(outside_data[:min(len(outside_data), len(inside_data))], 
                                                        inside_data[:min(len(outside_data), len(inside_data))])[0, 1])
                }
                
            except Exception as e:
                print(f"⚠️ Ошибка продвинутого анализа: {e}")
        
        return analysis
    
    def _perform_speech_recognition(self, outside_path, inside_path, reference_text=None):
        """Распознавание речи в аудиофайлах"""
        analysis = {
            'outside': {},
            'inside': {},
            'comparison': {},
            'engine_info': {}
        }
        
        if self.recognizer and hasattr(self.recognizer, 'current_engine'):
            engine = self.recognizer.current_engine
            if engine:
                analysis['engine_info'] = {
                    'name': engine.value,
                    'type': 'whisper' if 'whisper' in engine.value else 'vosk'
                }
                
                try:
                    # Распознавание
                    recognition_result = self.recognizer.analyze_pair(outside_path, inside_path, reference_text)
                    
                    analysis['outside'] = recognition_result.get('outside', {})
                    analysis['inside'] = recognition_result.get('inside', {})
                    analysis['comparison'] = recognition_result.get('comparison', {})
                    
                    # Дополнительные метрики
                    if reference_text:
                        wer_outside = self.recognizer.calculate_wer(reference_text, analysis['outside'].get('text', ''))
                        wer_inside = self.recognizer.calculate_wer(reference_text, analysis['inside'].get('text', ''))
                        
                        analysis['comparison']['wer_to_reference'] = {
                            'outside': wer_outside,
                            'inside': wer_inside,
                            'difference': wer_inside - wer_outside
                        }
                    
                except Exception as e:
                    print(f"⚠️ Ошибка распознавания: {e}")
                    analysis['error'] = str(e)
        
        return analysis
    
    def _calculate_spectral_metrics(self, outside_data, inside_data):
        """Расчет спектральных метрик"""
        try:
            import scipy.signal as signal
            
            # Спектральная плотность мощности
            f_out, Pxx_out = signal.welch(outside_data, fs=44100, nperseg=1024)
            f_in, Pxx_in = signal.welch(inside_data, fs=44100, nperseg=1024)
            
            # Основные частоты
            dominant_freq_out = f_out[np.argmax(Pxx_out)]
            dominant_freq_in = f_in[np.argmax(Pxx_in)]
            
            # Энергия в речевом диапазоне (300-3400 Гц)
            speech_band = (300, 3400)
            mask_out = (f_out >= speech_band[0]) & (f_out <= speech_band[1])
            mask_in = (f_in >= speech_band[0]) & (f_in <= speech_band[1])
            
            speech_energy_out = np.trapz(Pxx_out[mask_out], f_out[mask_out])
            speech_energy_in = np.trapz(Pxx_in[mask_in], f_in[mask_in])
            total_energy_out = np.trapz(Pxx_out, f_out)
            total_energy_in = np.trapz(Pxx_in, f_in)
            
            return {
                'dominant_frequency': {
                    'outside': float(dominant_freq_out),
                    'inside': float(dominant_freq_in)
                },
                'speech_band_energy': {
                    'outside': float(speech_energy_out),
                    'inside': float(speech_energy_in),
                    'outside_ratio': float(speech_energy_out / total_energy_out) if total_energy_out > 0 else 0,
                    'inside_ratio': float(speech_energy_in / total_energy_in) if total_energy_in > 0 else 0
                }
            }
            
        except ImportError:
            print("⚠️ SciPy не установлен, пропускаем спектральный анализ")
            return {}
        except Exception as e:
            print(f"⚠️ Ошибка спектрального анализа: {e}")
            return {}
    
    def _integrate_analyses(self, audio_analysis, speech_analysis):
        """Интеграция аудио анализа и распознавания речи"""
        metrics = {
            'basic': {},
            'recognition': {},
            'composite_scores': {}
        }
        
        # Базовые метрики из аудио анализа
        if 'basic_metrics' in audio_analysis:
            metrics['basic'] = audio_analysis['basic_metrics']
        
        if 'level_comparison' in audio_analysis:
            metrics['basic']['attenuation_db'] = audio_analysis['level_comparison'].get('attenuation_db', 0)
            metrics['basic']['reduction_ratio'] = audio_analysis['level_comparison'].get('reduction_ratio', 0)
            
            # Качество изоляции на основе ослабления
            attenuation = metrics['basic'].get('attenuation_db', 0)
            if attenuation >= 45:
                metrics['basic']['isolation_quality'] = "отличная"
            elif attenuation >= 30:
                metrics['basic']['isolation_quality'] = "хорошая"
            elif attenuation >= 20:
                metrics['basic']['isolation_quality'] = "удовлетворительная"
            else:
                metrics['basic']['isolation_quality'] = "плохая"
        
        # Метрики распознавания
        if 'comparison' in speech_analysis:
            metrics['recognition'] = speech_analysis['comparison']
            
            # WER как показатель утечки
            wer = speech_analysis['comparison'].get('wer', 1.0)
            metrics['recognition']['leakage_level'] = 'высокая' if wer < 0.4 else 'средняя' if wer < 0.7 else 'низкая'
        
        # Композитные оценки
        composite = self._calculate_composite_scores(metrics)
        metrics['composite_scores'] = composite
        
        return metrics
    
    def _calculate_composite_scores(self, metrics):
        """Расчет композитных оценок"""
        scores = {}
        
        # Оценка изоляции на основе ослабления (0-100)
        attenuation = metrics['basic'].get('attenuation_db', 0)
        isolation_score = min(100, attenuation * 2)  # 50 дБ = 100 баллов
        
        # Оценка на основе WER
        wer = metrics['recognition'].get('wer', 1.0)
        wer_score = max(0, 100 - (wer * 100))  # WER 0% = 100 баллов, 100% = 0 баллов
        
        # Оценка на основе корреляции сигналов
        correlation = metrics['basic'].get('correlation', 0)
        correlation_score = max(0, 50 - (abs(correlation) * 100))  # Низкая корреляция = лучше
        
        # Итоговая оценка (взвешенная)
        total_score = (
            isolation_score * 0.5 +      # 50% за ослабление
            wer_score * 0.3 +           # 30% за WER
            correlation_score * 0.2      # 20% за корреляцию
        )
        
        scores['isolation_score'] = isolation_score
        scores['recognition_score'] = wer_score
        scores['correlation_score'] = correlation_score
        scores['total_score'] = total_score
        scores['grade'] = self._score_to_grade(total_score)
        
        return scores
    
    def _score_to_grade(self, score):
        """Преобразование баллов в оценку"""
        if score >= 90:
            return "Отлично (A)"
        elif score >= 75:
            return "Хорошо (B)"
        elif score >= 60:
            return "Удовлетворительно (C)"
        elif score >= 40:
            return "Неудовлетворительно (D)"
        else:
            return "Плохо (F)"
    
    def _create_basic_metrics(self, audio_analysis):
        """Создание базовых метрик если распознавание недоступно"""
        metrics = {
            'basic': {},
            'recognition': {'available': False},
            'composite_scores': {}
        }
        
        if 'basic_metrics' in audio_analysis:
            metrics['basic'] = audio_analysis['basic_metrics']
        
        if 'level_comparison' in audio_analysis:
            attenuation = audio_analysis['level_comparison'].get('attenuation_db', 0)
            metrics['basic']['attenuation_db'] = attenuation
            
            if attenuation >= 45:
                metrics['basic']['isolation_quality'] = "отличная"
            elif attenuation >= 30:
                metrics['basic']['isolation_quality'] = "хорошая"
            elif attenuation >= 20:
                metrics['basic']['isolation_quality'] = "удовлетворительная"
            else:
                metrics['basic']['isolation_quality'] = "плохая"
        
        return metrics
    
    def _calculate_overall_assessment(self, detailed_metrics):
        """Расчет итоговой оценки"""
        basic = detailed_metrics.get('basic', {})
        recognition = detailed_metrics.get('recognition', {})
        composite = detailed_metrics.get('composite_scores', {})
        
        # Вердикт на основе качества изоляции
        quality = basic.get('isolation_quality', 'неизвестно')
        
        if quality == "отличная":
            verdict = "ОТЛИЧНАЯ ИЗОЛЯЦИЯ"
            color = "green"
        elif quality == "хорошая":
            verdict = "ХОРОШАЯ ИЗОЛЯЦИЯ"
            color = "lightgreen"
        elif quality == "удовлетворительная":
            verdict = "СРЕДНЯЯ ИЗОЛЯЦИЯ"
            color = "yellow"
        elif quality == "плохая":
            verdict = "НЕДОСТАТОЧНАЯ ИЗОЛЯЦИЯ"
            color = "red"
        else:
            verdict = "АНАЛИЗ ВЫПОЛНЕН"
            color = "gray"
        
        # Учет результатов распознавания
        if recognition.get('leakage_detected', False):
            verdict += " (УТЕЧКА ОБНАРУЖЕНА)"
            color = "orange"
        
        # Сводка
        attenuation = basic.get('attenuation_db', 0)
        wer = recognition.get('wer', 'N/A')
        
        if isinstance(wer, (int, float)):
            wer_text = f"{wer:.1%}"
        else:
            wer_text = str(wer)
        
        summary = f"Звукоизоляция: {quality}. Снижение шума: {attenuation:.1f} дБ"
        
        if recognition.get('available', True) and isinstance(wer, (int, float)):
            summary += f", WER: {wer_text}"
        
        # Рекомендации
        recommendations = self._get_recommendations(basic, recognition)
        
        return {
            'verdict': verdict,
            'color': color,
            'quality': quality,
            'db_reduction': float(attenuation),
            'wer': wer_text,
            'composite_score': composite.get('total_score', 0),
            'grade': composite.get('grade', 'N/A'),
            'summary': summary,
            'recommendations': recommendations,
            'detailed_metrics_available': True
        }
    
    def _get_recommendations(self, basic, recognition):
        """Получение рекомендаций на основе анализа"""
        recommendations = []
        
        attenuation = basic.get('attenuation_db', 0)
        leakage = recognition.get('leakage_detected', False)
        wer = recognition.get('wer', 1.0)
        
        if attenuation < 20:
            recommendations.append("Усилить изоляцию стен и окон")
            recommendations.append("Установить звукопоглощающие материалы")
            recommendations.append("Проверить наличие щелей и зазоров")
        elif attenuation < 35:
            recommendations.append("Добавить уплотнители на двери и окна")
            recommendations.append("Рассмотреть ковровое покрытие")
        
        if leakage or (isinstance(wer, (int, float)) and wer < 0.5):
            recommendations.append("Обнаружена утечка речи - усилить звукоизоляцию")
            recommendations.append("Проверить целостность звукоизоляционных материалов")
        
        if not recommendations:
            recommendations.append("Изоляция соответствует нормам")
        
        return recommendations
    
    def _get_file_stats(self, filepath):
        """Получение статистики файла"""
        try:
            size = os.path.getsize(filepath) // 1024  # КБ
            return {'size_kb': size, 'exists': True}
        except:
            return {'size_kb': 0, 'exists': False}
    
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
    
    def set_recognition_engine(self, engine_name):
        """Установка движка распознавания"""
        if self.recognizer:
            try:
                from speech_recognizer import RecognitionEngine
                engine = RecognitionEngine(engine_name)
                return self.recognizer.set_engine(engine)
            except:
                print(f"⚠️ Не удалось установить движок: {engine_name}")
                return False
        return False