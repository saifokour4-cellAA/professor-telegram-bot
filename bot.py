import logging
import json
import os
import tempfile

from datetime import datetime, time
from zoneinfo import ZoneInfo

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from openai import AsyncOpenAI


# =========================================================
# OpenAI Setup
# =========================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


async def ask_gpt(user_text: str) -> str:
    if not client:
        return "❌ مفتاح OpenAI غير موجود في متغيرات Railway."

    try:
        response = await client.responses.create(
            model="gpt-5",
            input=[
                {
                    "role": "system",
                    "content": (
                        "أنت البروفيسور 👑. "
                        "تشرح لطلاب pharmacy بأسلوبنا المعروف: mix عربي + English، "
                        "مع الحفاظ على المصطلحات الطبية والصيدلانية والسريرية بالإنجليزي غالبًا. "

                        "مهم جدًا جدًا: "
                        "لا تعرض menu. "
                        "لا تقترح topics من نفسك. "
                        "لا تسرد أمثلة أو مواد أو عناوين إلا إذا طلب المستخدم ذلك. "
                        "لا تكرر أي أمثلة سابقة أو نماذج شرح أُعطيت لك كأمثلة أسلوب. "
                        "لا تقل: ابعتلي topic. "
                        "لا تقل: نولع pharmacy mode. "
                        "لا تحكي عن أسلوبك أو طريقتك أو أنك ستشرح بطريقة البروفيسور. "
                        "ادخل مباشرة في الرد المناسب فقط. "

                        "قواعد السلوك: "
                        "1) إذا كانت الرسالة casual مثل: مرحبا، السلام عليكم، هلا، صباح الخير → "
                        "رد قصير طبيعي جدًا ولطيف بدون إطالة. "
                        "2) إذا كانت الرسالة سؤالًا علميًا أو دوائيًا أو أكاديميًا → ابدأ مباشرة بالشرح. "
                        "3) إذا كان السؤال MCQ أو exam-style → "
                        "أعطِ الجواب بهذا الشكل غالبًا: "
                        "✅ Correct answer "
                        "🧠 الشرح (Brain-Lock 🔒) "
                        "❌ ليش الباقي غلط؟ "
                        "🎯 Exam Pearl "
                        "4) إذا كان السؤال topic/explanation → "
                        "قسم الشرح بشكل مرتب وواضح، مع mix عربي + English، وبدون حشو. "
                        "5) استخدم كلمات مثل: شوف، ركز معي، هون الفكرة، يعني بالمختصر، الزبدة، انتبه هون. "
                        "6) لا تكن رسميًا أو روبوتيًا. "
                        "7) لا تطل إذا كانت الرسالة قصيرة وبسيطة. "
                        "8) لا تضف أي شيء غير مطلوب من نفسك. "
                        "9) إذا السؤال طبي/دوائي حساس، كن accurate جدًا. "
                        "10) إذا الشرح كان علمي، خليه structured, engaging, exam-oriented."
                    )
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ],
            max_output_tokens=500
        )

        return response.output_text.strip()

    except Exception as e:
        print(f"❌ GPT error: {e}")
        return f"❌ صار خطأ أثناء الاتصال بـ GPT:\n{e}"


# =========================================================
# Logging
# =========================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =========================================================
# Settings
# =========================================================
TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"

ADMIN_ID = 8151228673
ADMIN_IDS = {ADMIN_ID}
ADMIN_USERNAME = "@theproff991"
ADMIN_URL = "https://t.me/theproff991"
MAIN_CHANNEL_ID = "@TheProfessoR199"
BOT_USERNAME = "theprofessor26bot"


# =========================================================
# Persistent Storage
# =========================================================
DATA_DIR = "/data"
os.makedirs(DATA_DIR, exist_ok=True)

REQUESTS_FILE = os.path.join(DATA_DIR, "requests_data.json")
STUDENTS_FILE = os.path.join(DATA_DIR, "students_data.json")
POSTED_RAMADAN_FILE = os.path.join(DATA_DIR, "posted_ramadan.json")
QUIZ_FILE = os.path.join(DATA_DIR, "ramadan_quiz_data.json")


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

if not os.path.exists(POSTED_RAMADAN_FILE):
    save_json_file(POSTED_RAMADAN_FILE, {"posted_dates": []})

if not os.path.exists(QUIZ_FILE):
    save_json_file(QUIZ_FILE, {
        "current_quiz": None,
        "quizzes": {},
        "participants": {}
    })

REQUESTS_DATA = load_json_file(REQUESTS_FILE, {"counts": {}, "who": {}})
STUDENTS_DATA = load_json_file(STUDENTS_FILE, {"students": {}})
POSTED_RAMADAN_DATA = load_json_file(POSTED_RAMADAN_FILE, {"posted_dates": []})
QUIZ_DATA = load_json_file(QUIZ_FILE, {
    "current_quiz": None,
    "quizzes": {},
    "participants": {}
})

DATA = REQUESTS_DATA


# =========================================================
# Helpers
# =========================================================
def normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def amman_now():
    return datetime.now(ZoneInfo("Asia/Amman"))


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
            "requested_subjects": [],
        }
    else:
        student = STUDENTS_DATA["students"][user_id]
        student["full_name"] = user.full_name
        student["username"] = user.username if user.username else ""
        student["first_name"] = user.first_name if user.first_name else ""
        student["last_seen"] = "active"
        ensure_student_fields(student)

    save_json_file(STUDENTS_FILE, STUDENTS_DATA)


