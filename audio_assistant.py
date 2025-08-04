import sounddevice as sd
from scipy.io.wavfile import write
import whisper
from openai import OpenAI
import os
import time
from datetime import datetime

class AudioAssistant:
    def __init__(self, openai_api_key=None):
        self.api_key = openai_api_key
        self.fs = 44100  # частота дискретизации
        self.client = None
        
        if openai_api_key:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openai_api_key
            )
        
        # Проверка доступных аудио устройств
        print("Доступные аудио устройства:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"  {i}: {device['name']} (вход: {device['max_input_channels']} каналов)")
        
    def record_audio(self, seconds=30, filename=None):
        """Запись аудио"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.wav"
            
        print(f"Начинается запись на {seconds} секунд...")
        print("Говорите сейчас!")
        
        try:
            # Используем только 1 канал (mono) для избежания ошибок
            recording = sd.rec(int(seconds * self.fs), samplerate=self.fs, channels=1, dtype='int16')
            sd.wait()
            write(filename, self.fs, recording)
            print(f"Готово! Сохранено как {filename}")
            return filename
        except Exception as e:
            print(f"Ошибка при записи: {e}")
            # Попробуем с другими настройками
            try:
                print("Попытка записи с другими настройками...")
                recording = sd.rec(int(seconds * self.fs), samplerate=self.fs, channels=1, dtype='float32')
                sd.wait()
                # Конвертируем в int16
                recording = (recording * 32767).astype('int16')
                write(filename, self.fs, recording)
                print(f"Готово! Сохранено как {filename}")
                return filename
            except Exception as e2:
                raise Exception(f"Не удалось записать аудио: {e2}")
    
    def load_audio_file(self, filename):
        """Загрузка существующего аудио файла"""
        if os.path.exists(filename):
            print(f"Загружен файл: {filename}")
            return filename
        else:
            print(f"Файл {filename} не найден!")
            return None
    
    def transcribe_audio(self, filename, model_size="small", language="ru"):
        """Транскрибация аудио"""
        print("Загрузка модели Whisper...")
        model = whisper.load_model(model_size)
        
        print("Транскрибация аудио...")
        result = model.transcribe(filename, language=language)
        transcribed_text = result["text"]
        
        print("Транскрипция завершена!")
        return transcribed_text
    
    def create_summary(self, text, max_points=5):
        """Создание резюме с помощью GPT"""
        if not self.client:
            print("API ключ не предоставлен!")
            return None
            
        print("Создание резюме...")
        
        prompt = f"""Проанализируй разговор и создай краткое резюме с основными моментами.
        Выдели не более {max_points} ключевых пунктов.
        Разговор для анализа:
        {text}"""
        
        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты помощник, создающий краткие и структурированные резюме разговоров. Выделяй основные темы и решения."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content
            print("Резюме создано!")
            return summary
            
        except Exception as e:
            print(f"Ошибка при создании резюме: {e}")
            return None
    
    def save_results(self, text, summary, base_filename):
        """Сохранение результатов в файлы"""
        # Сохранение транскрипции
        transcript_file = base_filename.replace('.wav', '_transcript.txt')
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write("ТЕКСТ РАЗГОВОРА:\n")
            f.write("=" * 50 + "\n")
            f.write(text)
        
        # Сохранение резюме
        if summary:
            summary_file = base_filename.replace('.wav', '_summary.txt')
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("РЕЗЮМЕ РАЗГОВОРА:\n")
                f.write("=" * 50 + "\n")
                f.write(summary)
            
            print(f"Результаты сохранены в файлы:")
            print(f"  - Полный текст: {transcript_file}")
            print(f"  - Резюме: {summary_file}")
        else:
            print(f"Текст сохранен в: {transcript_file}")

def main():
    print("🎙️  Аудио помощник - Запись, транскрибация и резюме")
    print("=" * 50)
    
    # Ваш API ключ от OpenRouter
    API_KEY = "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"
    
    assistant = AudioAssistant(openai_api_key=API_KEY)
    
    while True:
        print("\nВыберите действие:")
        print("1. Записать новый разговор")
        print("2. Обработать существующий аудио файл")
        print("3. Выход")
        
        choice = input("\nВведите номер действия (1-3): ").strip()
        
        if choice == "1":
            # Запись нового разговора
            try:
                duration = int(input("Длительность записи в секундах (по умолчанию 30): ") or "30")
                filename = assistant.record_audio(seconds=duration)
                
                # Транскрибация
                text = assistant.transcribe_audio(filename)
                print("\nРАСШИФРОВКА:")
                print("-" * 30)
                print(text[:500] + "..." if len(text) > 500 else text)
                
                # Создание резюме
                summary = assistant.create_summary(text)
                if summary:
                    print("\nРЕЗЮМЕ:")
                    print("-" * 30)
                    print(summary)
                
                # Сохранение результатов
                assistant.save_results(text, summary, filename)
                
            except ValueError:
                print("Ошибка: введите корректное число секунд")
            except Exception as e:
                print(f"Ошибка при записи: {e}")
        
        elif choice == "2":
            # Обработка существующего файла
            filename = input("Введите имя аудио файла: ").strip()
            if not filename.endswith(('.wav', '.mp3', '.m4a', '.flac')):
                filename += '.wav'
            
            audio_file = assistant.load_audio_file(filename)
            if audio_file:
                try:
                    # Транскрибация
                    text = assistant.transcribe_audio(audio_file)
                    print("\nРАСШИФРОВКА:")
                    print("-" * 30)
                    print(text[:500] + "..." if len(text) > 500 else text)
                    
                    # Создание резюме
                    summary = assistant.create_summary(text)
                    if summary:
                        print("\nРЕЗЮМЕ:")
                        print("-" * 30)
                        print(summary)
                    
                    # Сохранение результатов
                    assistant.save_results(text, summary, audio_file)
                    
                except Exception as e:
                    print(f"Ошибка при обработке файла: {e}")
        
        elif choice == "3":
            print("До свидания! 👋")
            break
        
        else:
            print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()
