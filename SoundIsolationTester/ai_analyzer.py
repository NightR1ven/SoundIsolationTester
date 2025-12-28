# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
import numpy as np
from difflib import SequenceMatcher
import re

class EnhancedSoundIsolationAnalyzer:
    """Анализатор звукоизоляции для аттестации помещений"""
    
    def __init__(self):
        self.initialized = False
        
        try:
            import numpy as np
            self.np = np
            print("✅ NumPy загружен")
            self.initialized = True
        except ImportError as e:
            print(f"⚠️ NumPy не установлен: {e}")
            self.np = None
        
        # Инициализация распознавателя (если доступен)
        self.recognizer = None
        try:
            from speech_recognizer import MultiEngineSpeechRecognizer
            self.recognizer = MultiEngineSpeechRecognizer()
            print("✅ Модуль распознавания загружен")
        except ImportError as e:
            print(f"⚠️ Модуль распознавания недоступен: {e}")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки распознавателя: {e}")
    
    def analyze_with_audio_analysis(self, outside_audio_path, inside_audio_path, test_name, 
                               reference_text=None, enable_speech_recognition=True):
        """Анализ для аттестации звукоизоляции помещения"""
        try:
            analysis = {
                'test_name': test_name,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'analysis_type': 'room_isolation_assessment',
                'reference_text': reference_text,
                'file_paths': {
                    'inside': inside_audio_path,
                    'outside': outside_audio_path
                },
                'results': {
                    'audio_analysis': {},
                    'speech_recognition': {},
                    'detailed_metrics': {},
                    'overall_assessment': {},
                    'isolation_assessment': {}
                }
            }
        
            # 1. Базовый анализ аудио (громкость)
            print(f"🔊 Начинаю аудиоанализ...")
            audio_analysis = self._perform_audio_analysis(outside_audio_path, inside_audio_path)
            analysis['results']['audio_analysis'] = audio_analysis
            print(f"✅ Аудиоанализ завершен")
        
            # 2. Распознавание речи (если включено и доступно)
            if enable_speech_recognition and self.recognizer:
                print(f"🎤 Начинаю распознавание речи...")
                try:
                    speech_analysis = self._perform_speech_recognition(
                        outside_audio_path, inside_audio_path, reference_text
                    )
                    analysis['results']['speech_recognition'] = speech_analysis
                    print(f"✅ Распознавание речи завершено")
                
                    # 3. Оценка изоляции помещения
                    if reference_text:
                        print(f"📊 Оцениваю изоляцию помещения...")
                        isolation_assessment = self._assess_room_isolation(
                            speech_analysis, reference_text, audio_analysis
                        )
                        analysis['results']['isolation_assessment'] = isolation_assessment
                        print(f"✅ Оценка изоляции завершена")
                    
                    # 4. Интегрируем результаты
                    integrated = self._integrate_analyses(
                        audio_analysis, speech_analysis, 
                        analysis['results'].get('isolation_assessment')
                    )
                    analysis['results']['detailed_metrics'] = integrated
                    
                except Exception as e:
                    print(f"⚠️ Ошибка при распознавании речи: {e}")
                    # Если распознавание не удалось, используем только аудиоанализ
                    analysis['results']['detailed_metrics'] = self._create_basic_metrics(audio_analysis)
            else:
                print(f"ℹ️ Распознавание речи отключено или недоступно")
                analysis['results']['detailed_metrics'] = self._create_basic_metrics(audio_analysis)
        
            # 5. Итоговая оценка
            print(f"🏆 Формирую итоговую оценку...")
            overall = self._calculate_overall_assessment(
                analysis['results']['detailed_metrics'],
                analysis['results'].get('isolation_assessment')
            )
            analysis['results']['overall_assessment'] = overall
            print(f"✅ Анализ завершен успешно")
        
            return analysis
        
        except Exception as e:
            print(f"❌ Критическая ошибка анализа: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_report(test_name, str(e))
    
    def _assess_room_isolation(self, speech_analysis, reference_text, audio_analysis):
        """Оценка звукоизоляции помещения по разнице в распознавании"""
        assessment = {
            'inside_reference_check': {},   # Проверка эталона (внутри)
            'outside_isolation_check': {},  # Проверка изоляции (снаружи)
            'isolation_metrics': {}         # Метрики изоляции
        }
        
        try:
            # Получаем распознанные тексты
            inside_text = speech_analysis.get('inside', {}).get('text', '')
            outside_text = speech_analysis.get('outside', {}).get('text', '')
            inside_confidence = speech_analysis.get('inside', {}).get('confidence', 0)
            outside_confidence = speech_analysis.get('outside', {}).get('confidence', 0)
            
            print(f"📝 Внутренний текст: {inside_text[:50]}...")
            print(f"📝 Наружный текст: {outside_text[:50]}...")
            
            # 1. Проверка эталона (должен хорошо распознаваться)
            if reference_text and inside_text:
                inside_validation = self._validate_spoken_text(inside_text, reference_text, inside_confidence)
                assessment['inside_reference_check'] = inside_validation
                print(f"✅ Проверка эталона: {inside_validation.get('match_score', 0)*100:.1f}%")
            else:
                assessment['inside_reference_check'] = {
                    'valid': False,
                    'match_score': 0,
                    'error': 'Нет текста для проверки'
                }
            
            # 2. Оценка изоляции по распознаванию
            if inside_text and outside_text and reference_text:
                # Сходство с эталоном
                inside_similarity = self._calculate_text_similarity(reference_text, inside_text)
                outside_similarity = self._calculate_text_similarity(reference_text, outside_text)
                
                print(f"📊 Сходство внутри: {inside_similarity*100:.1f}%")
                print(f"📊 Сходство снаружи: {outside_similarity*100:.1f}%")
                
                # Эффективность изоляции (чем меньше снаружи, тем лучше)
                if inside_similarity > 0:
                    isolation_efficiency = 1 - (outside_similarity / inside_similarity)
                    # 0% = утечка полная, 100% = идеальная изоляция
                else:
                    isolation_efficiency = 0
                
                print(f"📊 Эффективность изоляции: {isolation_efficiency*100:.1f}%")
                
                # Потерянные слова
                ref_words = self._clean_and_split_text(reference_text)
                inside_words = self._clean_and_split_text(inside_text)
                outside_words = self._clean_and_split_text(outside_text)
                
                # Считаем слова, которые удалось распознать
                words_understood_inside = self._count_matching_words(ref_words, inside_words)
                words_understood_outside = self._count_matching_words(ref_words, outside_words)
                
                assessment['isolation_metrics'] = {
                    'inside_similarity': float(inside_similarity),
                    'outside_similarity': float(outside_similarity),
                    'isolation_efficiency': float(isolation_efficiency),
                    'estimated_attenuation_db': float(isolation_efficiency * 50),  # примерная оценка
                    'words_total': len(ref_words),
                    'words_understood_inside': words_understood_inside,
                    'words_understood_outside': words_understood_outside,
                    'words_lost': max(0, words_understood_inside - words_understood_outside),
                    'leakage_percentage': float(outside_similarity / inside_similarity * 100) if inside_similarity > 0 else 100.0
                }
            
            # 3. Оценка по громкости (из audio_analysis)
            if 'level_comparison' in audio_analysis:
                level_data = audio_analysis['level_comparison']
                inside_rms = level_data.get('inside_rms', 0)
                outside_rms = level_data.get('outside_rms', 0)
                
                # Правильный расчет ослабления для изоляции помещения
                # Источник ВНУТРИ, измеряем СНАРУЖИ
                if inside_rms > 0 and outside_rms > 0:
                    if inside_rms >= outside_rms:
                        attenuation_db = 20 * np.log10(inside_rms / outside_rms)  # ПРАВИЛЬНО!
                    else:
                        attenuation_db = -20 * np.log10(outside_rms / inside_rms)
                    
                    if 'isolation_metrics' in assessment:
                        assessment['isolation_metrics']['attenuation_db'] = float(attenuation_db)
                        assessment['isolation_metrics']['level_reduction_ratio'] = float(outside_rms / inside_rms)
                        assessment['isolation_metrics']['inside_level_db'] = float(20 * np.log10(inside_rms) if inside_rms > 0 else 0)
                        assessment['isolation_metrics']['outside_level_db'] = float(20 * np.log10(outside_rms) if outside_rms > 0 else 0)
                    else:
                        assessment['isolation_metrics'] = {
                            'attenuation_db': float(attenuation_db),
                            'level_reduction_ratio': float(outside_rms / inside_rms),
                            'inside_level_db': float(20 * np.log10(inside_rms) if inside_rms > 0 else 0),
                            'outside_level_db': float(20 * np.log10(outside_rms) if outside_rms > 0 else 0)
                        }
                    
                    print(f"🔊 Ослабление звука: {attenuation_db:.1f} дБ")
            
        except Exception as e:
            print(f"⚠️ Ошибка оценки изоляции: {e}")
            assessment['error'] = str(e)
        
        return assessment
    
    def _clean_and_split_text(self, text):
        """Очистка текста и разделение на слова"""
        if not text:
            return []
        
        # Удаляем знаки препинания, приводим к нижнему регистру
        cleaned = re.sub(r'[^\w\s]', '', str(text).lower())
        # Разделяем на слова, удаляем пустые
        words = [w.strip() for w in cleaned.split() if w.strip()]
        return words
    
    def _count_matching_words(self, ref_words, recognized_words):
        """Подсчет совпадающих слов с учетом частичных совпадений"""
        if not ref_words or not recognized_words:
            return 0
        
        matches = 0
        for ref_word in ref_words:
            for rec_word in recognized_words:
                # Полное совпадение
                if ref_word == rec_word:
                    matches += 1
                    break
                # Частичное совпадение (первые 3 буквы)
                elif len(ref_word) >= 3 and len(rec_word) >= 3:
                    if ref_word[:3] == rec_word[:3]:
                        matches += 0.5  # Частичный балл
                        break
        
        return matches
    
    def _calculate_text_similarity(self, text1, text2):
        """Расчет схожести текстов"""
        if not text1 or not text2:
            return 0.0
        
        try:
            # Используем SequenceMatcher для более точного сравнения
            similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
            return float(similarity)
        except:
            # Запасной метод
            words1 = self._clean_and_split_text(text1)
            words2 = self._clean_and_split_text(text2)
            
            if not words1:
                return 0.0
            
            matches = self._count_matching_words(words1, words2)
            return matches / len(words1)
    
    def _validate_spoken_text(self, recognized_text, reference_text, confidence):
        """Валидация произнесенного текста"""
        if not reference_text or not recognized_text:
            return {
                'valid': False, 
                'match_score': 0.0,
                'confidence': confidence,
                'reference': reference_text,
                'recognized': recognized_text,
                'error': 'Нет текста для сравнения'
            }
        
        try:
            match_score = self._calculate_text_similarity(reference_text, recognized_text)
            
            # Для эталона (внутри) требуется высокая точность
            # Минимум 60% совпадения и уверенность не ниже 0.5
            is_valid = match_score >= 0.6 and confidence >= 0.5
            
            return {
                'valid': is_valid,
                'match_score': float(match_score),
                'confidence': float(confidence),
                'reference': reference_text,
                'recognized': recognized_text,
                'validation_passed': is_valid
            }
        except Exception as e:
            return {
                'valid': False,
                'match_score': 0.0,
                'confidence': confidence,
                'error': str(e)
            }
    
    def _perform_audio_analysis(self, outside_path, inside_path):
        """Анализ аудио характеристик для изоляции помещения"""
        analysis = {
            'file_stats': {
                'outside': self._get_file_stats(outside_path),
                'inside': self._get_file_stats(inside_path)
            },
            'level_comparison': {},
            'spectral_analysis': {},
            'basic_metrics': {}
        }
        
        if self.initialized and self.np is not None:
            try:
                import wave
                
                # Чтение WAV файлов
                def read_wav_data(filepath):
                    with wave.open(filepath, 'rb') as wav:
                        frames = wav.readframes(wav.getnframes())
                        sample_width = wav.getsampwidth()
                        if sample_width == 2:
                            data = np.frombuffer(frames, dtype=np.int16)
                        elif sample_width == 4:
                            data = np.frombuffer(frames, dtype=np.int32)
                        else:
                            data = np.frombuffer(frames, dtype=np.uint8)
                        
                        # Нормализация
                        if data.dtype == np.int16:
                            data = data.astype(np.float32) / 32768.0
                        elif data.dtype == np.int32:
                            data = data.astype(np.float32) / 2147483648.0
                        else:
                            data = data.astype(np.float32) / 255.0
                        
                        return data
                
                print(f"📁 Чтение аудиофайлов...")
                inside_data = read_wav_data(inside_path)   # Источник ВНУТРИ
                outside_data = read_wav_data(outside_path) # Что вышло СНАРУЖИ
                
                print(f"📊 Анализирую уровни звука...")
                # Расчет RMS (среднеквадратичное значение)
                inside_rms = np.sqrt(np.mean(inside_data**2))
                outside_rms = np.sqrt(np.mean(outside_data**2))
                
                # Правильный расчет ослабления для изоляции помещения
                # Источник ВНУТРИ, измеряем СНАРУЖИ
                if inside_rms > 0 and outside_rms > 0:
                    if inside_rms >= outside_rms:
                        attenuation_db = 20 * np.log10(inside_rms / outside_rms)  # ПРАВИЛЬНО!
                        reduction_ratio = outside_rms / inside_rms  # Какая часть звука вышла
                    else:
                        attenuation_db = -20 * np.log10(outside_rms / inside_rms)
                        reduction_ratio = 1.0  # Аномалия: снаружи громче
                else:
                    attenuation_db = 0
                    reduction_ratio = 0
                
                # Уровни в дБFS (относительно полной шкалы)
                inside_level_db = 20 * np.log10(inside_rms) if inside_rms > 0 else -np.inf
                outside_level_db = 20 * np.log10(outside_rms) if outside_rms > 0 else -np.inf
                
                analysis['level_comparison'] = {
                    'inside_rms': float(inside_rms),      # Уровень источника ВНУТРИ
                    'outside_rms': float(outside_rms),    # Уровень СНАРУЖИ
                    'attenuation_db': float(attenuation_db),  # Ослабление звука
                    'reduction_ratio': float(reduction_ratio), # Доля звука, вышедшего наружу
                    'sound_reduction_index': float(attenuation_db),  # Индекс звукоизоляции
                    'inside_level_db': float(inside_level_db),
                    'outside_level_db': float(outside_level_db),
                    'level_difference_db': float(inside_level_db - outside_level_db)
                }
                
                # Дополнительные метрики
                analysis['basic_metrics'] = {
                    'inside_max': float(np.max(np.abs(inside_data))),
                    'outside_max': float(np.max(np.abs(outside_data))),
                    'inside_mean': float(np.mean(np.abs(inside_data))),
                    'outside_mean': float(np.mean(np.abs(outside_data))),
                    'inside_std': float(np.std(inside_data)),
                    'outside_std': float(np.std(outside_data)),
                    'inside_dynamic_range': float(20 * np.log10(np.max(np.abs(inside_data)) / (np.std(inside_data) + 1e-10))),
                    'outside_dynamic_range': float(20 * np.log10(np.max(np.abs(outside_data)) / (np.std(outside_data) + 1e-10)))
                }
                
                # Расчет корреляции (для очень коротких файлов может быть проблема)
                min_len = min(len(inside_data), len(outside_data))
                if min_len > 100:  # Нужно достаточно данных
                    try:
                        correlation = np.corrcoef(
                            inside_data[:min_len], 
                            outside_data[:min_len]
                        )[0, 1]
                        analysis['basic_metrics']['correlation'] = float(correlation)
                    except:
                        analysis['basic_metrics']['correlation'] = 0.0
                else:
                    analysis['basic_metrics']['correlation'] = 0.0
                
                print(f"✅ Аудиоанализ: внутри {inside_rms:.4f}, снаружи {outside_rms:.4f}, ослабление {attenuation_db:.1f} дБ")
                
            except Exception as e:
                print(f"⚠️ Ошибка продвинутого аудиоанализа: {e}")
                import traceback
                traceback.print_exc()
        
        return analysis
    
    def _perform_speech_recognition(self, outside_path, inside_path, reference_text=None):
        """Распознавание речи в аудиофайлах"""
        analysis = {
            'outside': {},
            'inside': {},
            'comparison': {},
            'engine_info': {}
        }
        
        if self.recognizer:
            try:
                print(f"🔍 Начинаю распознавание речи...")
                
                # Получаем информацию о текущем движке
                if hasattr(self.recognizer, 'current_engine'):
                    engine = self.recognizer.current_engine
                    if engine:
                        analysis['engine_info'] = {
                            'name': str(engine),
                            'type': 'whisper' if 'whisper' in str(engine).lower() else 'vosk'
                        }
                
                # Распознавание пары файлов
                recognition_result = self.recognizer.analyze_pair(outside_path, inside_path, reference_text)
                
                # Заполняем результаты
                if recognition_result:
                    analysis['outside'] = recognition_result.get('outside', {})
                    analysis['inside'] = recognition_result.get('inside', {})
                    analysis['comparison'] = recognition_result.get('comparison', {})
                    
                    print(f"✅ Распознавание завершено")
                    print(f"   Внутри: {analysis['inside'].get('text', '')[:50]}...")
                    print(f"   Снаружи: {analysis['outside'].get('text', '')[:50]}...")
                    if 'wer' in analysis['comparison']:
                        print(f"   WER: {analysis['comparison'].get('wer', 0):.2%}")
                else:
                    print(f"⚠️ Результат распознавания пустой")
                    analysis['error'] = 'Результат распознавания пустой'
                    
            except Exception as e:
                print(f"❌ Ошибка распознавания речи: {e}")
                analysis['error'] = str(e)
        
        return analysis
    
    def _integrate_analyses(self, audio_analysis, speech_analysis, isolation_assessment=None):
        """Интеграция анализов для оценки изоляции помещения"""
        metrics = {
            'basic': {},
            'recognition': {},
            'isolation_metrics': {},
            'composite_scores': {}
        }
        
        # Базовые метрики из аудио анализа
        if 'basic_metrics' in audio_analysis:
            metrics['basic'] = audio_analysis['basic_metrics']
        
        if 'level_comparison' in audio_analysis:
            level_data = audio_analysis['level_comparison']
            attenuation = level_data.get('attenuation_db', 0)
            
            metrics['basic']['attenuation_db'] = attenuation
            metrics['basic']['sound_reduction_index'] = attenuation
            
            # Оценка качества изоляции по ослаблению
            if attenuation >= 50:
                metrics['basic']['isolation_quality'] = "отличная"
                metrics['basic']['isolation_score'] = 90 + min((attenuation - 50), 10)
            elif attenuation >= 40:
                metrics['basic']['isolation_quality'] = "хорошая"
                metrics['basic']['isolation_score'] = 70 + min((attenuation - 40) * 2, 20)
            elif attenuation >= 30:
                metrics['basic']['isolation_quality'] = "удовлетворительная"
                metrics['basic']['isolation_score'] = 50 + min((attenuation - 30) * 2, 20)
            elif attenuation >= 20:
                metrics['basic']['isolation_quality'] = "плохая"
                metrics['basic']['isolation_score'] = 30 + min((attenuation - 20) * 2, 20)
            else:
                metrics['basic']['isolation_quality'] = "очень плохая"
                metrics['basic']['isolation_score'] = attenuation * 1.5
        
        # Метрики распознавания
        if 'comparison' in speech_analysis:
            metrics['recognition'] = speech_analysis['comparison']
            
            # WER как показатель утечки речи
            wer = speech_analysis['comparison'].get('wer', 1.0)
            if wer < 0.4:
                metrics['recognition']['speech_leakage'] = 'высокая'
            elif wer < 0.7:
                metrics['recognition']['speech_leakage'] = 'средняя'
            else:
                metrics['recognition']['speech_leakage'] = 'низкая'
            
            metrics['recognition']['leakage_detected'] = wer < 0.5
        
        # Метрики изоляции
        if isolation_assessment and 'isolation_metrics' in isolation_assessment:
            iso_metrics = isolation_assessment['isolation_metrics']
            metrics['isolation_metrics'] = iso_metrics
            
            # Комбинированная оценка изоляции
            if 'attenuation_db' in iso_metrics and 'isolation_efficiency' in iso_metrics:
                # Нормализуем ослабление (0-60 дБ -> 0-1)
                attenuation_norm = min(iso_metrics['attenuation_db'] / 60, 1.0)
                efficiency_norm = iso_metrics['isolation_efficiency']
                
                combined_score = (attenuation_norm * 0.6 + efficiency_norm * 0.4) * 100
                metrics['isolation_metrics']['combined_isolation_score'] = combined_score
        
        # Композитные оценки
        composite = self._calculate_composite_scores(metrics)
        metrics['composite_scores'] = composite
        
        return metrics
    
    def _calculate_composite_scores(self, metrics):
        """Расчет композитных оценок"""
        scores = {}
        
        # Оценка изоляции на основе ослабления (0-100)
        attenuation = metrics['basic'].get('attenuation_db', 0)
        isolation_score = min(100, max(0, attenuation * 2))  # 50 дБ = 100 баллов
        
        # Оценка на основе WER (если есть)
        wer = metrics['recognition'].get('wer', 1.0)
        wer_score = max(0, 100 - (wer * 100))  # WER 0% = 100 баллов, 100% = 0 баллов
        
        # Оценка на основе эффективности изоляции (если есть)
        iso_efficiency = metrics['isolation_metrics'].get('isolation_efficiency', 0.5)
        efficiency_score = iso_efficiency * 100
        
        # Итоговая оценка (взвешенная)
        total_score = (
            isolation_score * 0.4 +          # 40% за ослабление
            wer_score * 0.3 +               # 30% за WER
            efficiency_score * 0.3          # 30% за эффективность
        )
        
        scores['isolation_score'] = isolation_score
        scores['recognition_score'] = wer_score
        scores['efficiency_score'] = efficiency_score
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
    
    def _calculate_overall_assessment(self, detailed_metrics, isolation_assessment=None):
        """Расчет итоговой оценки для аттестации помещения"""
        try:
            basic = detailed_metrics.get('basic', {})
            isolation_metrics = detailed_metrics.get('isolation_metrics', {})
            composite = detailed_metrics.get('composite_scores', {})
            
            # Ключевые метрики
            attenuation = basic.get('attenuation_db', 0)
            isolation_score = composite.get('total_score', 0)
            isolation_quality = basic.get('isolation_quality', 'неизвестно')
            
            # Вердикт на основе ослабления звука
            if attenuation >= 50:
                verdict = "ОТЛИЧНАЯ ЗВУКОИЗОЛЯЦИЯ"
                color = "darkgreen"
            elif attenuation >= 40:
                verdict = "ХОРОШАЯ ЗВУКОИЗОЛЯЦИЯ"
                color = "green"
            elif attenuation >= 30:
                verdict = "УДОВЛЕТВОРИТЕЛЬНАЯ ИЗОЛЯЦИЯ"
                color = "orange"
            elif attenuation >= 20:
                verdict = "СЛАБАЯ ЗВУКОИЗОЛЯЦИЯ"
                color = "red"
            else:
                verdict = "НЕЭФФЕКТИВНАЯ ИЗОЛЯЦИЯ"
                color = "darkred"
            
            # Проверка эталона
            if isolation_assessment and 'inside_reference_check' in isolation_assessment:
                inside_check = isolation_assessment['inside_reference_check']
                if not inside_check.get('valid', True):
                    verdict += " (ПРОБЛЕМА С ЭТАЛОНОМ)"
                    color = "purple"
            
            # Сводка
            summary_parts = []
            summary_parts.append(f"Ослабление звука: {attenuation:.1f} дБ")
            
            if 'isolation_efficiency' in isolation_metrics:
                efficiency = isolation_metrics['isolation_efficiency'] * 100
                summary_parts.append(f"Эффективность изоляции: {efficiency:.0f}%")
            
            if 'words_lost' in isolation_metrics and 'words_total' in isolation_metrics:
                words_lost = isolation_metrics['words_lost']
                words_total = isolation_metrics['words_total']
                if words_total > 0:
                    summary_parts.append(f"Слов потеряно: {words_lost}/{words_total}")
            
            summary = ", ".join(summary_parts)
            
            # Рекомендации
            recommendations = self._get_recommendations_for_isolation(basic, isolation_metrics)
            
            return {
                'verdict': verdict,
                'color': color,
                'quality': isolation_quality,
                'attenuation_db': float(attenuation),
                'isolation_score': float(isolation_score),
                'composite_grade': composite.get('grade', 'Н/Д'),
                'summary': summary,
                'recommendations': recommendations,
                'detailed_metrics_available': True
            }
            
        except Exception as e:
            print(f"⚠️ Ошибка расчета итоговой оценки: {e}")
            return {
                'verdict': 'ОШИБКА АНАЛИЗА',
                'color': 'red',
                'summary': f'Ошибка: {str(e)[:100]}',
                'recommendations': ['Проверьте входные данные', 'Убедитесь в корректности аудиофайлов']
            }
    
    def _get_recommendations_for_isolation(self, basic, isolation_metrics):
        """Рекомендации по улучшению звукоизоляции"""
        recommendations = []
        
        attenuation = basic.get('attenuation_db', 0)
        efficiency = isolation_metrics.get('isolation_efficiency', 0)
        words_lost = isolation_metrics.get('words_lost', 0)
        
        # Рекомендации по ослаблению
        if attenuation < 30:
            recommendations.append("Усилить изоляцию стен и перекрытий")
            recommendations.append("Установить звукопоглощающие материалы (минеральная вата, акустические панели)")
            recommendations.append("Проверить герметичность окон и дверей, установить уплотнители")
        
        if 20 <= attenuation < 35:
            recommendations.append("Рассмотреть установку звукоизоляционных мембран")
            recommendations.append("Добавить ковровое покрытие для снижения ударного шума")
        
        # Рекомендации по утечке речи
        if efficiency < 0.5:  # Меньше 50% эффективности
            recommendations.append("Обнаружена значительная утечка речи - требуется усиление изоляции")
        
        if words_lost > 0:
            recommendations.append(f"Обнаружена утечка {words_lost} слов - рекомендуется дополнительная звукоизоляция")
        
        # Общие рекомендации
        if attenuation >= 40 and efficiency >= 0.7:
            recommendations.append("Изоляция соответствует нормам для жилых помещений")
        
        if attenuation >= 50:
            recommendations.append("Отличная изоляция! Соответствует требованиям для конференц-залов")
        
        # Если рекомендаций нет, добавить стандартные
        if not recommendations:
            recommendations.append("Провести дополнительные измерения в разных точках помещения")
            recommendations.append("Рассмотреть возможность профессиональной акустической экспертизы")
        
        return recommendations
    
    def _create_basic_metrics(self, audio_analysis):
        """Создание базовых метрик если распознавание недоступно"""
        metrics = {
            'basic': {},
            'recognition': {'available': False},
            'isolation_metrics': {'available': False},
            'composite_scores': {}
        }
        
        if 'basic_metrics' in audio_analysis:
            metrics['basic'] = audio_analysis['basic_metrics']
        
        if 'level_comparison' in audio_analysis:
            attenuation = audio_analysis['level_comparison'].get('attenuation_db', 0)
            metrics['basic']['attenuation_db'] = attenuation
            
            if attenuation >= 45:
                metrics['basic']['isolation_quality'] = "отличная"
            elif attenuation >= 35:
                metrics['basic']['isolation_quality'] = "хорошая"
            elif attenuation >= 25:
                metrics['basic']['isolation_quality'] = "удовлетворительная"
            else:
                metrics['basic']['isolation_quality'] = "плохая"
        
        return metrics
    
    def _get_file_stats(self, filepath):
        """Получение статистики файла"""
        try:
            size_kb = os.path.getsize(filepath) // 1024
            exists = os.path.exists(filepath)
            
            # Получаем время создания/модификации
            mtime = os.path.getmtime(filepath)
            from datetime import datetime
            mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                'size_kb': size_kb,
                'exists': exists,
                'modified': mod_time,
                'filename': os.path.basename(filepath)
            }
        except Exception as e:
            return {
                'size_kb': 0,
                'exists': False,
                'error': str(e)
            }
    
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
                    'recommendations': [
                        'Проверьте аудиофайлы',
                        'Убедитесь, что файлы не повреждены',
                        'Проверьте установку всех зависимостей'
                    ],
                    'summary': f'Произошла ошибка при анализе: {error_message[:100]}'
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
            except Exception as e:
                print(f"⚠️ Не удалось установить движок {engine_name}: {e}")
                return False
        return False