def resolve_student_id(target_text: str):
    target_text = (target_text or "").strip()

    if not target_text:
        return None

    if target_text.isdigit():
        if target_text in STUDENTS_DATA["students"]:
            return target_text

    if target_text.startswith("@"):
        search_username = normalize_text(target_text[1:])
        for student_id, student in STUDENTS_DATA["students"].items():
            username = normalize_text(student.get("username", ""))
            if username == search_username:
                return student_id

    search_name = normalize_text(target_text)
    for student_id, student in STUDENTS_DATA["students"].items():
        full_name = normalize_text(student.get("full_name", ""))
        if full_name == search_name:
            return student_id

    return None


def get_quiz_ranking():
    participants = QUIZ_DATA.get("participants", {})
    return sorted(
        participants.values(),
        key=lambda x: (x.get("points", 0), x.get("correct_count", 0)),
        reverse=True
    )


def get_user_rank(user_id: str):
    ranking = get_quiz_ranking()
    for idx, participant in enumerate(ranking, start=1):
        if str(participant.get("id")) == str(user_id):
            return idx
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


def build_dashboard_text() -> str:
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

    most_requested = None
    if DATA.get("counts"):
        most_requested = max(DATA["counts"].items(), key=lambda x: x[1])

    most_profitable = None
    if subject_revenue:
        most_profitable = max(subject_revenue.items(), key=lambda x: x[1])

    best_student = None
    if STUDENTS_DATA["students"]:
        best_student = max(
            STUDENTS_DATA["students"].values(),
            key=lambda s: s.get("points", 0)
        )

    msg = (
        "📊 لوحة تحكم البروفيسور\n\n"
        f"👨‍🎓 عدد الطلاب: {students_count}\n"
        f"💰 إجمالي الأرباح: {total_revenue} JD\n"
        f"⭐ مجموع النقاط: {total_points}\n\n"
    )

    if most_requested:
        msg += f"🔥 أكثر مادة طلبًا:\n{most_requested[0]} ({most_requested[1]} طلب)\n\n"

    if most_profitable:
        msg += f"💵 أكثر مادة ربحًا:\n{most_profitable[0]} ({most_profitable[1]} JD)\n\n"

    if best_student:
        username = f"@{best_student.get('username','')}" if best_student.get("username") else ""
        msg += (
            "🏆 أفضل طالب:\n"
            f"{best_student.get('full_name','')} {username}\n"
            f"⭐ {best_student.get('points',0)} نقطة\n"
            f"💰 {best_student.get('total_paid',0)} JD\n"
        )

    return msg


def build_leaderboard_text() -> str:
    students = []
    for student in STUDENTS_DATA["students"].values():
        ensure_student_fields(student)
        students.append({
            "name": student.get("full_name", "بدون اسم"),
            "username": student.get("username", ""),
            "points": student.get("points", 0),
            "paid": student.get("total_paid", 0),
        })

    students = sorted(students, key=lambda x: x["points"], reverse=True)

    if not students:
        return "لا توجد بيانات طلاب بعد."

    msg = "🏆 أعلى الطلاب بالنقاط\n\n"
    for i, s in enumerate(students[:10], start=1):
        username = f"@{s['username']}" if s["username"] else ""
        msg += f"{i}) {s['name']} {username}\n⭐ {s['points']} نقطة | 💰 {s['paid']} JD\n\n"
    return msg


def build_profits_text() -> str:
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

    return msg


def build_top_text() -> str:
    counts = DATA.get("counts", {})
    if not counts:
        return "لا توجد بيانات بعد."

    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    msg = "🔥 أعلى 10 مواد طلبًا:\n\n"
    for i, (subject, count) in enumerate(items, start=1):
        msg += f"{i}) {subject} — {count}\n"
    return msg


