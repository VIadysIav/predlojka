import logging
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import asyncio

ADMIN_ID = YOUR_ID
BOT_TOKEN = 'YOUR_TOKEN'

banned_users = {}

async def start(update: Update, context) -> None:
    await update.message.reply_text(
        "Привіт! Надішли мені новину, i я передам її адміністрції для розгляду."
    )

async def ban(update: Update, context) -> None:
    if update.effective_user.id == ADMIN_ID:
        if context.args:
            username = context.args[0]
            banned_users[username] = True
            await update.message.reply_text(f"Користувач {username} заблокований.")
        else:
            await update.message.reply_text("Використання: /ban @username")
    else:
        await update.message.reply_text("Ви не маєте прав для цієї команди.")

async def unban(update: Update, context) -> None:
    if update.effective_user.id == ADMIN_ID:
        if context.args:
            username = context.args[0]
            if username in banned_users:
                del banned_users[username]
                await update.message.reply_text(f"Користувач {username} розблокований.")
            else:
                await update.message.reply_text(f"Користувач {username} не заблокований.")
        else:
            await update.message.reply_text("Використання: /unban @username")
    else:
        await update.message.reply_text("Ви не маєте прав для цієї команди.")

def is_banned(user) -> bool:
    return f"@{user.username}" in banned_users if user.username else False

async def handle_message(update: Update, context) -> None:
    user = update.message.from_user
    if is_banned(user):
        await update.message.reply_text("Ви заблоковані та не можете надсилати повідомлення.")
        return

    user_message = update.message.text_html
    admin_message = f"Нове повідомлення від @{user.username} (ID: {user.id}):\n\n{user_message}"

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_message,
        parse_mode="HTML"
    )

    await update.message.reply_text("Новину надіслано на розгляд.")

media_groups = {}

async def handle_media_group(update: Update, context) -> None:
    user = update.message.from_user
    if is_banned(user):
        await update.message.reply_text("Ви заблоковані та не можете надсилати повідомлення.")
        return

    username = f"@{user.username}" if user.username else f"User ID: {user.id}"
    media_group_id = update.message.media_group_id
    caption = update.message.caption_html if update.message.caption else ""

    if media_group_id:
        if media_group_id not in media_groups:
            media_groups[media_group_id] = []

        if update.message.photo:
            best_photo = update.message.photo[-1]
            media_groups[media_group_id].append(
                InputMediaPhoto(
                    media=best_photo.file_id,
                    caption=f"Повідомлення від {username}\n\n{caption}" if len(media_groups[media_group_id]) == 0 else "",
                    parse_mode="HTML"
                )
            )
        elif update.message.video:
            media_groups[media_group_id].append(
                InputMediaVideo(
                    media=update.message.video.file_id,
                    caption=f"Повідомлення від {username}\n\n{caption}" if len(media_groups[media_group_id]) == 0 else "",
                    parse_mode="HTML"
                )
            )

        if len(media_groups[media_group_id]) > 1:
            await context.bot.send_media_group(chat_id=ADMIN_ID, media=media_groups[media_group_id])
            await update.message.reply_text("Новину надіслано на розгляд.")
            del media_groups[media_group_id]

    else:
        if update.message.photo:
            best_photo = update.message.photo[-1]
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=best_photo.file_id,
                caption=f"Повідомлення від {username}\n\n{caption}",
                parse_mode="HTML"
            )
        elif update.message.video:
            await context.bot.send_video(
                chat_id=ADMIN_ID,
                video=update.message.video.file_id,
                caption=f"Повідомлення від {username}\n\n{caption}",
                parse_mode="HTML"
            )

        await update.message.reply_text("Новину надіслано на розгляд.")

async def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('ban', ban))
    application.add_handler(CommandHandler('unban', unban))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_media_group))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        print("Завершение работы бота...")
    finally:
        if application.updater.running:
            await application.updater.stop()

        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную.")
