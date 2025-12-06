from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes
)
import re
import os


# ---------------------
# BOT TOKEN
# ---------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")


# Regex for Telegram links
TG_LINK_PATTERN = r"(https?:\/\/t\.me\/[^\s]+|t\.me\/[^\s]+)"


def has_tg_link(text: str):
    if not text:
        return False
    return re.search(TG_LINK_PATTERN, text) is not None


# ======================
# AUTO RESTRICT
# ======================
async def auto_restrict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # restrict forever
    await context.bot.restrict_chat_member(
        chat.id,
        user.id,
        ChatPermissions(can_send_messages=False),
        until_date=0
    )

    # delete the message
    try:
        await update.message.delete()
    except:
        pass

    await chat.send_message(
        f"🚫 {user.mention_html()} has been permanently restricted.",
        parse_mode="HTML"
    )


# ======================
# FILTER SYSTEM
# ======================
async def filter_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.message

    # ignore commands
    if msg.text and msg.text.startswith("/"):
        return

    # forwarded channel messages
    if msg.forward_from_chat and msg.forward_from_chat.type == "channel":
        await auto_restrict(update, context)
        return

    # t.me links
    if has_tg_link(msg.text):
        await auto_restrict(update, context)
        return

    if has_tg_link(msg.caption):
        await auto_restrict(update, context)
        return


# ======================
# COMMANDS
# ======================

# /kick (reply)
async def kick_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.reply_to_message:
        return await msg.reply_text("Reply to the user you want to kick.")

    uid = msg.reply_to_message.from_user.id
    await context.bot.ban_chat_member(msg.chat.id, uid)
    await context.bot.unban_chat_member(msg.chat.id, uid)

    await msg.reply_text("👢 User kicked.")


# /restrict (reply)
async def restrict_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.reply_to_message:
        return await msg.reply_text("Reply to the user to restrict them.")

    uid = msg.reply_to_message.from_user.id

    await context.bot.restrict_chat_member(
        msg.chat.id,
        uid,
        ChatPermissions(can_send_messages=False),
        until_date=0
    )

    await msg.reply_text("🔒 User permanently restricted.")


# /purge (reply)
async def purge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.reply_to_message:
        return await msg.reply_text("Reply to the message where purge begins.")

    chat = msg.chat
    start = msg.reply_to_message.message_id
    end = msg.message_id

    deleted = 0
    for msg_id in range(start, end + 1):
        try:
            await context.bot.delete_message(chat.id, msg_id)
            deleted += 1
        except:
            pass

    await chat.send_message(f"🧹 Purged {deleted} messages.")


# ======================
# RUN BOT
# ======================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, filter_messages))
app.add_handler(CommandHandler("kick", kick_cmd))
app.add_handler(CommandHandler("restrict", restrict_cmd))
app.add_handler(CommandHandler("purge", purge_cmd))

print("Bot is running...")
app.run_polling()