def build_students_stats_text() -> str:
    students_count = len(STUDENTS_DATA["students"])
    return f"👨‍🎓 عدد الطلاب المحفوظين: {students_count}"


def build_subject_stats_text(subject_name: str) -> str:
    request_count = DATA.get("counts", {}).get(subject_name, 0)

    paid_students = []
    total_revenue = 0

    for student in STUDENTS_DATA["students"].values():
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

    return msg


# =========================================================
# Subject Requests
# =========================================================
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

        buttons = [
            [InlineKeyboardButton("✅ تأكيد الدفع لهذا الطالب", callback_data=f"confirm_pay|{user.id}|{subject}")]
        ]

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=msg,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

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


# =========================================================
# Subjects and Menus
# =========================================================
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


# =========================================================
# General Commands
# =========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_student(update.effective_user)

    if context.args and context.args[0] == "quiztoday":
        await send_current_quiz_to_user(update, context)
        return

    await update.message.reply_text(
        "👋 أهلاً بك في بوت البروفيسور\n\n"
        "💪 معنا رح تضمن التفوق وبشهادة الجميع\n\n"
        "اختر القسم المناسب من القائمة 👇",
        reply_markup=main_keyboard(),
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
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
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return
    await update.message.reply_text(build_top_text())


async def ready_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
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
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return
    await update.message.reply_text(build_students_stats_text())


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
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return
    await update.message.reply_text(build_profits_text())


async def student_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
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


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return
    await update.message.reply_text(build_leaderboard_text())


async def subject_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    if not context.args:
        await update.message.reply_text("استخدم الأمر هكذا:\n/subject لاب مايكرو - ميد")
        return

    subject_name = " ".join(context.args).strip()
    await update.message.reply_text(build_subject_stats_text(subject_name))


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return
    await update.message.reply_text(build_dashboard_text())


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
        "والدليل؟ الفيدباك منهم يحكي القصة كلها ✨"
    )


# =========================================================
# Ramadan Quiz
# =========================================================
async def quiz_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    context.user_data["admin_mode"] = "create_ramadan_quiz"
    await update.message.reply_text(
        "🕌 أرسل سؤال رمضان بهذا الشكل:\n\n"
        "السؤال\n"
        "الخيار 1\n"
        "الخيار 2\n"
        "الخيار 3\n"
        "الخيار 4\n"
        "رقم الجواب الصحيح\n\n"
        "مثال:\n"
        "What is first-line treatment for dysmenorrhoea?\n"
        "Paracetamol\n"
        "NSAIDs\n"
        "Insulin\n"
        "Antibiotics\n"
        "2"
    )


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_current_quiz_to_user(update, context)


async def quiz_ramadan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    participants = QUIZ_DATA.get("participants", {})
    if not participants:
        await update.message.reply_text("لا يوجد مشاركون في مسابقة رمضان بعد.")
        return

    sorted_participants = get_quiz_ranking()

    msg = "🕌 تقرير مسابقة رمضان\n\n"
    for i, p in enumerate(sorted_participants, start=1):
        username = f"@{p.get('username')}" if p.get("username") else "بدون يوزرنيم"
        msg += (
            f"{i}) {p.get('full_name', 'بدون اسم')}\n"
            f"🔗 اليوزر: {username}\n"
            f"🆔 ID: {p.get('id')}\n"
            f"🗳️ عدد الإجابات: {p.get('votes_count', 0)}\n"
            f"✅ الصحيحة: {p.get('correct_count', 0)}\n"
            f"⭐ النقاط: {p.get('points', 0)}\n\n"
        )

    msg += (
        "🎁 الجوائز:\n"
        "الأول: 3 مواد مجانًا\n"
        "الثاني: مادتين مجانًا\n"
        "الثالث: مادة واحدة مجانًا"
    )

    await update.message.reply_text(msg)


