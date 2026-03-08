import logging
import json
import os
import tempfile
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.ext import CallbackQueryHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== إعدادات =====================
TOKEN = os.getenv("BOT_TOKEN") or "8654189257:AAHQ7Jdn5-vmLsD5jP4SC-WwrkyWxJO9Fhc"

ADMIN_ID = 8151228673
ADMIN_IDS = {ADMIN_ID}
ADMIN_USERNAME = "@theproff991"
ADMIN_URL = "https://t.me/theproff991"

# ===================== التخزين الدائم =====================
DATA_DIR = "/data"
os.makedirs(DATA_DIR, exist_ok=True)

REQUESTS_FILE = os.path.join(DATA_DIR, "requests_data.json")
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


if not os.path.exists(REQUESTS_FILE):
    save_json_file(REQUESTS_FILE, {"counts": {}, "who": {}})

if not os.path.exists(STUDENTS_FILE):
    save_json_file(STUDENTS_FILE, {"students": {}})

REQUESTS_DATA = load_json_file(REQUESTS_FILE, {"counts": {}, "who": {}})
STUDENTS_DATA = load_json_file(STUDENTS_FILE, {"students": {}})

DATA = REQUESTS_DATA


# ===================== أدوات مساعدة للطلاب =====================
def normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def ensure_student_fields(student: dict):
    if "points" not in student:
        student["points"] = 0
    if "paid" not in student:
        student["paid"] = False
    if "total_paid" not in student:
        student["total_paid"] = 0
    if "payments" not in student:
        student["payments"] = []
    if "subscriptions" not in student:
        student["subscriptions"] = {}
    if "requested_subjects" not in student:
        student["requested_subjects"] = []
    if "full_name" not in student:
        student["full_name"] = ""
    if "username" not in student:
        student["username"] = ""
    if "first_name" not in student:
        student["first_name"] = ""
    if "last_seen" not in student:
        student["last_seen"] = "active"


def save_student(user):
    user_id = str(user.id)

    if user_id not in STUDENTS_DATA["students"]:
        STUDENTS_DATA["students"][user_id] = {
            "id": user.id,
            "full_name": user.full_name,
            "username": user.username if user.username else "",
            "first_name": user.first_name if user.first_name else "",
            "points": 0,
            "last_seen": "active",
            "paid": False,
            "total_paid": 0,
            "payments": [],
            "subscriptions": {},
            "requested_subjects": []
        }
    else:
        student = STUDENTS_DATA["students"][user_id]
        student["full_name"] = user.full_name
        student["username"] = user.username if user.username else ""
        student["first_name"] = user.first_name if user.first_name else ""
        student["last_seen"] = "active"
        ensure_student_fields(student)

    save_json_file(STUDENTS_FILE, STUDENTS_DATA)


def add_points(user_id, points):
    user_id = str(user_id)

    if user_id not in STUDENTS_DATA["students"]:
        return

    student = STUDENTS_DATA["students"][user_id]
    ensure_student_fields(student)
    student["points"] += points
    save_json_file(STUDENTS_FILE, STUDENTS_DATA)


def resolve_student_id(target_text: str):
    target_text = target_text.strip()

    if not target_text:
        return None

    # 1) ID
    if target_text.isdigit():
        if target_text in STUDENTS_DATA["students"]:
            return target_text

    # 2) username
    if target_text.startswith("@"):
        search_username = normalize_text(target_text[1:])
        for student_id, student in STUDENTS_DATA["students"].items():
            username = normalize_text(student.get("username", ""))
            if username == search_username:
                return student_id

    # 3) full name exact
    search_name = normalize_text(target_text)
    for student_id, student in STUDENTS_DATA["students"].items():
        full_name = normalize_text(student.get("full_name", ""))
        if full_name == search_name:
            return student_id

    return None


