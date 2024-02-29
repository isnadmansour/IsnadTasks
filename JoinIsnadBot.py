import datetime
import logging
import os
import random
import re
import time
from typing import List, Optional, Tuple

import telegram
from fastapi import BackgroundTasks, FastAPI, HTTPException
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ContextTypes, ConversationHandler,
                          Filters, MessageHandler, Updater, filters)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = FastAPI(title="Ask Isnad Bot")


@app.on_event("startup")
async def startup_event():
    print('JoinIsnad Server started---- :', datetime.datetime.now())
    global is_task_running
    is_task_running = True
    try:
        main()
        pass
    except telegram.error.Conflict as e:
        print(f"Telegram Conflict Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")



# Define a global variable to store the conversation ID counter
conversation_id_counter = 1

# Set to store blocked user chat IDs
blocked_users = set()

# Define conversation states
GET_TWITTER_ACCOUNT, GET_VOICE, BLOCKED = range(3)

# Define a function to start the conversation
def start(update: Update, context: CallbackContext) -> int:
    global conversation_id_counter  # Access the global conversation ID counter

    # Generate a unique ID for the conversation
    context.user_data['conversation_id'] = conversation_id_counter
    conversation_id_counter += 1  # Increment the conversation ID counter

    user = update.message.from_user
    welcome_message =(
        "*شكراً لتطوعك في إسناد* "+"\n"
        " "+"\n"
        "مرحباً بك، أنا *بوت إسناد الإلكتروني🤖 * لاستقبال الأعضاء الجدد:"+"\n"
        " "+"\n"
        "✅ قبل أي شئ يجب تعمل (اسم مستخدم - USER NAME) لحسابك تليجرام من الإعدادات"+"\n"
        "اعمل دا .. وبعدها كمل قرادة الرساله دي 👇🏼"+"\n"
        " "+"\n"
        "1️⃣-  أول خطوة للانضمام هي الانضمام للجروب المغلق."+"\n"
        " "+"\n"
        "2️⃣-  الانضمام لجروب إسناد بيستلزم نتأكد انك شخص عربي حقيقي، لأن بيجيلنا طلبات انضمام من صهاينة بيىىىــىحدموا تطبيقات تزجمة، فبنحتاج نفلترها."+"\n"
        " "+"\n"
        " "+"\n"
        "3️⃣- لذلك مطلوب منك تبعتلنا هنا رىىىـ.ـــا له فو، ـيس تحكى فيها تحــ ــيةـالىىىــلامــ صو،تياَ - كرد على الرىىىىاله هنا."+"\n"
        " "+"\n"
        "هذه رسالة ثابتة من بوت إسناد ، سوف تصل إلى الآدمن المختص لمراجعتها ثم الرد عليك"+"\n"
        "فقط مسموح بإرسال التىىىجـــل الصو، تى في الرد."+"\n"
        " "+"\n"
        "تحياتنا، ومرحباً بك.✅"+"\n"
    )
    # Get the username of the user
    username = update.message.from_user.username
    print('username:',username)
    context.user_data['user_username'] = username
    context.user_data['user_chat_id'] = user.id  # Store user's chat ID
    context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message,  parse_mode= 'Markdown')
    return GET_VOICE

