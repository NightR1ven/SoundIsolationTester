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
            # Ждем, пока таймер сам не остановит запись
            print("⏳ Ожидание автоматической остановки через 5 секунд...")
            time.sleep(6)  # Ждем немного больше для надежности
            print("✅ Тест завершен!")
            
            # Проверяем, что запись остановилась
            if not audio.is_recording:
                print("✅ Запись автоматически остановлена по таймеру")
            else:
                print("⚠️ Запись не остановилась автоматически")
        else:
            print("❌ Ошибка записи!")
    else:
        print("❌ Нужно как минимум 2 устройства для теста!")

if __name__ == "__main__":
    test_audio_devices()