def build_student_profile_text(student_id: str) -> str:
    student = STUDENTS_DATA["students"][student_id]
    ensure_student_fields(student)

    username = student.get("username", "")
    username_text = f"@{username}" if username else "بدون يوزرنيم"

    requested_subjects = student.get("requested_subjects", [])
    subscriptions = student.get("subscriptions", {})
    payments = student.get("payments", [])

    requested_text = "لا يوجد طلبات مسجلة."
    if requested_subjects:
        requested_text = "\n".join([f"• {subject}" for subject in requested_subjects])

    subscriptions_text = "لا يوجد اشتراكات مدفوعة مسجلة."
    if subscriptions:
        lines = []
        for subject, data in subscriptions.items():
            amount = data.get("amount", 0)
            date = data.get("date", "")
            lines.append(f"• {subject} — {amount} JD — {date}")
        subscriptions_text = "\n".join(lines)

    payments_text = "لا توجد دفعات مسجلة."
    if payments:
        lines = []
        for p in payments:
            lines.append(
                f"• {p.get('subject', 'بدون مادة')} — {p.get('amount', 0)} JD — {p.get('date', '')}"
            )
        payments_text = "\n".join(lines)

    msg = (
        f"📁 ملف الطالب الكامل\n\n"
        f"👤 الاسم: {student.get('full_name', 'بدون اسم')}\n"
        f"🔗 اليوزر: {username_text}\n"
        f"🆔 ID: {student_id}\n"
        f"✅ حالة الدفع العامة: {'دافع' if student.get('paid', False) else 'غير دافع'}\n"
        f"💰 مجموع المدفوع: {student.get('total_paid', 0)} JD\n"
        f"⭐ النقاط: {student.get('points', 0)}\n\n"
        f"📚 كل ما طلبه:\n{requested_text}\n\n"
        f"✅ كل ما اشترك به ودفعه:\n{subscriptions_text}\n\n"
        f"🧾 سجل الدفعات:\n{payments_text}"
    )

    return msg


# ===================== تسجيل طلب مادة =====================
async def notify_admin_new_interest(subject: str, user, count: int, context: ContextTypes.DEFAULT_TYPE):
    try:
        username = f"@{user.username}" if user.username else "بدون يوزرنيم"

        msg = (
            "📊 طلب جديد على مادة\n\n"
            f"📚 المادة: {subject}\n"
            f"👤 الطالب: {user.full_name}\n"
            f"🔗 الحساب: {username}\n"
            f"🆔 ID: {user.id}\n"
            f"📈 العدد الكلي: {count}"
        )

        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        print(f"✅ Admin notified successfully: {subject} / {user.id}")

    except Exception as e:
        print(f"❌ notify_admin_new_interest failed: {e}")