async def send_current_quiz_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_student(user)

    current_quiz_key = QUIZ_DATA.get("current_quiz")
    if not current_quiz_key:
        await update.message.reply_text("لا يوجد سؤال رمضان متاح حاليًا.")
        return

    quiz_info = QUIZ_DATA["quizzes"].get(current_quiz_key)
    if not quiz_info:
        await update.message.reply_text("لا يوجد سؤال رمضان متاح حاليًا.")
        return

    if quiz_info.get("closed", False):
        await update.message.reply_text("لا يوجد سؤال رمضان متاح حاليًا.")
        return

    user_id = str(user.id)
    participants = QUIZ_DATA.setdefault("participants", {})

    if user_id in participants and current_quiz_key in participants[user_id].get("answers", {}):
        rank = get_user_rank(user_id)
        await update.message.reply_text(
            f"🕌 أنت جاوبت على سؤال اليوم بالفعل.\n\n"
            f"⭐ نقاطك الحالية: {participants[user_id].get('points', 0)}\n"
            f"🏆 ترتيبك الحالي: {rank if rank else 'غير محدد'}"
        )
        return

    buttons = []
    for idx, option in enumerate(quiz_info["options"]):
        buttons.append([
            InlineKeyboardButton(
                option,
                callback_data=f"quizanswer|{current_quiz_key}|{idx}"
            )
        ])

    await update.message.reply_text(
        f"🕌 سؤال رمضان اليوم\n\n{quiz_info['question']}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def quiz_answer_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    parts = data.split("|")

    if len(parts) != 3:
        return

    _, quiz_key, chosen_idx_text = parts

    try:
        chosen_idx = int(chosen_idx_text)
    except Exception:
        return

    quiz_info = QUIZ_DATA["quizzes"].get(quiz_key)
    if not quiz_info:
        await query.message.reply_text("هذا السؤال غير متاح.")
        return

    if quiz_info.get("closed", False):
        await query.message.reply_text("⛔ هذا السؤال انتهى، انتظر سؤال اليوم الجديد.")
        return

    user = query.from_user
    user_id = str(user.id)

    save_student(user)

    participants = QUIZ_DATA.setdefault("participants", {})
    student = STUDENTS_DATA["students"].get(user_id)
    if student:
        ensure_student_fields(student)

    if user_id not in participants:
        participants[user_id] = {
            "id": user.id,
            "full_name": user.full_name,
            "username": user.username if user.username else "",
            "points": 0,
            "votes_count": 0,
            "correct_count": 0,
            "answers": {}
        }
    else:
        participants[user_id]["full_name"] = user.full_name
        participants[user_id]["username"] = user.username if user.username else ""

    if quiz_key in participants[user_id]["answers"]:
        rank = get_user_rank(user_id)
        await query.message.reply_text(
            f"🕌 أنت جاوبت هذا السؤال بالفعل.\n\n"
            f"⭐ نقاطك الحالية: {participants[user_id].get('points', 0)}\n"
            f"🏆 ترتيبك الحالي: {rank if rank else 'غير محدد'}"
        )
        return

    is_correct = chosen_idx == quiz_info["correct_option"]

    participants[user_id]["votes_count"] += 1
    participants[user_id]["answers"][quiz_key] = {
        "chosen_option": chosen_idx,
        "is_correct": is_correct
    }

    if is_correct:
        participants[user_id]["points"] += 3
        participants[user_id]["correct_count"] += 1

        if student:
            student["points"] += 3

        save_json_file(STUDENTS_FILE, STUDENTS_DATA)
        save_json_file(QUIZ_FILE, QUIZ_DATA)

        rank = get_user_rank(user_id)
        username_text = f"@{participants[user_id]['username']}" if participants[user_id]["username"] else "بدون يوزرنيم"

        await query.message.reply_text(
            "✅ إجابة صحيحة يا بطل!\n\n"
            "⭐ صار عندك 3 نقاط\n"
            f"🏆 مجموعك الكلي: {participants[user_id]['points']}\n"
            f"📈 ترتيبك الحالي: {rank if rank else 'غير محدد'}"
        )

        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "✅ طالب جاوب صح في سؤال رمضان\n\n"
                    f"👤 الاسم: {participants[user_id]['full_name']}\n"
                    f"🔗 اليوزر: {username_text}\n"
                    f"🆔 ID: {user_id}\n"
                    f"⭐ مجموع نقاطه: {participants[user_id]['points']}\n"
                    f"🏆 ترتيبه الحالي: {rank if rank else 'غير محدد'}"
                )
            )
        except Exception as e:
            print(f"❌ failed to notify admin: {e}")

    else:
        save_json_file(QUIZ_FILE, QUIZ_DATA)

        rank = get_user_rank(user_id)

        await query.message.reply_text(
            "❌ إجابة غير صحيحة.\n\n"
            f"🏆 مجموعك الكلي: {participants[user_id]['points']}\n"
            f"📈 ترتيبك الحالي: {rank if rank else 'غير محدد'}"
        )

