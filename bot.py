import logging
import os
import sqlite3

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== إعدادات =====================
TOKEN = "PUT_YOUR_NEW_BOT_TOKEN_HERE"

ADMIN_ID = 8151228673
ADMIN_IDS = {ADMIN_ID}

ADMIN_USERNAME = "@theproff991"
ADMIN_URL = "https://t.me/theproff991"

# ===================== التخزين الدائم SQLite =====================
DATA_DIR = "/data"
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "bot.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # جدول الطلاب
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        full_name TEXT,
        username TEXT,
        first_name TEXT,
        points INTEGER DEFAULT 0
    )
    """)

    # جدول طلبات المواد
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, subject)
    )
    """)

    conn.commit()
    conn.close()


def save_student(user):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO students (id, full_name, username, first_name, points)
    VALUES (?, ?, ?, ?, 0)
    ON CONFLICT(id) DO UPDATE SET
        full_name = excluded.full_name,
        username = excluded.username,
        first_name = excluded.first_name
    """, (
        user.id,
        user.full_name,
        user.username if user.username else "",
        user.first_name if user.first_name else ""
    ))

    conn.commit()
    conn.close()


def add_points(user_id, points):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE students
    SET points = points + ?
    WHERE id = ?
    """, (points, user_id))

    conn.commit()
    conn.close()


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
    ["👨‍🏫 من هو البروفيسور؟"],
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
    except Exception as e:
        print(f"❌ notify_admin_new_interest failed: {e}")


async def register_request(subject: str, user, context: ContextTypes.DEFAULT_TYPE):
    save_student(user)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*)
    FROM requests
    WHERE student_id = ? AND subject = ?
    """, (user.id, subject))
    exists = cursor.fetchone()[0]

    if exists == 0:
        cursor.execute("""
        INSERT INTO requests (student_id, subject)
        VALUES (?, ?)
        """, (user.id, subject))

        add_points(user.id, 1)

        cursor.execute("""
        SELECT COUNT(*)
        FROM requests
        WHERE subject = ?
        """, (subject,))
        count = cursor.fetchone()[0]

        conn.commit()
        conn.close()

        await notify_admin_new_interest(subject, user, count, context)
    else:
        conn.close()


# ===================== أوامر =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_student(update.effective_user)

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

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT subject, COUNT(*)
    FROM requests
    GROUP BY subject
    ORDER BY COUNT(*) DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("لا توجد طلبات مسجلة بعد.")
        return

    msg = "📊 إحصائيات الطلب على المواد:\n\n"
    for subject, count in rows:
        msg += f"• {subject} : {count}\n"

    await update.message.reply_text(msg)


async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT subject, COUNT(*)
    FROM requests
    GROUP BY subject
    ORDER BY COUNT(*) DESC
    LIMIT 10
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("لا توجد بيانات بعد.")
        return

    msg = "🔥 أعلى 10 مواد طلبًا:\n\n"
    for i, (subject, count) in enumerate(rows, start=1):
        msg += f"{i}) {subject} — {count}\n"

    await update.message.reply_text(msg)


async def ready_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(READY_SUBJECTS))
    cursor.execute(f"""
    SELECT subject, COUNT(*)
    FROM requests
    WHERE subject IN ({placeholders})
    GROUP BY subject
    ORDER BY COUNT(*) DESC
    """, tuple(READY_SUBJECTS.keys()))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("لا توجد طلبات على المواد الجاهزة بعد.")
        return

    msg = "✅ إحصائيات المواد الجاهزة:\n\n"
    for subject, count in rows:
        msg += f"• {subject} : {count}\n"

    await update.message.reply_text(msg)


async def students_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    count = cursor.fetchone()[0]
    conn.close()

    await update.message.reply_text(f"👨‍🎓 عدد الطلاب المسجلين: {count}")


async def my_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT points
    FROM students
    WHERE id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("لا يوجد لديك حساب نقاط بعد.")
        return

    points = row[0]
    await update.message.reply_text(
        f"⭐ نقاطك مع البروفيسور: {points}\n\n"
        "كلما زادت نقاطك، اقتربت من خصومات أفضل."
    )


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


async def send_about_professor(update: Update):
    await update.message.reply_text(
        "👨‍🏫 من هو البروفيسور؟\n\n"
        "البروفيسور هو دكتور صيدلة بخبرة أكثر من 10 سنوات في التدريس.\n"
        "طريقته مختلفة: ما بعلّمك تحفظ السؤال… بل تفهم فكرته 🧠\n\n"
        "يعتمد على تحليل تفكير الدكاترة،\n"
        "مراجعة سنوات الامتحانات القديمة،\n"
        "ودراسة التفاريغ وكل ما يخص المادة.\n\n"
        "ومن خلال هذا التحليل يحدد:\n"
        "🎯 الأفكار الرئيسية والمتكررة في الامتحانات\n\n"
        "ثم يقدّم:\n"
        "📚 أسئلة سنوات متوقعة\n"
        "مع شرحها الكامل بطريقة تخليك تفهم الفكرة.\n\n"
        "لأن السؤال ممكن يجي بنفس الفكرة لكن بصياغة مختلفة،\n"
        "فهدفه إنك تعرف تحل أي سؤال بثقة وليس تحفظه كوبي-بيست.\n\n"
        "والدليل؟\n"
        "اسألوا زملاءكم اللي درسوا معه…\n"
        "الفيدباك منهم يحكي القصة كلها ✨"
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

    if text == "👨‍🏫 من هو البروفيسور؟":
        await send_about_professor(update)
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
            "✅ تم تسجيل طلبك بنجاح.\n\n"
            "إذا وصلنا لعدد كافٍ من الطلبات على هذه المادة،\n"
            "رح نعلن عنها رسميًا على القناة إن شاء الله.\n\n"
            "📩 وإذا بدك تستفسر أكثر، تواصل مع البروفيسور من الزر بالأسفل.",
            reply_markup=InlineKeyboardMarkup(btns)
        )
        return

    await update.message.reply_text(
        "اختار من الأزرار الموجودة 👇",
        reply_markup=main_keyboard()
    )


# ===================== تشغيل البوت =====================
def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("ready_stats", ready_stats))
    app.add_handler(CommandHandler("students_stats", students_stats))
    app.add_handler(CommandHandler("points", my_points))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()