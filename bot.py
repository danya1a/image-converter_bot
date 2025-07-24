
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from PIL import Image
from io import BytesIO

# Уровень логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Языки интерфейса
LANGUAGES = {
    "en": {"start": "Send me an image and I'll convert it to another format.",
           "choose_format": "Choose format to convert to:",
           "converted": "Here is your converted image:"},
    "ru": {"start": "Отправь мне изображение, и я сконвертирую его в другой формат.",
           "choose_format": "Выберите формат для конвертации:",
           "converted": "Вот ваше сконвертированное изображение:"},
    "uk": {"start": "Надішліть мені зображення, і я конвертую його в інший формат.",
           "choose_format": "Оберіть формат для конвертації:",
           "converted": "Ось ваше конвертоване зображення:"}
}

# Форматы для конвертации
FORMATS = ["JPEG", "PNG", "WEBP", "BMP", "TIFF"]

user_language = {}

async def start(update: Update, context: CallbackContext):
    lang = "en"
    user_language[update.effective_user.id] = lang
    keyboard = [
        [InlineKeyboardButton("English", callback_data="lang_en"),
         InlineKeyboardButton("Русский", callback_data="lang_ru"),
         InlineKeyboardButton("Українська", callback_data="lang_uk")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(LANGUAGES[lang]["start"], reply_markup=reply_markup)

async def set_language(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_language[query.from_user.id] = lang
    await query.edit_message_text(LANGUAGES[lang]["start"])

async def handle_image(update: Update, context: CallbackContext):
    lang = user_language.get(update.effective_user.id, "en")
    keyboard = [[InlineKeyboardButton(fmt, callback_data=f"convert_{fmt}")] for fmt in FORMATS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    file_id = update.message.photo[-1].file_id if update.message.photo else update.message.document.file_id
    context.user_data["file_id"] = file_id
    await update.message.reply_text(LANGUAGES[lang]["choose_format"], reply_markup=reply_markup)

async def convert_image(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    lang = user_language.get(query.from_user.id, "en")
    fmt = query.data.split("_")[1]
    file_id = context.user_data.get("file_id")
    if not file_id:
        await query.edit_message_text("No image found.")
        return

    file = await context.bot.get_file(file_id)
    byte_data = await file.download_as_bytearray()
    image = Image.open(BytesIO(byte_data))
    output = BytesIO()
    output.name = f"converted.{fmt.lower()}"
    image.save(output, format=fmt)
    output.seek(0)
    await query.message.reply_document(document=output, filename=output.name, caption=LANGUAGES[lang]["converted"])

def main():
    import dotenv
    dotenv.load_dotenv()
    token = os.getenv("BOT_TOKEN", "")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(convert_image, pattern="^convert_"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image))
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