# =========================================================
# Ramadan Posts
# =========================================================
RAMADAN_POSTS_BY_DATE = {
    "2026-03-09": "🌙 إفطارًا هنيئًا يا أبطال البروفيسور 🤍\nاليوم 18 رمضان\n\nاشربوا المي بين الإفطار والسحور بشكل موزع 💧",
    "2026-03-10": "🌙 إفطارًا هنيئًا 🤍\nاليوم 19 رمضان\n\nمريض السكري لا يغير الجرعات من نفسه برمضان.",
    "2026-03-11": "🌙 إفطارًا هنيئًا 🤍\nاليوم 20 رمضان\n\nهبوط السكر قد يسبب رجفة وتعرق ودوخة.",
    "2026-03-12": "🌙 إفطارًا هنيئًا 🤍\nاليوم 21 رمضان\n\nبعض أدوية الضغط والمدرات تحتاج تنظيم محترم برمضان.",
    "2026-03-13": "🌙 إفطارًا هنيئًا 🤍\nاليوم 22 رمضان\n\nللبشرة الناشفة: مرطب مباشر بعد الغسل.",
    "2026-03-14": "🌙 إفطارًا هنيئًا 🤍\nاليوم 23 رمضان\n\nالإفطار الثقيل جدًا مرة وحدة يعمل خمول وحموضة.",
    "2026-03-15": "🌙 إفطارًا هنيئًا 🤍\nاليوم 24 رمضان\n\nوزع شرب الماء من الإفطار للسحور.",
    "2026-03-16": "🌙 إفطارًا هنيئًا 🤍\nاليوم 25 رمضان\n\nبعض الأدوية لا تُنقل بين الإفطار والسحور ببساطة.",
    "2026-03-17": "🌙 إفطارًا هنيئًا 🤍\nاليوم 26 رمضان\n\nالجفاف الشديد والدوخة القوية لازم ينأخذوا بجدية.",
    "2026-03-18": "🌙 إفطارًا هنيئًا 🤍\nاليوم 27 رمضان\n\nالإفطار الذكي: نشويات + بروتين + خضار + سوائل.",
    "2026-03-19": "🌙 إفطارًا هنيئًا 🤍\nاليوم 28 رمضان\n\nالعصير حتى لو طبيعي يبقى محمل بالسكر.",
    "2026-03-20": "🌙 إفطارًا هنيئًا 🤍\nاليوم 29 رمضان\n\nالصداع في رمضان قد يكون من الجفاف أو الكافيين أو قلة النوم.",
}


async def scheduled_ramadan_post(context: ContextTypes.DEFAULT_TYPE):
    today_str = amman_now().strftime("%Y-%m-%d")

    if today_str not in RAMADAN_POSTS_BY_DATE:
        return

    posted_dates = POSTED_RAMADAN_DATA.get("posted_dates", [])
    if today_str in posted_dates:
        return

    try:
        await context.bot.send_message(
            chat_id=MAIN_CHANNEL_ID,
            text=RAMADAN_POSTS_BY_DATE[today_str]
        )

        posted_dates.append(today_str)
        POSTED_RAMADAN_DATA["posted_dates"] = posted_dates
        save_json_file(POSTED_RAMADAN_FILE, POSTED_RAMADAN_DATA)

    except Exception as e:
        print(f"❌ scheduled_ramadan_post failed: {e}")


async def post_ramadan_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    today_str = amman_now().strftime("%Y-%m-%d")
    posted_dates = POSTED_RAMADAN_DATA.get("posted_dates", [])

    if today_str not in RAMADAN_POSTS_BY_DATE:
        await update.message.reply_text(f"❌ لا يوجد منشور مربوط بتاريخ اليوم.\n📅 التاريخ: {today_str}")
        return

    if today_str in posted_dates:
        await update.message.reply_text(f"⚠️ منشور اليوم منشور سابقًا.\n📅 التاريخ: {today_str}")
        return

    try:
        await context.bot.send_message(
            chat_id=MAIN_CHANNEL_ID,
            text=RAMADAN_POSTS_BY_DATE[today_str]
        )

        posted_dates.append(today_str)
        POSTED_RAMADAN_DATA["posted_dates"] = posted_dates
        save_json_file(POSTED_RAMADAN_FILE, POSTED_RAMADAN_DATA)

        await update.message.reply_text(f"✅ تم نشر منشور رمضان بنجاح.\n📅 التاريخ: {today_str}")

    except Exception as e:
        await update.message.reply_text(f"❌ فشل النشر:\n{e}")