# Define a function to get the user's email
def get_twitter_account(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    user_twitter_url = update.message.text
    user_chat_id = update.message.chat_id
    twitter_url_pattern = r'^https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+'

    if re.match(twitter_url_pattern, user_twitter_url):

        # Forward the voice message along with the user's chatid to the admin
        conversation_id = context.user_data['conversation_id']
        admin_chat_id = '516506452'  # Replace with your admin's chat ID
        voice_message_id = context.user_data['voice']['file_id']
        context.user_data['twitter_account'] = user_twitter_url
        user_username = ""
        if context.user_data['user_username']:
            user_username = str(context.user_data['user_username'])
            admin_msg =(
                "<b>طلب عضوية جديد.</b>"+"\n"
                " "+"\n"
                "<u>بيانات العضو:</u>"+"\n"
                " "+"\n"
                "رقم العضوية: " + str(conversation_id)+"\n"
                "أكونت تليجرام:"+"\n"
                "@"+user_username+"\n"
                " "+"\n"
                "<a href=\""+context.user_data['twitter_account']+"\">أكونت تويتر</a>"
                )
        else:
            admin_msg =(
                "<b>طلب عضوية جديد.</b>"+"\n"
                " "+"\n"
                "<u>بيانات العضو:</u>"+"\n"
                " "+"\n"
                "رقم العضوية: " + str(conversation_id)+"\n"
                " "+"\n"
                "<a href=\"tg://user?id="+str(context.user_data['user_chat_id'])+"\">أكونت تليجرام</a>"
                " "+"\n"
                "<a href=\""+context.user_data['twitter_account']+"\">أكونت تويتر</a>"
            )
        context.bot.send_message(admin_chat_id, admin_msg, parse_mode="HTML", disable_web_page_preview=True)
        context.bot.send_message(admin_chat_id, "<b>الرسالة الصوتية:</b>" , parse_mode="HTML")
        context.bot.send_voice(admin_chat_id, voice=voice_message_id)
        context.bot.send_message(admin_chat_id, "------------------------------------------" , parse_mode="HTML")
        # Block further messages from the user
        blocked_users.add(user_chat_id)

        thanks_message =(
            "<b>طلبك قيد المراجعه من الآدمن المختص</b>"+"\n"
            " "+"\n"
            "ساعدنا بالصبر، سنرد عليك خلال 24 ساعه على الأكثر إن شاء الله"+"\n"
            "سنراجع طلبك وفي حال انك ارسلت حساب عبري صحيح، والرسالة التأكيدية بشكل صحيح، سيتم قبول طلبك."+"\n"
            " "+"\n"
            )
        update.message.reply_text(text=thanks_message, parse_mode= 'HTML')
        time.sleep(1)
        thanks_message=(
            "ونعتذر لتعدد الخطوات ، ولكن هذا لأمان الحملة ، لعدم السماح باندساس صهاينة لحساب المهمات."+"\n"
            " "+"\n"
            "ـ🇵🇸"
            "لنا طلب أخير عندك بعد انضمامك لنا، ربنا أعطالنا طريقة لإسناد المقاومة ونصرة المظلومين، وأختارنا ليمسح عنا العجز والخذلان :"+"\n"
            " "+"\n"
            "<b>\"نتمنى منك بشدة انك لا تتوقف عن تنفيذ المهمات، ولا يؤثر بك الإحباط أو الألم ، ولا تتخاذل عن استكمال المهمات يوميا، حتى يكتب لنا ربنا النصر، ويكتب لنا أجر المجاهدين المرابطين\"</b>"+"\n"
            " "+"\n"
            " "+"\n"
            "<b>تأكد من عمل اسم مستخدم USER NAME لحسابك من إعدادات تليجرام </b>"+"\n"
            " "+"\n"
            "تحياتنا "+"\n"
            "ومرحب بيك في إسناد "+"\n"
        )
        update.message.reply_text(text=thanks_message, parse_mode= 'HTML')

        return BLOCKED
    else:
        update.message.reply_text(
            "عفواً, يرجي إرسال رابط أكونت تويتر فقط."
        )
        return GET_TWITTER_ACCOUNT

# Define a function to handle messages from blocked users
def blocked_message_handler(update: Update, context: CallbackContext) -> None:
    user_chat_id = update.message.chat_id
    if user_chat_id in blocked_users:
        update.message.reply_text(
            "طلبك قيد المراجعه من الآدمن المختص."
        )
    else:
        # Process the message as usual
        pass


# Define a function to get the user's voice message
def get_voice(update: Update, context: CallbackContext) -> int:
    if update.message.voice:
        user = update.message.from_user
        context.user_data['voice'] = update.message.voice

        voice_finished_message =(
        "⭕️ <b>مطلوب الآن تعمل حساب عبري على تويتر بأي إيميل،، ازاي ؟</b>"+"\n"
        " "+"\n"
        "1️⃣- تختار اسم عبري بحروف عبرية ، من جوجل او شات جي بي تي أو ممكن تختار أسامي عبرية من هنا <a href=\'https://docs.google.com/document/d/193Snn-Q268QFRNtKWJy_2WCSMjQ3WqGX3dGSdY0Wdmc/edit?usp=sharing\'>اضغط هنا</a>"+"\n"
        "ملاحظة: أول حاجة لازم تكون مقرر اكاونت بنت ولا ولد وعمره كام، عشان تبقى المعلومات متناسقة 👌 "+"\n"
        "ممكن اسم بحروف انجليزي عادي، مش شرط عبري، ولو الاتنين مع بعض يكون أفضل. و يكون متجانس مع اليوزرنيم."+"\n"
        " "+"\n"
        )
        time.sleep(1)
        context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'HTML', disable_web_page_preview=True)
        voice_finished_message =(
        "2️⃣- تختار صورة بروفايل صهيونية (سيرش جوجل على صورة مناسبة، لا تستخدم علم اسرائيل أصبح مكشوف)"+"\n"
        "* الصورة الشخصية: يفضل تكون لشخص عادي حتي لو من بعيد والملامح مش ظاهرة، و دي ممكن تجيبها من الفيسبوك عندهم. "+"\n"
        "* صورة الخلفية: يفضل تكون بتعبر عن اتجاه ما، مش مجرد صورة عشوائية. "+"\n"
        " "+"\n"
        )
        context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
        time.sleep(1)
        voice_finished_message =(
        "3️⃣- ويوزرنيم تويتر يكون رموز وارقام *مايكونش اسم عربي*. "+"\n"
        "4️⃣- الحساب مهم جداً ميكونش فيه ولا كلمه عربي."+"\n"
        "5️⃣- يكون لوكيشن الحساب اسم الدوله اسرائيل بالانجليزي Israel أو اسرائيل بالعبري: ישראל "+"\n"
        " "+"\n"
        )
        context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
        time.sleep(1)
        voice_finished_message =(
        "6️⃣- الوصف/البيو: يتاخد من اكاونت صهيوني فيس او تويتر، بس خلي بالك انت حسابك هايكون (ذكر ولا مؤنث) عشان بتفرق في الصياغة، او ممكن تخلي البيو انجليزي."+"\n"
        " "+"\n"
        "🔴 اهم حاجه ان *الاكونت يكون متسق مع بعضه* مش متناقض،، يعني ميبقاش اسم بنت و الوصف شاب 😅"+"\n"
        "او صورة بنت صغيرة و مكتوب انها ام مثلا او جدة.."+"\n"
        )
        context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
        time.sleep(1)
        voice_finished_message =(
        "بعد ما تعمل الحساب بالمواصفات دي، ابعت الرابط بتاعه هنا كرد على الرساله دي،"+"\n"
        "ولو عملته بالفعل، راجعه الاول وحسن فيه بحسب المواصفات دي، وابعت الرابط هنا"+"\n"
        " "+"\n"
        "(لو مش عارف تجيب رابط تويتر، انشر تويته عندك عالحساب وهات الرابط بتاعها من الشير)"+"\n"
        " "+"\n"
        "*رابط وليس صورة شاشة*"+"\n"
        )
        context.bot.send_message(chat_id=update.effective_chat.id,text=voice_finished_message,  parse_mode= 'Markdown')
        return GET_TWITTER_ACCOUNT
    else:
        update.message.reply_text(
            " فقط مسموح بإرسال المطلوب في الرسالة السابقة، أعد قرائتها جيداً ."
        )
        return GET_VOICE

# Define a function to cancel the conversation
def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    update.message.reply_text(
        "The conversation has been canceled.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token
    updater = Updater("6918060750:AAE7w0GNJO6PXKxG5SHndkiuR3QWxnUmR5A")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Define conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GET_VOICE: [MessageHandler(Filters.all & ~Filters.command, get_voice)],
            GET_TWITTER_ACCOUNT: [MessageHandler(Filters.text & ~Filters.command, get_twitter_account)],
            BLOCKED: [MessageHandler(Filters.text & ~Filters.command, blocked_message_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Register conversation handler
    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    # updater.idle()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
