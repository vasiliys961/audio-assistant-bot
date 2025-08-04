import # telegram_bot.py
import telebot
from openai import OpenAI
import os

# --- Конфигурация ---
# Получаем токены из переменных окружения или используем тестовые значения
# В production ОБЯЗАТЕЛЬНО задавать их через переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN') or "8034117424:AAGka9oDLR5zfwYaHjyfeee1UqvNrnZHfYY"
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY') or "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"

# Проверка, используется ли тестовый токен
if BOT_TOKEN == "8034117424:AAGka9oDLR5zfwYaHjyfeee1UqvNrnZHfYY":
    print("⚠️  Используется тестовый BOT_TOKEN. Для production установите переменную окружения BOT_TOKEN")

# --- Инициализация клиентов ---
bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация клиента OpenAI для работы с OpenRouter
# ВАЖНО: Убедитесь, что в base_url нет лишних пробелов
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", # Исправлен URL без пробелов
    api_key=OPENROUTER_API_KEY
)

# --- Обработчики сообщений ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Отправляет приветственное сообщение при /start или /help"""
    welcome_text = """
🎙️ *Аудио помощник*

Я могу анализировать текст разговоров и делать резюме!

📝 *Как использовать:*
1. Запиши голосовое сообщение в Telegram (он автоматически преобразуется в текст)
2. Или отправь мне текст разговора
3. Я создам краткое резюме через GPT

💰 *Стоимость:* около 1-2 рублей за сообщение
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(content_types=['text'])
def handle_text(message):
    """
    Обрабатывает текстовые сообщения от пользователей.
    Отправляет текст в OpenRouter API для генерации резюме.
    """
    try:
        # Уведомление о начале обработки
        processing_msg = bot.reply_to(message, "🧠 Создаю резюме...")
        
        # Создание резюме через GPT
        # Используем модель gpt-3.5-turbo для экономии
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "Ты помощник, создающий краткие резюме разговоров. Выдели основные темы, решения и действия."
                },
                {
                    "role": "user", 
                    "content": f"Сделай резюме разговора:\n\n{message.text}"
                }
            ],
            max_tokens=500,      # Ограничиваем длину ответа
            temperature=0.3      # Делаем ответы более детерминированными
        )
        
        # Извлекаем текст резюме из ответа API
        summary = response.choices[0].message.content
        
        # Отправка результата пользователю
        # Используем edit_message_text, чтобы изменить предыдущее сообщение
        bot.edit_message_text(
            f"📋 *РЕЗЮМЕ РАЗГОВОРА:*\n\n{summary}", 
            chat_id=processing_msg.chat.id, 
            message_id=processing_msg.message_id,
            parse_mode='Markdown'
        )
            
    except Exception as e:
        # В случае любой ошибки отправляем сообщение об этом пользователю
        error_msg = f"❌ Ошибка обработки: {str(e)}"
        print(error_msg) # Логируем ошибку в консоль для отладки
        bot.reply_to(message, error_msg)

# --- Запуск бота ---
if __name__ == '__main__':
    print("🤖 Бот запущен!")
    print("Для остановки нажмите Ctrl+C")
    try:
        # Запускаем long polling для получения обновлений от Telegram
        # none_stop=True означает, что бот будет пытаться переподключаться при ошибках
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        # Перехватываем сигнал Ctrl+C для корректного завершения работы
        print("\n👋 Бот остановлен!")
    except Exception as e:
        # Логируем любые неожиданные ошибки при запуске
        print(f"🚨 Критическая ошибка при запуске бота: {e}")