async def register_request(subject: str, user, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(user.id)

    try:
        save_student(user)

        if subject not in DATA["counts"]:
            DATA["counts"][subject] = 0
            DATA["who"][subject] = []

        is_new_request = user_id not in DATA["who"][subject]

        if is_new_request:
            DATA["who"][subject].append(user_id)
            DATA["counts"][subject] += 1

            student = STUDENTS_DATA["students"].get(user_id)
            if student is not None:
                ensure_student_fields(student)
                if subject not in student["requested_subjects"]:
                    student["requested_subjects"].append(subject)
                save_json_file(STUDENTS_FILE, STUDENTS_DATA)

            save_json_file(REQUESTS_FILE, DATA)

        await notify_admin_new_interest(subject, user, DATA["counts"][subject], context)

    except Exception as e:
        print(f"❌ register_request failed: {e}")


# ===================== المواد الجاهزة حسب المادة + نوع الامتحان =====================
READY_SUBJECTS = {
    ("لاب مايكرو", "ميد"): (
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

    ("فايتو صيدلة", "فيرست"): (
        "🌿 قناة متوقّع البروفيسور – فايتو صيدلة\n\n"
        "القناة تحتوي على:\n"
        "✔ سنوات أسئلة\n"
        "✔ إجاباتها الكاملة\n\n"
        "💰 الاشتراك: 3 دنانير\n\n"
        "💳 الدفع عبر زين كاش:\n"
        "📱 0798024692\n\n"
        "📸 بعد التحويل اضغط الزر بالأسفل وابعت صورة الوصل للبروفيسور."
    ),

    ("فايتوثيرابي صيدلة", "فيرست"): (
        "🌿 قناة متوقّع البروفيسور – فايتوثيرابي صيدلة\n\n"
        "القناة تحتوي على:\n"
        "✔ أسئلة سنوات متوقعة مع إجاباتها\n\n"
        "💰 الاشتراك: 4 دنانير\n\n"
        "💳 الدفع عبر زين كاش:\n"
        "📱 0798024692\n\n"
        "📸 بعد التحويل اضغط الزر بالأسفل وابعت صورة الوصل للبروفيسور."
    ),

    ("ميدو 2", "فيرست"): (
        "😎 طلاب ميدو 2\n"
        "فيرست\n\n"
        "📚 فيديوهات سنوات + متوقّع البروفيسور\n"
        "⏱️ مدة الشرح تقريبًا ساعتين\n"
        "شرح السؤال كامل + مراجعة نوع الدواء + SAR خطوة خطوة 👨‍🏫\n\n"
        "💰 سعر الاشتراك: ٨ دنانير\n\n"
        "💳 الدفع عبر زين كاش:\n"
        "📱 0798024692\n\n"
        "📸 يرجى تصوير وصل التحويل\n"
        "وإرساله عالخاص للتأكيد ✔"
    ),

    ("ميدو 1", "فيرست"): (
        "😎 طلاب ميدو 1\n"
        "فيرست\n\n"
        "📚 فيديوهات سنوات + متوقّع البروفيسور\n"
        "⏱️ مدة الشرح تقريبًا اربع ساعات\n"
        "شرح السؤال كامل +\n"
        "مراجعة نوع الدواء + SAR خطوة خطوة 👨‍🏫\n"
        "ما في داعي تدرس اصلا 😹\n\n"
        "💰 سعر الاشتراك: ١٠ دنانير\n\n"
        "💳 الدفع عبر زين كاش:\n"
        "📱 0798024692\n\n"
        "📸 يرجى تصوير وصل التحويل\n"
        "وإرساله عالخاص للتأكيد ✔"
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

EXAM_TYPE_MENU = [
    ["فيرست", "سكند"],
    ["فاينال", "ميد"],
    ["⬅️ رجوع للقائمة الرئيسية"],
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


def exam_type_keyboard():
    return ReplyKeyboardMarkup(EXAM_TYPE_MENU, resize_keyboard=True)


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


async def ready_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    counts = DATA.get("counts", {})
    ready_counts = {
        k: v for k, v in counts.items()
        if any(k == f"{subject} - {exam}" for (subject, exam) in READY_SUBJECTS.keys())
    }

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


async def my_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    student = STUDENTS_DATA["students"].get(user_id)
    if not student:
        await update.message.reply_text("لا يوجد لديك حساب نقاط بعد.")
        return

    ensure_student_fields(student)
    points = student.get("points", 0)
    await update.message.reply_text(
        f"⭐ نقاطك مع البروفيسور: {points}\n\n"
        "✅ النقاط تُحتسب بعد تأكيد الدفع فقط.\n"
        "كلما زادت نقاطك اقتربت من خصومات أفضل."
    )


async def my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    student = STUDENTS_DATA["students"].get(user_id)
    if not student:
        await update.message.reply_text("لا توجد لديك طلبات مسجلة بعد.")
        return

    ensure_student_fields(student)
    requested_subjects = student.get("requested_subjects", [])

    if not requested_subjects:
        await update.message.reply_text("لا توجد لديك طلبات مسجلة بعد.")
        return

    msg = "📚 المواد التي طلبتها:\n\n"
    for subject in requested_subjects:
        msg += f"• {subject}\n"

    await update.message.reply_text(msg)


async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "استخدم الأمر هكذا:\n"
            "/paid @username اسم المادة - نوع الامتحان 7\n"
            "مثال:\n"
            "/paid @ahmad لاب مايكرو - ميد 7"
        )
        return

    target_text = context.args[0].strip()
    amount_text = context.args[-1].strip()
    subject_text = " ".join(context.args[1:-1]).strip()

    try:
        amount = float(amount_text)
    except Exception:
        await update.message.reply_text("المبلغ غير صحيح.")
        return

    if not subject_text:
        await update.message.reply_text("اكتب اسم المادة بين اسم الطالب والمبلغ.")
        return

    found_student_id = resolve_student_id(target_text)

    if not found_student_id:
        await update.message.reply_text("لم أجد هذا الطالب في البيانات.")
        return

    student = STUDENTS_DATA["students"][found_student_id]
    ensure_student_fields(student)

    payment_record = {
        "amount": amount,
        "subject": subject_text,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "confirmed_by": uid
    }

    student["paid"] = True
    student["total_paid"] += amount
    student["points"] += int(amount)
    student["payments"].append(payment_record)
    student["subscriptions"][subject_text] = {
        "paid": True,
        "amount": amount,
        "date": payment_record["date"]
    }

    save_json_file(STUDENTS_FILE, STUDENTS_DATA)

    try:
        await context.bot.send_message(
            chat_id=int(found_student_id),
            text=(
                "✅ تم تأكيد الدفع بنجاح\n\n"
                f"📚 المادة: {subject_text}\n"
                f"💰 المبلغ المسجل: {amount} JD\n"
                f"⭐ نقاطك الحالية: {student['points']}\n\n"
                "شكرًا لك 🌟"
            )
        )
    except Exception as e:
        print(f"❌ failed to notify student: {e}")

    username_text = f"@{student.get('username', '')}" if student.get("username") else "بدون يوزرنيم"

    await update.message.reply_text(
        f"✅ تم تأكيد الدفع للطالب:\n"
        f"👤 الاسم: {student.get('full_name', 'بدون اسم')}\n"
        f"🔗 اليوزر: {username_text}\n"
        f"🆔 ID: {found_student_id}\n"
        f"📚 المادة: {subject_text}\n"
        f"💰 المبلغ: {amount} JD\n"
        f"⭐ النقاط الحالية: {student['points']}"
    )


async def profits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    total_revenue = 0
    paid_students = 0
    subject_revenue = {}

    for student in STUDENTS_DATA["students"].values():
        ensure_student_fields(student)

        amount = student.get("total_paid", 0)
        if amount > 0:
            paid_students += 1
            total_revenue += amount

        for payment in student.get("payments", []):
            subject = payment.get("subject", "بدون مادة")
            value = payment.get("amount", 0)
            subject_revenue[subject] = subject_revenue.get(subject, 0) + value

    msg = (
        f"💰 إجمالي الأرباح: {total_revenue} JD\n"
        f"👨‍🎓 عدد الطلاب الدافعين: {paid_students}\n\n"
    )

    if subject_revenue:
        msg += "📚 الأرباح حسب المادة:\n"
        for subject, value in sorted(subject_revenue.items(), key=lambda x: x[1], reverse=True):
            msg += f"• {subject}: {value} JD\n"

    await update.message.reply_text(msg)


async def student_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    if not context.args:
        await update.message.reply_text(
            "استخدم الأمر هكذا:\n"
            "/student @username\n"
            "/student 123456789\n"
            "/student الاسم الكامل"
        )
        return

    target_text = " ".join(context.args).strip()
    found_student_id = resolve_student_id(target_text)

    if not found_student_id:
        await update.message.reply_text("هذا الطالب غير موجود.")
        return

    await update.message.reply_text(build_student_profile_text(found_student_id))


async def student_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await student_profile(update, context)


# ===================== الرسائل العامة =====================
async def send_subscription_guide(update: Update):
    btns = [[InlineKeyboardButton("📩 تواصل مع البروفيسور", url=ADMIN_URL)]]
    await update.message.reply_text(
        "💳 طريقة الاشتراك:\n\n"
        "1) اختر المادة\n"
        "2) اختر نوع الامتحان\n"
        "3) حوّل المبلغ عبر زين كاش\n"
        "4) اضغط زر إرسال وصل الدفع\n"
        "5) ابعت صورة الوصل للبروفيسور\n"
        "6) بعد التأكيد رح تستلم رابط القناة\n\n"
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
        context.user_data.pop("pending_subject", None)

        await update.message.reply_text(
            "رجعناك للقائمة الرئيسية ✅",
            reply_markup=main_keyboard()
        )
        return

    if text == "✅ المواد الجاهزة الآن":
        ready_subject_names = sorted(list({subject for subject, exam in READY_SUBJECTS.keys()}))
        await update.message.reply_text(
            "اختر مادة جاهزة 👇",
            reply_markup=section_keyboard(ready_subject_names)
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

    ready_subject_names = {subject for subject, exam in READY_SUBJECTS.keys()}

    if text in ready_subject_names:
        context.user_data["pending_subject"] = text

        await update.message.reply_text(
            f"📚 المادة: {text}\n\nاختر نوع الامتحان المطلوب 👇",
            reply_markup=exam_type_keyboard()
        )
        return

    if text in ALL_SUBJECTS:
        context.user_data["pending_subject"] = text

        await update.message.reply_text(
            f"📚 المادة: {text}\n\nاختر نوع الامتحان المطلوب 👇",
            reply_markup=exam_type_keyboard()
        )
        return

    if text in ["فيرست", "سكند", "فاينال", "ميد"]:
        pending_subject = context.user_data.get("pending_subject")

        if not pending_subject:
            await update.message.reply_text(
                "اختار المادة أولًا 👇",
                reply_markup=main_keyboard()
            )
            return

        full_subject = f"{pending_subject} - {text}"
        await register_request(full_subject, user, context)

        ready_key = (pending_subject, text)

        if ready_key in READY_SUBJECTS:
            btns = [[InlineKeyboardButton("📩 إرسال وصل الدفع للبروفيسور", url=ADMIN_URL)]]
            await update.message.reply_text(
                READY_SUBJECTS[ready_key] + f"\n\n📝 الامتحان المختار: {text}",
                reply_markup=InlineKeyboardMarkup(btns)
            )
        else:
            btns = [[InlineKeyboardButton("📩 تواصل مع البروفيسور", url=ADMIN_URL)]]
            await update.message.reply_text(
                f"📚 المادة: {pending_subject}\n"
                f"📝 الامتحان: {text}\n\n"
                "✅ تم تسجيل طلبك بنجاح.\n\n"
                "إذا وصلنا لعدد كافٍ من الطلبات على هذا الجزء،\n"
                "رح نعلن عنه رسميًا على القناة إن شاء الله.\n\n"
                "📩 وإذا بدك تستفسر أكثر، تواصل مع البروفيسور من الزر بالأسفل.",
                reply_markup=InlineKeyboardMarkup(btns)
            )

        context.user_data.pop("pending_subject", None)
        return

    await update.message.reply_text(
        "اختار من الأزرار الموجودة 👇",
        reply_markup=main_keyboard()
    )


# ===================== الأوامر غير المعروفة =====================
async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if not text.startswith("/"):
        return

    uid = update.effective_user.id

    if uid in ADMIN_IDS:
        raw = text[1:].strip()

        known_commands = {
    "start",
    "myid",
    "stats",
    "top",
    "ready_stats",
    "students_stats",
    "subject",
    "points",
    "paid",
    "profits",
    "studentpay",
    "student",
    "myrequests",
    "leaderboard",
    "fixpayment"
}

        if raw and " " not in raw and raw.lower() not in known_commands:
            target = f"@{raw}"
            found_student_id = resolve_student_id(target)
            if found_student_id:
                await update.message.reply_text(build_student_profile_text(found_student_id))
                return

    await update.message.reply_text("أمر غير معروف.")


# ===================== leaderboard =====================
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    students = []
    for student_id, student in STUDENTS_DATA["students"].items():
        ensure_student_fields(student)

        students.append({
            "name": student.get("full_name", "بدون اسم"),
            "username": student.get("username", ""),
            "points": student.get("points", 0),
            "paid": student.get("total_paid", 0)
        })

    students = sorted(students, key=lambda x: x["points"], reverse=True)

    msg = "🏆 أعلى الطلاب بالنقاط\n\n"

    for i, s in enumerate(students[:10], start=1):
        username = f"@{s['username']}" if s["username"] else ""
        msg += f"{i}) {s['name']} {username}\n⭐ {s['points']} نقطة | 💰 {s['paid']} JD\n\n"

    await update.message.reply_text(msg)


async def subject_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    if not context.args:
        await update.message.reply_text(
            "استخدم الأمر هكذا:\n"
            "/subject لاب مايكرو - ميد"
        )
        return

    subject_name = " ".join(context.args).strip()

    request_count = DATA.get("counts", {}).get(subject_name, 0)

    paid_students = []
    total_revenue = 0

    for student_id, student in STUDENTS_DATA["students"].items():

        ensure_student_fields(student)

        subscriptions = student.get("subscriptions", {})

        if subject_name in subscriptions:

            amount = subscriptions[subject_name].get("amount", 0)
            total_revenue += amount

            paid_students.append({
                "name": student.get("full_name", "بدون اسم"),
                "username": student.get("username", ""),
                "points": student.get("points", 0),
                "amount": amount
            })

    msg = (
        f"📚 المادة: {subject_name}\n\n"
        f"📈 عدد الطلبات: {request_count}\n"
        f"💰 عدد المشتركين: {len(paid_students)}\n"
        f"💵 مجموع الربح: {total_revenue} JD\n\n"
    )

    if paid_students:

        msg += "👨‍🎓 الطلاب المشتركين:\n\n"

        for i, s in enumerate(paid_students, start=1):

            username = f"@{s['username']}" if s["username"] else ""

            msg += (
                f"{i}) {s['name']} {username}\n"
                f"💰 دفع: {s['amount']} JD\n"
                f"⭐ نقاطه: {s['points']}\n\n"
            )

    else:
        msg += "لا يوجد طلاب دافعين لهذه المادة."

    await update.message.reply_text(msg)

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    if not context.args:
        await update.message.reply_text(
            "استخدم الأمر هكذا:\n"
            "/subject لاب مايكرو - ميد"
        )
        return

    subject_name = " ".join(context.args).strip()

    request_count = DATA.get("counts", {}).get(subject_name, 0)

    paid_count = 0
    total_revenue = 0

    for student_id, student in STUDENTS_DATA["students"].items():

        subscriptions = student.get("subscriptions", {})

        if subject_name in subscriptions:
            paid_count += 1
            amount = subscriptions[subject_name].get("amount", 0)
            total_revenue += amount

    msg = (
        f"📚 المادة: {subject_name}\n\n"
        f"📈 عدد الطلبات: {request_count}\n"
        f"💰 عدد المشتركين الدافعين: {paid_count}\n"
        f"💵 مجموع الربح: {total_revenue} JD"
    )

    await update.message.reply_text(msg)
    
    
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "admin_dashboard":
        await dashboard(update, context)

    elif data == "admin_leaderboard":
        await leaderboard(update, context)

    elif data == "admin_profits":
        await profits(update, context)

    elif data == "admin_top":
        await top(update, context)

    elif data == "admin_students":
        await students_stats(update, context)

    elif data == "admin_student":
        await query.message.reply_text(
            "استخدم الأمر هكذا:\n"
            "/student @username"
        )

    elif data == "admin_paid":
        await query.message.reply_text(
            "تأكيد الدفع:\n"
            "/paid @username اسم المادة - نوع الامتحان 7"
        )

    elif data == "admin_subject":
        await query.message.reply_text(
            "إحصائية مادة:\n"
            "/subject لاب مايكرو - ميد"
        )
    
    
async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    students_count = len(STUDENTS_DATA["students"])

    total_revenue = 0
    total_points = 0
    subject_revenue = {}

    for student in STUDENTS_DATA["students"].values():
        ensure_student_fields(student)

        total_revenue += student.get("total_paid", 0)
        total_points += student.get("points", 0)

        for payment in student.get("payments", []):
            subject = payment.get("subject", "بدون مادة")
            amount = payment.get("amount", 0)

            subject_revenue[subject] = subject_revenue.get(subject, 0) + amount

    msg = (
        "📊 لوحة تحكم البروفيسور\n\n"
        f"👨‍🎓 عدد الطلاب: {students_count}\n"
        f"💰 إجمالي الأرباح: {total_revenue} JD\n"
        f"⭐ مجموع النقاط: {total_points}\n"
    )

    await update.message.reply_text(msg)


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    if uid not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    buttons = [
        [InlineKeyboardButton("📊 Dashboard", callback_data="admin_dashboard")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="admin_leaderboard")],
        [InlineKeyboardButton("💰 الأرباح", callback_data="admin_profits")],
        [InlineKeyboardButton("📚 أكثر المواد طلبًا", callback_data="admin_top")],
        [InlineKeyboardButton("👨‍🎓 عدد الطلاب", callback_data="admin_students")],
        [InlineKeyboardButton("👤 ملف طالب", callback_data="admin_student")],
        [InlineKeyboardButton("💳 تأكيد دفع", callback_data="admin_paid")],
        [InlineKeyboardButton("📊 إحصائية مادة", callback_data="admin_subject")]
    ]

    await update.message.reply_text(
        "⚙️ لوحة تحكم البروفيسور",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "admin_dashboard":
        await dashboard(query, context)

    elif data == "admin_leaderboard":
        await leaderboard(query, context)

    elif data == "admin_profits":
        await profits(query, context)

    elif data == "admin_top":
        await top(query, context)

    elif data == "admin_students":
        await students_stats(query, context)

    elif data == "admin_student":
        await query.message.reply_text(
            "استخدم الأمر:\n/student @username"
        )

    elif data == "admin_paid":
        await query.message.reply_text(
            "لتأكيد الدفع استخدم:\n/paid @username المادة - الامتحان 7"
        )

    elif data == "admin_subject":
        await query.message.reply_text(
            "إحصائية مادة:\n/subject لاب مايكرو - ميد"
        )
    
    
# ===================== تشغيل البوت =====================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("ready_stats", ready_stats))
    app.add_handler(CommandHandler("students_stats", students_stats))
    app.add_handler(CommandHandler("subject", subject_stats))
    app.add_handler(CommandHandler("points", my_points))
    app.add_handler(CommandHandler("myrequests", my_requests))

    app.add_handler(CommandHandler("paid", paid))
    app.add_handler(CommandHandler("profits", profits))
    app.add_handler(CommandHandler("studentpay", student_payment))
    app.add_handler(CommandHandler("student", student_profile))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_buttons))
    app.add_handler(CommandHandler("dashboard", dashboard))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
