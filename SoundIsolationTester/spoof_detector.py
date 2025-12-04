# -*- coding: utf-8 -*-
import numpy as np
import librosa
from scipy import signal
import warnings
warnings.filterwarnings('ignore')

class SpoofingDetector:
    """Детектор спуфинг-атак для системы тестирования звукоизоляции"""
    
    def __init__(self):
        self.speech_band = [300, 3400]  # Речевой диапазон Гц
        self.noise_types = {
            'music': {'centroid_range': [100, 5000], 'bandwidth': 3000},
            'construction': {'centroid_range': [50, 500], 'bandwidth': 2000},
            'traffic': {'centroid_range': [50, 1000], 'bandwidth': 1500}
        }
    
    def analyze_for_spoofing(self, audio_path, sr=None):
        """Анализ аудио на признаки спуфинг-атаки"""
        try:
            y, sr = librosa.load(audio_path, sr=sr)
            
            results = {
                'is_spoofing_suspected': False,
                'suspected_attack_type': None,
                'confidence': 0.0,
                'metrics': {},
                'warnings': []
            }
            
            # 1. Анализ уровня громкости
            rms = np.sqrt(np.mean(y**2))
            results['metrics']['rms'] = float(rms)
            
            if rms < 0.001:
                results['warnings'].append("Очень низкий уровень сигнала - возможна попытка скрытой речи")
                results['is_spoofing_suspected'] = True
                results['suspected_attack_type'] = 'low_volume_mask'
                results['confidence'] = 0.7
            
            # 2. Анализ спектральных характеристик
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            
            mean_centroid = np.mean(spectral_centroid)
            mean_bandwidth = np.mean(spectral_bandwidth)
            
            results['metrics']['spectral_centroid'] = float(mean_centroid)
            results['metrics']['spectral_bandwidth'] = float(mean_bandwidth)
            
            # 3. Проверка на речеподобность
            speech_likeness = self._check_speech_likeness(y, sr)
            results['metrics']['speech_likeness'] = speech_likeness
            
            if speech_likeness < 0.3 and rms > 0.01:
                results['warnings'].append("Высокий уровень звука, но низкая речеподобность - возможен искусственный шум")
                results['is_spoofing_suspected'] = True
                results['suspected_attack_type'] = 'artificial_noise'
                results['confidence'] = 0.8
            
            # 4. Анализ стабильности сигнала
            stability_score = self._analyze_signal_stability(y)
            results['metrics']['signal_stability'] = stability_score
            
            if stability_score > 0.9:
                results['warnings'].append("Высокая стабильность сигнала - возможен искусственный источник")
            
            # 5. Анализ на наличие музыкальных паттернов
            is_music = self._detect_music_patterns(y, sr)
            if is_music:
                results['warnings'].append("Обнаружены музыкальные паттерны")
                results['is_spoofing_suspected'] = True
                results['suspected_attack_type'] = 'music_masking'
                results['confidence'] = 0.9
            
            return results
            
        except Exception as e:
            print(f"❌ Ошибка анализа спуфинга: {e}")
            return None
    
    def _check_speech_likeness(self, y, sr):
        """Оценка речеподобности сигнала"""
        # Энтропия спектра
        S = np.abs(librosa.stft(y))
        spectral_flatness = librosa.feature.spectral_flatness(S=S)[0]
        
        # ZCR для речи
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        
        # Энергия в речевом диапазоне
        fft = np.fft.fft(y)
        freqs = np.fft.fftfreq(len(y), 1/sr)
        
        speech_mask = (np.abs(freqs) >= self.speech_band[0]) & (np.abs(freqs) <= self.speech_band[1])
        speech_energy = np.sum(np.abs(fft[speech_mask])**2)
        total_energy = np.sum(np.abs(fft)**2)
        
        if total_energy > 0:
            speech_ratio = speech_energy / total_energy
        else:
            speech_ratio = 0
        
        # Комбинированная оценка
        likeness_score = (0.4 * (1 - np.mean(spectral_flatness)) + 
                         0.3 * (np.mean(zcr) / 0.1) + 
                         0.3 * speech_ratio)
        
        return min(max(likeness_score, 0), 1)
    
    def _analyze_signal_stability(self, y):
        """Анализ стабильности сигнала во времени"""
        # Разделяем на сегменты
        segment_length = len(y) // 10
        if segment_length < 100:
            return 0
        
        segments = []
        for i in range(0, len(y), segment_length):
            if i + segment_length <= len(y):
                segments.append(y[i:i+segment_length])
        
        if len(segments) < 2:
            return 0
        
        # Сравниваем RMS между сегментами
        rms_values = [np.sqrt(np.mean(seg**2)) for seg in segments]
        rms_std = np.std(rms_values)
        rms_mean = np.mean(rms_values)
        
        if rms_mean > 0:
            stability = 1 - min(rms_std / rms_mean, 1)
        else:
            stability = 0
        
        return stability
    
    def _detect_music_patterns(self, y, sr):
        """Обнаружение музыкальных паттернов"""
        # Анализ гармоник
        harmonic, percussive = librosa.effects.hpss(y)
        
        # Соотношение гармоник/перкуссия
        harmonic_energy = np.sum(harmonic**2)
        percussive_energy = np.sum(percussive**2)
        total_energy = harmonic_energy + percussive_energy
        
        if total_energy > 0:
            harmonic_ratio = harmonic_energy / total_energy
            
            # Музыка обычно имеет высокое соотношение гармоник
            if harmonic_ratio > 0.7:
                return True
        
        # Анализ на ритмические паттерны
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        
        # Регулярный ритм может указывать на музыку
        if len(beats) > 3:
            beat_intervals = np.diff(beats)
            beat_std = np.std(beat_intervals)
            
            if beat_std < 5:  # Очень регулярные биты
                return True
        
        return False
    
    def compare_pair_for_spoofing(self, outside_path, inside_path):
        """Сравнение пары аудио для выявления спуфинга"""
        outside_analysis = self.analyze_for_spoofing(outside_path)
        inside_analysis = self.analyze_for_spoofing(inside_path)
        
        if not outside_analysis or not inside_analysis:
            return None
        
        comparison = {
            'outside': outside_analysis,
            'inside': inside_analysis,
            'anomalies': [],
            'is_test_valid': True,
            'validation_score': 1.0
        }
        
        # Проверка на несоответствия
        outside_rms = outside_analysis['metrics'].get('rms', 0)
        inside_rms = inside_analysis['metrics'].get('rms', 0)
        
        # Если снаружи громко, а внутри тихо - подозрительно
        if outside_rms > 0.05 and inside_rms < 0.001:
            comparison['anomalies'].append("Высокий внешний шум с очень низким внутренним уровнем")
            comparison['validation_score'] *= 0.5
        
        # Если снаружи не речеподобный сигнал
        outside_speech = outside_analysis['metrics'].get('speech_likeness', 0)
        if outside_speech < 0.2:
            comparison['anomalies'].append("Внешний сигнал не похож на речь")
            comparison['validation_score'] *= 0.7
        
        # Если подозревается спуфинг в любом из каналов
        if outside_analysis['is_spoofing_suspected']:
            comparison['anomalies'].append(f"Подозрение на спуфинг снаружи: {outside_analysis['suspected_attack_type']}")
            comparison['validation_score'] *= 0.3
        
        if inside_analysis['is_spoofing_suspected']:
            comparison['anomalies'].append(f"Подозрение на спуфинг внутри: {inside_analysis['suspected_attack_type']}")
            comparison['validation_score'] *= 0.3
        
        if comparison['validation_score'] < 0.5:
            comparison['is_test_valid'] = False
        
        return comparison



