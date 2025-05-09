import os
import logging
import base64
import whisper
import uuid
from pydub import AudioSegment
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client with OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def transcribe_with_whisper_local(audio_path):
    model = whisper.load_model("base")  # Можно заменить на "small", "medium", "large"
    result = model.transcribe(audio_path, language="ru")
    return result["text"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Привет! Я бот для улучшения дикции.\n\n"
        "Отправь мне голосовое сообщение, и я проанализирую твою речь, "
        "найду возможные проблемы с дикцией и дам рекомендации по улучшению.\n\n"
        "Просто запиши и отправь голосовое сообщение!"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = (
        "🤖 Как пользоваться ботом:\n\n"
        "1. Запиши голосовое сообщение\n"
        "2. Отправь его мне\n"
        "3. Я проанализирую твою речь и дам рекомендации\n\n"
        "Советы для лучшего результата:\n"
        "• Говори четко и в нормальном темпе\n"
        "• Записывай в тихом помещении\n"
        "• Держи микрофон на расстоянии 10-15 см от рта"
    )
    await update.message.reply_text(help_text)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages and analyze diction."""
    try:
        # Получаем голосовой файл
        voice = await update.message.voice.get_file()
        voice_file = await voice.download_as_bytearray()

        # Генерируем уникальное имя файла
        temp_ogg = f"temp_voice_{uuid.uuid4().hex}.ogg"
        temp_wav = temp_ogg.replace(".ogg", ".wav")

        # Сохраняем ogg
        with open(temp_ogg, "wb") as f:
            f.write(voice_file)
        logger.info(f"Файл сохранён: {temp_ogg}, существует: {os.path.exists(temp_ogg)}")

        # Проверяем существование перед конвертацией
        if not os.path.exists(temp_ogg):
            logger.error(f"Файл не найден перед конвертацией: {temp_ogg}")
            await update.message.reply_text("Временный файл не найден. Попробуйте ещё раз.")
            return

        # Конвертируем ogg в wav
        audio = AudioSegment.from_file(temp_ogg)
        audio.export(temp_wav, format="wav")
        logger.info(f"Файл сконвертирован: {temp_wav}, существует: {os.path.exists(temp_wav)}")

        # Проверяем существование перед распознаванием
        if not os.path.exists(temp_wav):
            logger.error(f"Файл не найден перед распознаванием: {temp_wav}")
            await update.message.reply_text("Временный wav-файл не найден. Попробуйте ещё раз.")
            return

        # 1. Распознаём речь через локальный Whisper
        recognized_text = transcribe_with_whisper_local(temp_wav)

        # Удаляем временные файлы
        for temp_file in [temp_ogg, temp_wav]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.info(f"Файл удалён: {temp_file}")
            else:
                logger.warning(f"Файл не найден для удаления: {temp_file}")

        if not recognized_text.strip():
            await update.message.reply_text(
                "Не удалось распознать речь. Пожалуйста, попробуйте записать сообщение четче."
            )
            return

        # 2. Анализируем текст через LLM
        completion = client.chat.completions.create(
            model="anthropic/claude-3-sonnet",
            messages=[
                {
                    "role": "user",
                    "content": f"Проанализируй мою дикцию и дай рекомендации по улучшению. Вот текст, который я произнёс: {recognized_text}"
                }
            ]
        )
        analysis = completion.choices[0].message.content

        # Отправляем анализ пользователю
        await update.message.reply_text(f"Распознанный текст: {recognized_text}\n\n{analysis}")

    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке голосового сообщения. "
            "Пожалуйста, попробуйте еще раз."
        )

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 