from audio_core import AudioCore
import time

def test_audio_devices():
    """Протестировать работу аудиоустройств"""
    audio = AudioCore()
    
    print("🎯 Поиск аудиоустройств...")
    devices = audio.get_audio_devices()
    
    if not devices:
        print("❌ Устройства не найдены!")
        return
    
    print(f"✅ Найдено устройств: {len(devices)}")
    for i, device in enumerate(devices):
        print(f"  {i}: {device['name']} (каналы: {device['channels']})")
    
    # Тест записи
    if len(devices) >= 2:
        print("\n🎤 Тест записи с двух устройств...")
        success = audio.start_recording(devices[0]['index'], devices[1]['index'], duration=5)
        
        if success:
            print("✅ Запись начата...")
            time.sleep(6)  # Ждем завершения
            print("✅ Запись завершена!")
        else:
            print("❌ Ошибка записи!")
    else:
        print("❌ Нужно как минимум 2 устройства для теста!")

if __name__ == "__main__":
    test_audio_devices()


