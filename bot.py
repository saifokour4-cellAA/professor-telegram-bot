import json
import os
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ===================== إعدادات =====================
TOKEN = "8654189257:AAFET6wtMjvjrPsBeRH-ueLIRAXhptMospc"

ADMIN_ID = 8151228673
ADMIN_IDS = {ADMIN_ID}

ADMIN_USERNAME = "@theproff991"
ADMIN_URL = "https://t.me/theproff991"

DATA_FILE = "requests_data.json"
# ===================== التصويت =====================
VOTES = {}
# ===================== المواد =====================
READY_SUBJECTS = {
    "لاب مايكرو": (
        "🧫 قناة متوقّع البروفيسور – لاب مايكرو\n\n"
        "القناة تحتوي على:\n"
        "✔ شرح تجارب اللاب\n"
        "✔ أهم النقاط اللي يركز عليها الدكتور\n"
        "✔ أسئلة امتحانات سابقة\n"
        "✔ أسئلة متوقعة\n\n"
        "💰 الاشتراك: 7 دنانير\n\n"
        "💳 الدفع عبر زين كاش:\n"
        "📱 0798024692\n\n"
        "📸 بعد التحويل اضغط الزر بالأسفل وابعت صورة الوصل للبروفيسور."
    ),
    "فايتوثيرابي صيدلة": (
        "🌿 قناة متوقّع البروفيسور – فايتوثيرابي صيدلة\n\n"
        "القناة تحتوي على:\n"
        "✔ أسئلة سنوات متوقعة مع إجاباتها\n\n"
        "💰 الاشتراك: 4 دنانير\n\n"
        "💳 الدفع عبر زين كاش:\n"
        "📱 0798024692\n\n"
        "📸 بعد التحويل اضغط الزر بالأسفل وابعت صورة الوصل للبروفيسور."
    ),
}

BASIC_SUBJECTS = [
    "فارما 1", "فارما 2", "فارما 3",
    "سوتكس 1", "سوتكس 2", "سوتكس 3",
    "ميدو 1", "ميدو 2", "ميدو 3",
    "كيمياء تحليلية", "انسترو صيدلة",
    "فايتو صيدلة", "كاينتك",
    "تكنو صيدلة", "تقانات حيوية",
    "انظمه ايصال | Drug delivery", "مناعة",
    "مصادر المعلومات وتقييم الدراسات", "كلينيكال",
    "صحة عامة", "ادوية بدون وصفة طبية | OTC",
    "تغذية سريرية", "اخلاقيات ومهارات الاتصال",
    "اقتصاد وادارة", "تسويق صيدلي",
    "علم الاوبئة", "كيمياء عضوية صيدلية",
    "مقدمه في الصيدلة",
    "فايتوثيرابي صيدلة",
]

LAB_SUBJECTS = [
    "لاب علوم صيدلانية",
    "لاب تراكيب 2",
    "لاب مايكرو",
    "لاب كيسز 2",
    "لاب صيدلية تشبيهية",
]

PHARMD_SUBJECTS = [
    "انسترو دكتور صيدلة",
    "فايتو دكتور صيدلة",
    "لاب تركيب دكتور صيدلة د ص ٣٥٧",
    "كلينيكال كاينتك دكتور صيدلة",
    "اونكو دكتور صيدلة",
    "اندو دكتور صيدلة",
    "لاب سكيلز ٣",
    "لاب سيلز ٤",
    "تسويق واقتصاد دكتور صيدلة",
    "علاج دوائي : العناية الحثيثة",
    "علاج دوائي : صحة اطفال",
    "علاج دوائي : نسائية ومسالك",
    "لاب سكيلز ٧",
    "لاب سكيلز ٨",
    "مقدمه في التدريب دكتور صيدلة",
]

ALL_SUBJECTS = set(BASIC_SUBJECTS + LAB_SUBJECTS + PHARMD_SUBJECTS)

MAIN_MENU = [
    ["✅ المواد الجاهزة الآن", "📚 المواد الأساسية"],
    ["🧪 اللابات", "🎓 مواد دكتور صيدلة"],
    ["💳 كيف أشترك؟", "📩 تواصل مع البروفيسور"],
]
# ===================== أدوات مساعدة =====================
def chunk_buttons(items, per_row=2):
    rows = []
    for i in range(0, len(items), per_row):
        rows.append(items[i:i + per_row])
    return rows

def main_keyboard():
    return ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True)

