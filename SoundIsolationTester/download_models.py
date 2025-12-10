﻿#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скачивание всех моделей для офлайн работы
"""

import os
import sys
import urllib.request
import zipfile
import hashlib
from pathlib import Path

def create_directories():
    """Создание структуры папок для моделей"""
    directories = [
        "models/whisper",
        "models/vosk",
        "models/temp"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Создана папка: {directory}")
    
    return True

def download_whisper_models():
    """Скачивание и сохранение Whisper моделей"""
    print("\n" + "="*50)
    print("Загрузка Whisper моделей")
    print("="*50)
    
    models = {
        "tiny": "https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt",
        "base": "https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt",
        "small": "https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt",
        "medium": "https://openaipublic.azureedge.net/main/whisper/models/345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1/medium.pt"
    }
    
    for model_name, url in models.items():
        model_path = f"models/whisper/{model_name}.pt"
        
        if os.path.exists(model_path):
            print(f"✓ Модель {model_name} уже существует")
            continue
        
        print(f"📥 Скачивание {model_name}...")
        try:
            # Скачиваем модель
            urllib.request.urlretrieve(url, model_path)
            
            # Проверяем размер
            size_mb = os.path.getsize(model_path) / (1024 * 1024)
            print(f"✅ {model_name} загружен ({size_mb:.1f} МБ)")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки {model_name}: {e}")
    
    print("\n✅ Whisper модели готовы к использованию")

def download_vosk_models():
    """Скачивание Vosk моделей для русского языка"""
    print("\n" + "="*50)
    print("Загрузка Vosk моделей (русский язык)")
    print("="*50)
    
    vosk_models = {
        "small-ru": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip",
            "size": "40 МБ",
            "dir": "vosk-model-small-ru-0.22"
        },
        "large-ru": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip",
            "size": "1.8 ГБ",
            "dir": "vosk-model-ru-0.42"
        }
    }
    
    for model_name, model_info in vosk_models.items():
        model_dir = f"models/vosk/{model_name}"
        
        if os.path.exists(model_dir):
            print(f"✓ Модель {model_name} уже существует")
            continue
        
        print(f"\n📥 Скачивание {model_name} ({model_info['size']})...")
        print(f"URL: {model_info['url']}")
        
        # Создаем временный файл
        zip_path = f"models/temp/{model_name}.zip"
        
        try:
            # Скачиваем архив
            urllib.request.urlretrieve(model_info['url'], zip_path)
            print(f"✓ Архив скачан")
            
            # Распаковываем
            print(f"📦 Распаковка...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall("models/vosk")
            
            # Переименовываем папку
            extracted_dir = f"models/vosk/{model_info['dir']}"
            if os.path.exists(extracted_dir):
                os.rename(extracted_dir, model_dir)
                print(f"✅ Модель {model_name} установлена в {model_dir}")
            
            # Удаляем архив
            os.remove(zip_path)
            
        except Exception as e:
            print(f"❌ Ошибка загрузки {model_name}: {e}")
            continue
    
    print("\n✅ Vosk модели готовы к использованию")

def check_dependencies():
    """Проверка зависимостей"""
    print("\n" + "="*50)
    print("Проверка зависимостей")
    print("="*50)
    
    dependencies = {
        "whisper": "pip install openai-whisper",
        "vosk": "pip install vosk",
        "librosa": "pip install librosa",
    }
    
    missing = []
    
    for dep, install_cmd in dependencies.items():
        try:
            __import__(dep.replace("-", "_"))
            print(f"✅ {dep}")
        except ImportError:
            print(f"⚠️ {dep} - установите: {install_cmd}")
            missing.append(dep)
    
    return len(missing) == 0

def main():
    """Основная функция"""
    print("🔧 УСТАНОВКА МОДЕЛЕЙ ДЛЯ ТЕСТЕРА ЗВУКОИЗОЛЯЦИИ")
    print("="*60)
    
    # Создаем структуру
    create_directories()
    
    # Проверяем зависимости
    if not check_dependencies():
        print("\n⚠️ Установите недостающие зависимости и перезапустите скрипт")
        return
    
    # Загружаем модели
    download_whisper_models()
    download_vosk_models()
    
    print("\n" + "="*60)
    print("🎉 МОДЕЛИ УСТАНОВЛЕНЫ!")
    print("\n📁 Структура моделей:")
    print("  models/whisper/    - Whisper модели (tiny, base, small, medium)")
    print("  models/vosk/       - Vosk модели (small-ru, large-ru)")
    print("\n🚀 Теперь можно работать полностью офлайн!")

if __name__ == "__main__":
    main()