# =========================================================
# Admin Panel
# =========================================================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
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
        [InlineKeyboardButton("📊 إحصائية مادة", callback_data="admin_subject")],
        [InlineKeyboardButton("📢 إرسال إعلان", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📣 نشر في القناة الرئيسية", callback_data="admin_post_channel")],
    ]

    await update.message.reply_text(
        "⚙️ لوحة تحكم البروفيسور",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""

    if data.startswith("quizanswer|"):
        return

    await query.answer()

    if data == "admin_dashboard":
        await query.message.reply_text(build_dashboard_text())

    elif data == "admin_leaderboard":
        await query.message.reply_text(build_leaderboard_text())

    elif data == "admin_profits":
        await query.message.reply_text(build_profits_text())

    elif data == "admin_top":
        await query.message.reply_text(build_top_text())

    elif data == "admin_students":
        await query.message.reply_text(build_students_stats_text())

    elif data == "admin_student":
        context.user_data["admin_mode"] = "student_lookup"
        await query.message.reply_text("👤 أرسل الآن:\n\n@username\nأو\nID الطالب")

    elif data == "admin_subject":
        context.user_data["admin_mode"] = "subject_stats"
        await query.message.reply_text("📊 أرسل اسم المادة بهذا الشكل:\n\nلاب مايكرو - ميد")

    elif data == "admin_paid":
        context.user_data["admin_mode"] = "confirm_payment_manual"
        await query.message.reply_text(
            "💳 أرسل معلومات الدفع بهذا الشكل:\n\n"
            "@username\n"
            "المادة - الامتحان\n"
            "المبلغ\n\n"
            "مثال:\n"
            "@ahmad\n"
            "لاب مايكرو - ميد\n"
            "7"
        )

    elif data.startswith("confirm_pay|"):
        try:
            _, student_id, subject_text = data.split("|", 2)
        except ValueError:
            await query.message.reply_text("❌ تعذر قراءة بيانات الزر.")
            return

        context.user_data["admin_mode"] = "confirm_payment_amount_only"
        context.user_data["pending_payment_student_id"] = student_id
        context.user_data["pending_payment_subject"] = subject_text

        await query.message.reply_text(
            f"💰 اكتب الآن المبلغ لهذا الطالب فقط:\n\n"
            f"🆔 ID: {student_id}\n"
            f"📚 المادة: {subject_text}\n\n"
            "مثال:\n3"
        )

    elif data == "admin_broadcast":
        context.user_data["admin_mode"] = "broadcast_message"
        await query.message.reply_text("📢 أرسل الآن الرسالة التي تريد إرسالها لكل الطلاب.")

    elif data == "admin_post_channel":
        context.user_data["admin_mode"] = "post_main_channel"
        await query.message.reply_text("📣 أرسل الآن الرسالة التي تريد نشرها في القناة الرئيسية.")


# =========================================================
# Message Handler
# =========================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    user = update.effective_user
    mode = context.user_data.get("admin_mode")

    if mode == "student_lookup":
        student_id = resolve_student_id(text)
        if not student_id:
            await update.message.reply_text("لم أجد هذا الطالب.")
            return
        await update.message.reply_text(build_student_profile_text(student_id))
        context.user_data.pop("admin_mode", None)
        return

    if mode == "subject_stats":
        await update.message.reply_text(build_subject_stats_text(text.strip()))
        context.user_data.pop("admin_mode", None)
        return

    if mode == "confirm_payment_manual":
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        if len(lines) != 3:
            await update.message.reply_text(
                "❌ الصيغة غير صحيحة.\n\n"
                "أرسلها هكذا:\n@username\nالمادة - الامتحان\nالمبلغ"
            )
            return

        target_text, subject_text, amount_text = lines
        found_student_id = resolve_student_id(target_text)

        if not found_student_id:
            await update.message.reply_text("❌ لم أجد هذا الطالب.")
            return

        try:
            amount = float(amount_text)
        except Exception:
            await update.message.reply_text("❌ المبلغ غير صحيح.")
            return

        student = STUDENTS_DATA["students"][found_student_id]
        ensure_student_fields(student)

        payment_record = {
            "amount": amount,
            "subject": subject_text,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "confirmed_by": update.effective_user.id
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
            print(f"❌ failed to notify student from manual mode: {e}")

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

        context.user_data.pop("admin_mode", None)
        return

    if mode == "confirm_payment_amount_only":
        student_id = context.user_data.get("pending_payment_student_id")
        subject_text = context.user_data.get("pending_payment_subject")

        if not student_id or not subject_text:
            await update.message.reply_text("❌ لا توجد عملية دفع معلقة.")
            context.user_data.pop("admin_mode", None)
            context.user_data.pop("pending_payment_student_id", None)
            context.user_data.pop("pending_payment_subject", None)
            return

        try:
            amount = float(text)
        except Exception:
            await update.message.reply_text("❌ اكتب رقم فقط، مثل:\n3")
            return

        student = STUDENTS_DATA["students"].get(str(student_id))
        if not student:
            await update.message.reply_text("❌ الطالب غير موجود.")
            context.user_data.pop("admin_mode", None)
            context.user_data.pop("pending_payment_student_id", None)
            context.user_data.pop("pending_payment_subject", None)
            return

        ensure_student_fields(student)

        payment_record = {
            "amount": amount,
            "subject": subject_text,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "confirmed_by": update.effective_user.id
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
                chat_id=int(student_id),
                text=(
                    "✅ تم تأكيد الدفع بنجاح\n\n"
                    f"📚 المادة: {subject_text}\n"
                    f"💰 المبلغ المسجل: {amount} JD\n"
                    f"⭐ نقاطك الحالية: {student['points']}\n\n"
                    "شكرًا لك 🌟"
                )
            )
        except Exception as e:
            print(f"❌ failed to notify student from button mode: {e}")

        username_text = f"@{student.get('username', '')}" if student.get("username") else "بدون يوزرنيم"
        await update.message.reply_text(
            f"✅ تم تأكيد الدفع للطالب:\n"
            f"👤 الاسم: {student.get('full_name', 'بدون اسم')}\n"
            f"🔗 اليوزر: {username_text}\n"
            f"🆔 ID: {student_id}\n"
            f"📚 المادة: {subject_text}\n"
            f"💰 المبلغ: {amount} JD\n"
            f"⭐ النقاط الحالية: {student['points']}"
        )

        context.user_data.pop("admin_mode", None)
        context.user_data.pop("pending_payment_student_id", None)
        context.user_data.pop("pending_payment_subject", None)
        return

    if mode == "broadcast_message":
        sent = 0
        failed = 0

        for student_id in STUDENTS_DATA["students"].keys():
            try:
                await context.bot.send_message(
                    chat_id=int(student_id),
                    text=f"📢 إعلان من البروفيسور:\n\n{text}"
                )
                sent += 1
            except Exception:
                failed += 1

        await update.message.reply_text(
            f"✅ تم إرسال الإعلان\n\n📨 نجح الإرسال إلى: {sent}\n❌ فشل الإرسال إلى: {failed}"
        )
        context.user_data.pop("admin_mode", None)
        return

    if mode == "post_main_channel":
        try:
            await context.bot.send_message(chat_id=MAIN_CHANNEL_ID, text=text)
            await update.message.reply_text("✅ تم نشر الرسالة في القناة الرئيسية.")
        except Exception as e:
            await update.message.reply_text(f"❌ فشل النشر في القناة:\n{e}")

        context.user_data.pop("admin_mode", None)
        return

    if mode == "create_ramadan_quiz":
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if len(lines) != 6:
        await update.message.reply_text(
            "❌ الصيغة غير صحيحة.\n\n"
            "أرسلها هكذا:\n"
            "السؤال\n"
            "الخيار 1\n"
            "الخيار 2\n"
            "الخيار 3\n"
            "الخيار 4\n"
            "رقم الجواب الصحيح"
        )
        return

    question = lines[0]
    options = lines[1:5]
    correct_text = lines[5]

    try:
        correct_option = int(correct_text) - 1
    except Exception:
        await update.message.reply_text("❌ رقم الجواب الصحيح لازم يكون بين 1 و 4.")
        return

    if correct_option < 0 or correct_option > 3:
        await update.message.reply_text("❌ رقم الجواب الصحيح لازم يكون بين 1 و 4.")
        return

    quiz_date = amman_now().strftime("%Y-%m-%d_%H-%M-%S")

    old_quiz_key = QUIZ_DATA.get("current_quiz")
    if old_quiz_key and old_quiz_key in QUIZ_DATA["quizzes"]:
        QUIZ_DATA["quizzes"][old_quiz_key]["closed"] = True

    QUIZ_DATA["current_quiz"] = quiz_date
    QUIZ_DATA["quizzes"][quiz_date] = {
        "question": question,
        "options": options,
        "correct_option": correct_option,
        "closed": False
    }

    save_json_file(QUIZ_FILE, QUIZ_DATA)

    deep_link = f"https://t.me/{BOT_USERNAME}?start=quiztoday"
    buttons = [[InlineKeyboardButton("🕌 جاوب سؤال اليوم", url=deep_link)]]

    try:
        await context.bot.send_message(
            chat_id=MAIN_CHANNEL_ID,
            text=(
                "🕌 سؤال رمضان اليوم جاهز!\n\n"
                "اضغط الزر بالأسفل وجاوب داخل البوت 👇"
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

        await update.message.reply_text(
            f"✅ تم نشر سؤال رمضان الجديد بنجاح.\n"
            f"📅 التاريخ: {quiz_date}\n"
            "🔒 تم إغلاق السؤال السابق تلقائيًا."
        )

    except Exception as e:
        await update.message.reply_text(f"❌ فشل نشر سؤال رمضان:\n{e}")

    context.user_data.pop("admin_mode", None)
    return

    if text == "⬅️ رجوع للقائمة الرئيسية":
        context.user_data.pop("pending_subject", None)
        await update.message.reply_text("رجعناك للقائمة الرئيسية ✅", reply_markup=main_keyboard())
        return

    if text == "✅ المواد الجاهزة الآن":
        ready_subject_names = sorted(list({subject for subject, exam in READY_SUBJECTS.keys()}))
        await update.message.reply_text("اختر مادة جاهزة 👇", reply_markup=section_keyboard(ready_subject_names))
        return

    if text == "📚 المواد الأساسية":
        await update.message.reply_text("اختر من المواد الأساسية 👇", reply_markup=section_keyboard(BASIC_SUBJECTS))
        return

    if text == "🧪 اللابات":
        await update.message.reply_text("اختر من اللابات 👇", reply_markup=section_keyboard(LAB_SUBJECTS))
        return

    if text == "🎓 مواد دكتور صيدلة":
        await update.message.reply_text("اختر من مواد دكتور صيدلة 👇", reply_markup=section_keyboard(PHARMD_SUBJECTS))
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

    if text in ready_subject_names or text in ALL_SUBJECTS:
        context.user_data["pending_subject"] = text
        await update.message.reply_text(
            f"📚 المادة: {text}\n\nاختر نوع الامتحان المطلوب 👇",
            reply_markup=exam_type_keyboard()
        )
        return

    if text in ["فيرست", "سكند", "فاينال", "ميد"]:
        pending_subject = context.user_data.get("pending_subject")

        if not pending_subject:
            await update.message.reply_text("اختار المادة أولًا 👇", reply_markup=main_keyboard())
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

    known_buttons = {
        "✅ المواد الجاهزة الآن",
        "📚 المواد الأساسية",
        "🧪 اللابات",
        "🎓 مواد دكتور صيدلة",
        "💳 كيف أشترك؟",
        "📩 تواصل مع البروفيسور",
        "👨‍🏫 من هو البروفيسور؟",
        "⬅️ رجوع للقائمة الرئيسية",
        "فيرست",
        "سكند",
        "فاينال",
        "ميد",
    }

    greetings = {"مرحبا", "هلا", "السلام عليكم", "اهلا", "أهلا", "hi", "hello"}

    if text.strip().lower() in {g.lower() for g in greetings}:
        await update.message.reply_text("هلا والله 👑")
        return

    if text not in known_buttons:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )
        reply = await ask_gpt(text)
        await update.message.reply_text(reply)
        return

    await update.message.reply_text("اختار من الأزرار الموجودة 👇", reply_markup=main_keyboard())


# =========================================================
# Misc Commands
# =========================================================
async def gpt_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("اكتب السؤال بعد الأمر.")
        return
    question = " ".join(context.args)
    answer = await ask_gpt(question)
    await update.message.reply_text(answer)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("❌ Update caused error:", context.error)


async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if not text.startswith("/"):
        return

    uid = update.effective_user.id

    if uid in ADMIN_IDS:
        raw = text[1:].strip().split()[0].lower()

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
            "dashboard",
            "admin",
            "testchannel",
            "postramadannow",
            "gpttest",
            "quizday",
            "quizramadan",
            "quiz",
        }

        if raw not in known_commands:
            target = f"@{raw}"
            found_student_id = resolve_student_id(target)
            if found_student_id:
                await update.message.reply_text(build_student_profile_text(found_student_id))
                return

    await update.message.reply_text("أمر غير معروف.")


async def test_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("هذا الأمر للأدمن فقط ✅")
        return

    try:
        await context.bot.send_message(
            chat_id=MAIN_CHANNEL_ID,
            text="✅ تم ربط البوت بالقناة الرئيسية بنجاح"
        )
        await update.message.reply_text("✅ تم إرسال رسالة تجريبية للقناة.")
    except Exception as e:
        await update.message.reply_text(f"❌ فشل الإرسال للقناة:\n{e}")


# =========================================================
# Main
# =========================================================
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
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("testchannel", test_channel))
    app.add_handler(CommandHandler("postramadannow", post_ramadan_now))
    app.add_handler(CommandHandler("quizday", quiz_day))
    app.add_handler(CommandHandler("quizramadan", quiz_ramadan))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("gpttest", gpt_test))

    app.add_handler(CallbackQueryHandler(quiz_answer_button, pattern=r"^quizanswer\|"))
    app.add_handler(CallbackQueryHandler(admin_buttons))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))

    app.add_error_handler(error_handler)

    app.job_queue.run_daily(
        scheduled_ramadan_post,
        time=time(hour=20, minute=0, second=0, tzinfo=ZoneInfo("Asia/Amman"))
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()