def section_keyboard(items):
    rows = chunk_buttons(items, 2)
    rows.append(["⬅️ رجوع للقائمة الرئيسية"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"counts": {}, "who": {}}

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

DATA = load_data()

async def notify_admin_new_interest(subject: str, user, count: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        username = f"@{user.username}" if user.username else "بدون يوزرنيم"
        msg = (
            "📊 طلب جديد على مادة\n\n"
            f"📚 المادة: {subject}\n"
            f"👤 الطالب: {user.full_name}\n"
            f"🔗 الحساب: {username}\n"
            f"📈 العدد الكلي: {count}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
    except Exception:
        pass

async def register_request(subject: str, user, context: ContextTypes.DEFAULT_TYPE):
    user_id = user.id

    if subject not in DATA["counts"]:
        DATA["counts"][subject] = 0
        DATA["who"][subject] = []

    if user_id not in DATA["who"][subject]:
        DATA["who"][subject].append(user_id)
        DATA["counts"][subject] += 1
        save_data(DATA)
        await notify_admin_new_interest(subject, user, DATA["counts"][subject], context)

# ===================== أوامر =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت البروفيسور\n\n"
        "💪 معنا رح تضمن التفوق وبشهادة الجميع\n\n"
        "اختر القسم المناسب من القائمة 👇",
        reply_markup=main_keyboard(),
    )

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    counts = DATA.get("counts", {})
    if not counts:
        await update.message.reply_text("لا توجد طلبات مسجلة بعد.")
        return

    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    msg = "📊 إحصائيات الطلب على المواد:\n\n"

    for subject, count in items:
        msg += f"• {subject} : {count}\n"

    await update.message.reply_text(msg)

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    counts = DATA.get("counts", {})
    if not counts:
        await update.message.reply_text("لا توجد بيانات بعد.")
        return

    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    msg = "🔥 أعلى 10 مواد طلبًا:\n\n"

    for i, (subject, count) in enumerate(items, start=1):
        msg += f"{i}) {subject} — {count}\n"

    await update.message.reply_text(msg)

async def ready_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    counts = DATA.get("counts", {})
    ready_counts = {k: v for k, v in counts.items() if k in READY_SUBJECTS}

    if not ready_counts:
        await update.message.reply_text("لا توجد طلبات على المواد الجاهزة بعد.")
        return

    msg = "✅ إحصائيات المواد الجاهزة:\n\n"

    for subject, count in sorted(ready_counts.items(), key=lambda x: x[1], reverse=True):
        msg += f"• {subject} : {count}\n"
# ===================== الرسائل العامة =====================
async def send_subscription_guide(update: Update):
    btns = [[InlineKeyboardButton("📩 تواصل مع البروفيسور", url=ADMIN_URL)]]
    await update.message.reply_text(
        "💳 طريقة الاشتراك:\n\n"
        "1) اختر المادة\n"
        "2) حوّل المبلغ عبر زين كاش\n"
        "3) اضغط زر إرسال وصل الدفع\n"
        "4) ابعت صورة الوصل للبروفيسور\n"
        "5) بعد التأكيد رح تستلم رابط القناة\n\n"
        "📱 زين كاش: 0798024692",
        reply_markup=InlineKeyboardMarkup(btns),
    )

async def send_contact(update: Update):
    btns = [[InlineKeyboardButton("📩 افتح محادثة مع البروفيسور", url=ADMIN_URL)]]
    await update.message.reply_text(
        "للتواصل المباشر مع البروفيسور اضغط الزر بالأسفل 👇",
        reply_markup=InlineKeyboardMarkup(btns),
    )

# ===================== التعامل مع الرسائل =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    user = update.effective_user

    if text == "⬅️ رجوع للقائمة الرئيسية":
        await update.message.reply_text(
            "رجعناك للقائمة الرئيسية ✅",
            reply_markup=main_keyboard()
        )
        return

    if text == "✅ المواد الجاهزة الآن":
        await update.message.reply_text(
            "اختر مادة جاهزة 👇",
            reply_markup=section_keyboard(list(READY_SUBJECTS.keys()))
        )
        return

    if text == "📚 المواد الأساسية":
        await update.message.reply_text(
            "اختر من المواد الأساسية 👇",
            reply_markup=section_keyboard(BASIC_SUBJECTS)
        )
        return

    if text == "🧪 اللابات":
        await update.message.reply_text(
            "اختر من اللابات 👇",
            reply_markup=section_keyboard(LAB_SUBJECTS)
        )
        return

    if text == "🎓 مواد دكتور صيدلة":
        await update.message.reply_text(
            "اختر من مواد دكتور صيدلة 👇",
            reply_markup=section_keyboard(PHARMD_SUBJECTS)
        )
        return

    if text == "💳 كيف أشترك؟":
        await send_subscription_guide(update)
        return

    if text == "📩 تواصل مع البروفيسور":
        await send_contact(update)
        return

    if text in READY_SUBJECTS:
        await register_request(text, user, context)

        btns = [[InlineKeyboardButton("📩 إرسال وصل الدفع للبروفيسور", url=ADMIN_URL)]]
        await update.message.reply_text(
            READY_SUBJECTS[text],
            reply_markup=InlineKeyboardMarkup(btns)
        )
        return

    if text in ALL_SUBJECTS:
        await register_request(text, user, context)

        btns = [[InlineKeyboardButton("📩 تواصل مع البروفيسور", url=ADMIN_URL)]]
        await update.message.reply_text(
            f"📚 المادة: {text}\n\n"
            "⚠️ حالياً شغالين على تجهيز هاي المادة.\n"
            "إذا بدك تكون من أوائل الناس اللي بتنزل إلهم، ابعث اسم المادة للبروفيسور على الخاص 👇",
            reply_markup=InlineKeyboardMarkup(btns)
        )
        return

    await update.message.reply_text(
        "اختار من الأزرار الموجودة 👇",
        reply_markup=main_keyboard()
    )
# ===================== أوامر التصويت =====================

async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = []

    for subject in BASIC_SUBJECTS:
        keyboard.append([InlineKeyboardButton(subject, callback_data=f"vote_{subject}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📊 اختر المادة التي تريدها:",
        reply_markup=reply_markup
    )


async def vote_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    subject = query.data.replace("vote_", "")

    if subject not in VOTES:
        VOTES[subject] = 0

    VOTES[subject] += 1

    await query.edit_message_text(
        f"✅ تم تسجيل صوتك لمادة:\n{subject}"
    )


async def vote_results(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not VOTES:
        await update.message.reply_text("لا يوجد تصويت بعد.")
        return

    msg = "📊 نتائج التصويت:\n\n"

    for subject, count in VOTES.items():
        msg += f"{subject} : {count}\n"

    await update.message.reply_text(msg)
# ===================== تشغيل البوت =====================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("ready_stats", ready_stats))
    app.add_handler(CommandHandler("vote", vote))
    app.add_handler(CommandHandler("vote_results", vote_results))

    app.add_handler(CallbackQueryHandler(vote_button, pattern="^vote_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
