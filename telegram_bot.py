import telebot
from openai import OpenAI
import os

# Переменные окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN') or "8034117424:AAGka9oDLR5zfwYaHjyfeee1UqvNrnZHfYY"
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY') or "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"

# Проверка наличия токенов
if BOT_TOKEN == "8034117424:AAGka9oDLR5zfwYaHjyfeee1UqvNrnZHfYY":
    print("⚠️  Используется тестовый BOT_TOKEN. Для production установите переменную окружения BOT_TOKEN")

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Исправленный клиент OpenAI для OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",  # Убраны пробелы
    api_key=OPENROUTER_API_KEY
)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
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
    try:
        # Уведомление о начале обработки
        processing_msg = bot.reply_to(message, "🧠 Создаю резюме...")
        
        # Создание резюме через GPT
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты помощник, создающий краткие резюме разговоров. Выдели основные темы, решения и действия."},
                {"role": "user", "content": f"Сделай резюме разговора:\n\n{message.text}"}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content
        
        # Отправка результата
        bot.edit_message_text(f"📋 *РЕЗЮМЕ РАЗГОВОРА:*\n\n{summary}", 
                            chat_id=processing_msg.chat.id, 
                            message_id=processing_msg.message_id,
                            parse_mode='Markdown')
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка обработки: {str(e)}")

if __name__ == '__main__':
    print("🤖 Бот запущен!")
    print("Для остановки нажмите Ctrl+C")
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен!")