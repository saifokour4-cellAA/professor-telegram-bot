import logging
import json
import os
import tempfile

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, CallbackQueryHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_json_file(path, default_data):
    if not os.path.exists(path):
        return default_data
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ File {path} contains invalid JSON. Using default.")
        return default_data
    except Exception as e:
        print(f"❌ Error reading {path}: {e}")
        return default_data

def save_json_file(path, data):
    # atomic write
    dirpath = os.path.dirname(path)
    os.makedirs(dirpath, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception as e:
        print(f"❌ Error saving {path}: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# ===================== إعدادات =====================
TOKEN = "8654189257:AAFET6wtMjvjrPsBeRH-ueLIRAXhptMospc"
ADMIN_ID = 8151228673
ADMIN_IDS = {ADMIN_ID}
ADMIN_USERNAME = "@theproff991"
ADMIN_URL = "https://t.me/theproff991"
# ===================== التخزين الدائم =====================
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
os.makedirs(DATA_DIR, exist_ok=True)

REQUESTS_FILE = os.path.join(DATA_DIR, "requests_data.json")
VOTES_FILE = os.path.join(DATA_DIR, "votes_data.json")
STUDENTS_FILE = os.path.join(DATA_DIR, "students_data.json")


def load_json_file(path, default_data):
    if not os.path.exists(path):
        return default_data
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ File {path} contains invalid JSON. Using default.")
        return default_data
    except Exception as e:
        print(f"❌ Error reading {path}: {e}")
        return default_data


def save_json_file(path, data):
    dirpath = os.path.dirname(path)
    os.makedirs(dirpath, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception as e:
        print(f"❌ Error saving {path}: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


REQUESTS_DATA = load_json_file(REQUESTS_FILE, {"counts": {}, "who": {}})
VOTES_DATA = load_json_file(VOTES_FILE, {"votes": {}, "voters": {}})
STUDENTS_DATA = load_json_file(STUDENTS_FILE, {"students": {}})

USER_TEMP_VOTES = {}

DATA = REQUESTS_DATA
VOTES = VOTES_DATA["votes"]
VOTERS = VOTES_DATA["voters"]


def save_student(user):
    user_id = str(user.id)

    STUDENTS_DATA["students"][user_id] = {
        "id": user.id,
        "full_name": user.full_name,
        "username": user.username if user.username else "",
        "first_name": user.first_name if user.first_name else "",
        "last_seen": "active"
    }

    save_json_file(STUDENTS_FILE, STUDENTS_DATA)
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
VOTE_SUBJECTS = BASIC_SUBJECTS + LAB_SUBJECTS + PHARMD_SUBJECTS

MAIN_MENU = [
    ["✅ المواد الجاهزة الآن", "📚 المواد الأساسية"],
    ["🧪 اللابات", "🎓 مواد دكتور صيدلة"],
    ["💳 كيف أشترك؟", "📩 تواصل مع البروفيسور"],
    ["📊 التصويت على المواد", "👨‍🏫 من هو البروفيسور؟"],
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
    user_id = str(user.id)

    save_student(user)

    if subject not in DATA["counts"]:
        DATA["counts"][subject] = 0
        DATA["who"][subject] = []

    if user_id not in DATA["who"][subject]:
        DATA["who"][subject].append(user_id)
        DATA["counts"][subject] += 1
        save_json_file(REQUESTS_FILE, DATA)
        await notify_admin_new_interest(subject, user, DATA["counts"][subject], context)
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


async def voters_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    if not VOTERS:
        await update.message.reply_text("لا يوجد مصوتون بعد.")
        return

    msg = "🗳️ تفاصيل المصوتين:\n\n"

    for subject in sorted(VOTERS.keys(), key=lambda s: VOTES.get(s, 0), reverse=True):
        voter_ids = VOTERS.get(subject, [])
        msg += f"📚 {subject} ({len(voter_ids)})\n"

        if not voter_ids:
            msg += "— لا يوجد أحد\n\n"
            continue

        for voter_id in voter_ids:
            student = STUDENTS_DATA["students"].get(str(voter_id), {})
            full_name = student.get("full_name", "بدون اسم")
            username = student.get("username", "")

            if username:
                msg += f"• {full_name} (@{username})\n"
            else:
                msg += f"• {full_name}\n"

        msg += "\n"

    if len(msg) <= 4000:
        await update.message.reply_text(msg)
    else:
        parts = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
        for part in parts:
            await update.message.reply_text(part)


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

    await update.message.reply_text(msg)


async def students_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    students_count = len(STUDENTS_DATA["students"])
    await update.message.reply_text(f"👨‍🎓 عدد الطلاب المحفوظين: {students_count}")
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

    if text == "📊 التصويت على المواد":
        await vote(update, context)
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
# ===================== أوامر التصويت =====================

def build_vote_keyboard(user_id):
    keyboard = []

    for i, subject in enumerate(VOTE_SUBJECTS):
        temp_selected = i in USER_TEMP_VOTES.get(user_id, set())
        already_voted = str(user_id) in VOTERS.get(subject, [])

        selected = temp_selected or already_voted
        mark = "✅" if selected else "⬜"
        count = VOTES.get(subject, 0)

        keyboard.append([
            InlineKeyboardButton(
                f"{mark} {subject} ({count})",
                callback_data=f"tv|{i}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("🟢 تأكيد التصويت", callback_data="cv")
    ])

    keyboard.append([
        InlineKeyboardButton("📊 تحديث النتائج", callback_data="rv")
    ])

    return InlineKeyboardMarkup(keyboard)


def build_vote_text():
    msg = "📊 التصويت على المواد\n\n"
    msg += "اختر مادة أو أكثر، والنتائج تظهر مباشرة أول بأول:\n\n"

    for subject in VOTE_SUBJECTS:
        count = VOTES.get(subject, 0)
        msg += f"• {subject}: {count}\n"

    return msg


async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_student(update.effective_user)

    if user_id not in USER_TEMP_VOTES:
        USER_TEMP_VOTES[user_id] = set()

    await update.message.reply_text(
        build_vote_text(),
        reply_markup=build_vote_keyboard(user_id)
    )


async def vote_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    save_student(user)

    if user_id not in USER_TEMP_VOTES:
        USER_TEMP_VOTES[user_id] = set()

    data = query.data

    # اختيار أو إزالة اختيار مادة
    if data.startswith("tv|"):
        idx = int(data.split("|", 1)[1])

        if idx in USER_TEMP_VOTES[user_id]:
            USER_TEMP_VOTES[user_id].remove(idx)
        else:
            USER_TEMP_VOTES[user_id].add(idx)

        await query.edit_message_text(
            build_vote_text(),
            reply_markup=build_vote_keyboard(user_id)
        )
        return

    # تأكيد التصويت
    if data == "cv":
        selected_indexes = USER_TEMP_VOTES.get(user_id, set())

        if not selected_indexes:
            await query.edit_message_text(
                "⚠️ لم تختر أي مادة بعد.\n\n" + build_vote_text(),
                reply_markup=build_vote_keyboard(user_id)
            )
            return

        selected_subjects = []

        for idx in selected_indexes:
            subject = VOTE_SUBJECTS[idx]
            selected_subjects.append(subject)

            if subject not in VOTES:
                VOTES[subject] = 0
                VOTERS[subject] = []

            if str(user_id) not in VOTERS[subject]:
                VOTERS[subject].append(str(user_id))
                VOTES[subject] += 1

        save_json_file(VOTES_FILE, {"votes": VOTES, "voters": VOTERS})

        USER_TEMP_VOTES[user_id] = set()

        try:
            username = f"@{user.username}" if user.username else "بدون يوزرنيم"
            subjects_text = "\n".join([f"• {s}" for s in selected_subjects])

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "🗳️ تصويت جديد\n\n"
                    f"👤 الاسم: {user.full_name}\n"
                    f"🔗 الحساب: {username}\n\n"
                    f"📚 المواد المختارة:\n{subjects_text}"
                )
            )
        except Exception as e:
            print(f"vote admin notify failed: {e}")

        await query.edit_message_text(
            "✅ تم تسجيل تصويتك بنجاح.\n\n" + build_vote_text(),
            reply_markup=build_vote_keyboard(user_id)
        )
        return

   # تحديث النتائج
    if data == "rv":
        await query.edit_message_text(
            build_vote_text(),
            reply_markup=build_vote_keyboard(user_id)
        )
        return


async def vote_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.
# ===================== تشغيل البوت =====================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # أوامر البوت
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("ready_stats", ready_stats))
    app.add_handler(CommandHandler("students_stats", students_stats))

    # أوامر التصويت
    app.add_handler(CommandHandler("vote", vote))
    app.add_handler(CommandHandler("vote_results", vote_results))
    app.add_handler(CommandHandler("voters", voters_stats))

    # أزرار التصويت (Inline buttons)
    app.add_handler(
        CallbackQueryHandler(
            vote_button,
            pattern="^(tv\\|\\d+|cv|rv)$"
        )
    )

    # استقبال الرسائل العادية من الأزرار
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()

