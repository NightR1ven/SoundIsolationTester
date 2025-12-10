# Silero V3 - инструкция по установке

Silero V3 - это современная библиотека для распознавания речи с поддержкой русского языка.

## Установка:
pip install silero torch torchaudio

## Модели:
Модели автоматически загружаются при первом запуске через torch.hub.
Русская модель: 'silero_stt' (язык: 'ru')

## Путь к кэшу моделей:
~/.cache/torch/hub/snakers4_silero-models_master/

## Использование:
import torch
model, decoder, utils = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_stt',
    language='ru',
    device='cpu'
)

## Преимущества:
• Поддерживает Python 3.13
• Отличное качество для русского языка
• Быстрая работа на CPU
• Современная архитектура
