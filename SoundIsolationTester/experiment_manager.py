# -*- coding: utf-8 -*-
import os
import json
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
import seaborn as sns

@dataclass
class ExperimentConfig:
    """Конфигурация эксперимента"""
    name: str
    description: str
    audio_pairs: List[Dict]  # Список путей к аудиофайлам
    reference_texts: Optional[Dict]  # Референсные тексты
    engines_to_test: List[str]  # Движки для тестирования
    enable_spoof_check: bool = True
    output_dir: str = "experiments"

class ExperimentManager:
    """Менеджер для массового тестирования"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.results = []
        self.current_experiment = None
        
    def run_experiment(self, config: ExperimentConfig):
        """Запуск массового тестирования"""
        self.current_experiment = config
        os.makedirs(config.output_dir, exist_ok=True)
        
        print(f"🧪 Запуск эксперимента: {config.name}")
        print(f"📊 Тестируемых пар: {len(config.audio_pairs)}")
        print(f"🎯 Движки: {config.engines_to_test}")
        
        all_results = []
        
        for engine in config.engines_to_test:
            print(f"\n🔧 Тестирование с движком: {engine}")
            self.analyzer.set_recognition_engine(engine)
            
            for i, audio_pair in enumerate(config.audio_pairs):
                print(f"  Тест {i+1}/{len(config.audio_pairs)}: {audio_pair.get('name', f'test_{i}')}")
                
                outside_path = audio_pair.get('outside')
                inside_path = audio_pair.get('inside')
                test_name = audio_pair.get('name', f'test_{i}_{engine}')
                reference = config.reference_texts.get(test_name) if config.reference_texts else None
                
                if os.path.exists(outside_path) and os.path.exists(inside_path):
                    analysis = self.analyzer.analyze_with_audio_analysis(
                        outside_path, inside_path, test_name,
                        reference, config.enable_spoof_check
                    )
                    
                    # Добавляем информацию о движке
                    analysis['experiment_info'] = {
                        'engine': engine,
                        'pair_name': audio_pair.get('name'),
                        'experiment': config.name
                    }
                    
                    all_results.append(analysis)
                    
                    # Сохраняем индивидуальный отчет
                    self._save_individual_report(analysis, config.output_dir)
                else:
                    print(f"  ⚠️ Файлы не найдены для теста {test_name}")
        
        # Сохраняем сводный отчет
        summary = self._generate_experiment_summary(all_results, config)
        self._save_experiment_summary(summary, config)
        
        # Генерация графиков
        self._generate_experiment_plots(all_results, config)
        
        print(f"\n✅ Эксперимент завершен!")
        print(f"📁 Результаты сохранены в: {config.output_dir}")
        
        return all_results
    
    def _save_individual_report(self, analysis, output_dir):
        """Сохранение индивидуального отчета"""
        try:
            filename = f"{analysis['test_name']}_report.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Ошибка сохранения отчета: {e}")
    
    def _generate_experiment_summary(self, all_results, config):
        """Генерация сводного отчета по эксперименту"""
        summary = {
            'experiment_name': config.name,
            'description': config.description,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'config': {
                'engines_tested': config.engines_to_test,
                'total_pairs': len(config.audio_pairs),
                'enable_spoof_check': config.enable_spoof_check
            },
            'statistics': {},
            'engine_comparison': {},
            'detailed_results': []
        }
        
        # Группировка по движкам
        engine_results = {}
        for result in all_results:
            engine = result.get('experiment_info', {}).get('engine', 'unknown')
            if engine not in engine_results:
                engine_results[engine] = []
            engine_results[engine].append(result)
        
        # Статистика по каждому движку
        for engine, results in engine_results.items():
            attenuations = []
            valid_tests = 0
            leakage_count = 0
            
            for result in results:
                overall = result.get('results', {}).get('overall_assessment', {})
                metrics = result.get('results', {}).get('detailed_metrics', {}).get('basic', {})
                rec_metrics = result.get('results', {}).get('detailed_metrics', {}).get('recognition', {})
                
                attenuations.append(metrics.get('attenuation_db', 0))
                
                # Проверка валидности
                validation_score = overall.get('validation_score', 1.0)
                if validation_score >= 0.7:
                    valid_tests += 1
                
                # Утечки
                if rec_metrics and rec_metrics.get('leakage_detected', False):
                    leakage_count += 1
            
            summary['engine_comparison'][engine] = {
                'tests_count': len(results),
                'valid_tests': valid_tests,
                'valid_percentage': (valid_tests / len(results) * 100) if results else 0,
                'leakage_detected': leakage_count,
                'avg_attenuation_db': float(np.mean(attenuations)) if attenuations else 0,
                'std_attenuation_db': float(np.std(attenuations)) if len(attenuations) > 1 else 0
            }
        
        # Общая статистика
        all_attenuations = []
        all_validation_scores = []
        
        for result in all_results:
            overall = result.get('results', {}).get('overall_assessment', {})
            metrics = result.get('results', {}).get('detailed_metrics', {}).get('basic', {})
            
            all_attenuations.append(metrics.get('attenuation_db', 0))
            all_validation_scores.append(overall.get('validation_score', 1.0))
            
            # Детализированные результаты
            detailed = {
                'test_name': result['test_name'],
                'engine': result.get('experiment_info', {}).get('engine'),
                'attenuation_db': metrics.get('attenuation_db', 0),
                'isolation_quality': metrics.get('isolation_quality', 'unknown'),
                'validation_score': overall.get('validation_score', 1.0),
                'timestamp': result['timestamp']
            }
            summary['detailed_results'].append(detailed)
        
        summary['statistics'] = {
            'total_tests': len(all_results),
            'avg_attenuation_db': float(np.mean(all_attenuations)) if all_attenuations else 0,
            'avg_validation_score': float(np.mean(all_validation_scores)) if all_validation_scores else 0,
            'tests_by_quality': self._count_by_quality([r.get('results', {}).get('detailed_metrics', {}).get('basic', {}) 
                                                        for r in all_results])
        }
        
        return summary
    
    def _count_by_quality(self, metrics_list):
        """Подсчет тестов по качеству"""
        qualities = {}
        for metrics in metrics_list:
            quality = metrics.get('isolation_quality', 'unknown')
            qualities[quality] = qualities.get(quality, 0) + 1
        return qualities
    
    def _save_experiment_summary(self, summary, config):
        """Сохранение сводного отчета"""
        try:
            # JSON отчет
            json_path = os.path.join(config.output_dir, f"{config.name}_summary.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            # CSV отчет
            csv_path = os.path.join(config.output_dir, f"{config.name}_summary.csv")
            df_data = []
            
            for result in summary['detailed_results']:
                df_data.append({
                    'test_name': result['test_name'],
                    'engine': result['engine'],
                    'attenuation_db': result['attenuation_db'],
                    'isolation_quality': result['isolation_quality'],
                    'validation_score': result['validation_score'],
                    'timestamp': result['timestamp']
                })
            
            if df_data:
                df = pd.DataFrame(df_data)
                df.to_csv(csv_path, index=False, encoding='utf-8')
            
            print(f"📊 Сводный отчет сохранен: {json_path}")
            print(f"📊 CSV отчет сохранен: {csv_path}")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения сводного отчета: {e}")
    
    def _generate_experiment_plots(self, all_results, config):
        """Генерация графиков по результатам эксперимента"""
        try:
            plots_dir = os.path.join(config.output_dir, "plots")
            os.makedirs(plots_dir, exist_ok=True)
            
            # Подготовка данных
            plot_data = []
            for result in all_results:
                engine = result.get('experiment_info', {}).get('engine', 'unknown')
                metrics = result.get('results', {}).get('detailed_metrics', {}).get('basic', {})
                overall = result.get('results', {}).get('overall_assessment', {})
                
                plot_data.append({
                    'engine': engine,
                    'attenuation_db': metrics.get('attenuation_db', 0),
                    'validation_score': overall.get('validation_score', 1.0),
                    'quality': metrics.get('isolation_quality', 'unknown')
                })
            
            if not plot_data:
                return
            
            df = pd.DataFrame(plot_data)
            
            # 1. Boxplot по движкам
            plt.figure(figsize=(10, 6))
            sns.boxplot(x='engine', y='attenuation_db', data=df)
            plt.title(f'Распределение звукоизоляции по движкам\nЭксперимент: {config.name}')
            plt.xlabel('Движок распознавания')
            plt.ylabel('Ослабление, дБ')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(plots_dir, 'attenuation_by_engine.png'), dpi=150)
            plt.close()
            
            # 2. Scatter plot
            plt.figure(figsize=(10, 6))
            scatter = plt.scatter(
                df['attenuation_db'], 
                df['validation_score'] * 100,
                c=[self._quality_to_color(q) for q in df['quality']],
                alpha=0.6
            )
            plt.xlabel('Ослабление, дБ')
            plt.ylabel('Оценка валидности, %')
            plt.title(f'Соотношение ослабления и валидности тестов\n{config.name}')
            
            # Легенда
            qualities = df['quality'].unique()
            handles = [plt.Line2D([0], [0], marker='o', color='w', 
                                 markerfacecolor=self._quality_to_color(q), markersize=10) 
                      for q in qualities]
            plt.legend(handles, qualities, title='Качество')
            
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(plots_dir, 'attenuation_vs_validation.png'), dpi=150)
            plt.close()
            
            # 3. Bar chart средних значений
            engine_stats = df.groupby('engine')['attenuation_db'].agg(['mean', 'std', 'count']).reset_index()
            
            plt.figure(figsize=(10, 6))
            bars = plt.bar(engine_stats['engine'], engine_stats['mean'], 
                          yerr=engine_stats['std'], capsize=5)
            
            plt.xlabel('Движок распознавания')
            plt.ylabel('Среднее ослабление, дБ')
            plt.title(f'Среднее ослабление по движкам\n{config.name}')
            plt.xticks(rotation=45)
            
            # Добавление значений на столбцы
            for bar, count in zip(bars, engine_stats['count']):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'n={count}', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig(os.path.join(plots_dir, 'average_attenuation.png'), dpi=150)
            plt.close()
            
            print(f"📈 Графики сохранены в: {plots_dir}")
            
        except Exception as e:
            print(f"⚠️ Ошибка генерации графиков: {e}")
    
    def _quality_to_color(self, quality):
        """Преобразование качества в цвет"""
        color_map = {
            'отличная': 'green',
            'хорошая': 'lightgreen',
            'удовлетворительная': 'yellow',
            'плохая': 'red',
            'unknown': 'gray'
        }
        return color_map.get(quality, 'gray')