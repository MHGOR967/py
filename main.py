import telebot
from telebot import types
import requests
import re
import json
import time
import threading
from datetime import datetime
from flask import Flask
import os

# === سيرفر ويب لإبقاء البوت شغال على Render ===
web_app = Flask('')

@web_app.route('/')
def home():
    return 'TikWahm Bot is running!'

def run_web():
    port = int(os.environ.get('PORT', 10000))
    web_app.run(host='0.0.0.0', port=port)

# تشغيل السيرفر في thread منفصل
web_thread = threading.Thread(target=run_web)
web_thread.daemon = True
web_thread.start()

BOT_TOKEN = "8945719165:AAHeD9sJFlRDiUKEUUlj6bSoYxtwGmgmKmw"
bot = telebot.TeleBot(BOT_TOKEN)

try:
    bot.delete_webhook()
except:
    pass

# === إعدادات الأدمن والبيانات ===
ADMIN_ID = 8349168441
FORCED_CHANNELS = [] # قائمة اليوزرات أو الآيديات للقنوات
USERS_FILE = "users.json"
CHANNELS_FILE = "channels.json"

def load_data(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return default

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# تحميل القنوات والمستخدمين
FORCED_CHANNELS = load_data(CHANNELS_FILE, [])
all_users = load_data(USERS_FILE, [])

# === تخزين بيانات المستخدمين ===
user_states = {}   # {chat_id: {"state": "...", "data": {...}}}
user_sessions = {} # {chat_id: {"session_key": "...", "username": "...", "user_id": "..."}}
user_lang = {}     # {chat_id: "ar" / "en" / "ru"}

# === الترجمات ===
TEXTS = {
    "welcome": {
        "ar": "• مرحباً {first_name} °.° في TikWahm - معلومات تيك توك 🎵\n\n<blockquote>بوت متقدم يوفر مجموعة قوية من أدوات TikTok، ويتيح لك استخراج المعلومات العامة والمتقدمة للحسابات، وتحميل الستوري، واستخدام أدوات إدارة الحساب.</blockquote>\n\n<b>أرسل يوزر أو رابط مقطع.</b>\n\n<blockquote>يمكنك استخدام الأقسام من الأزرار بالأسفل.</blockquote>",
        "en": "• Welcome {first_name} °.° to TikWahm - TikTok Info 🎵\n\n<blockquote>An advanced bot that provides powerful TikTok tools, allowing you to extract public and advanced account information, download stories, and use account management tools.</blockquote>\n\n<b>Send a username or video link.</b>\n\n<blockquote>You can use sections from the buttons below.</blockquote>",
        "ru": "• Добро пожаловать {first_name} °.° в TikWahm - TikTok Info 🎵\n\n<blockquote>Продвинутый бот с мощными инструментами TikTok, позволяющий извлекать информацию об аккаунтах, скачивать сторис и управлять аккаунтом.</blockquote>\n\n<b>Отправьте имя пользователя или ссылку.</b>\n\n<blockquote>Используйте разделы из кнопок ниже.</blockquote>",
    },
    "private_section": {
        "ar": "🔐 <b>مرحباً بك في القسم الخاص</b>\n\n<blockquote>يمكنك من خلال هذا القسم التحكم الكامل بحسابك بسهولة وأمان، واستخدام أدوات الإدارة والخدمات المرتبطة بالحساب.</blockquote>\n\n<blockquote>استخدم الأزرار بالأسفل للوصول إلى الخدمات المتاحة.</blockquote>",
        "en": "🔐 <b>Welcome to the Private Section</b>\n\n<blockquote>Through this section, you can fully control your account easily and securely, and use management tools and account-related services.</blockquote>\n\n<blockquote>Use the buttons below to access available services.</blockquote>",
        "ru": "🔐 <b>Добро пожаловать в приватный раздел</b>\n\n<blockquote>В этом разделе вы можете полностью управлять своим аккаунтом безопасно и легко.</blockquote>\n\n<blockquote>Используйте кнопки ниже для доступа к услугам.</blockquote>",
    },
    "no_accounts": {
        "ar": "❌ لا توجد حسابات، يرجى إضافة حساب واحد على الأقل.",
        "en": "❌ No accounts found. Please add at least one account.",
        "ru": "❌ Аккаунты не найдены. Добавьте хотя бы один аккаунт.",
    },
    "add_account_guide": {
        "ar": "<b>Get Sessions 👤:</b>\n\n1. ادخل إلى قناة @get_session .\n2. بعد ذلك افتح أي رابط موجود داخل القناة.\n3. عند الضغط على الرابط سيتم توجيهك إلى تيك توك.\n4. ستظهر لك صفحة تحتوي على عدة بيانات.\n5. ابحث عن القيمة المسماة <code>Sessions_key</code>.\n6. انسخ Sessions_key فقط كما هو تمامًا دون تعديل.\n7. ثم أرسله إلى البوت في رسالة واحدة\n\n• مثل:\n<code>b5999c2e4fe0b9c17d66467463391e08</code>",
        "en": "<b>Get Sessions 👤:</b>\n\n1. Go to @get_session channel.\n2. Open any link inside the channel.\n3. You will be redirected to TikTok.\n4. A page with data will appear.\n5. Find the value named <code>Sessions_key</code>.\n6. Copy Sessions_key exactly as it is.\n7. Send it to the bot in one message.\n\n• Example:\n<code>b5999c2e4fe0b9c17d66467463391e08</code>",
        "ru": "<b>Получить Sessions 👤:</b>\n\n1. Перейдите в канал @get_session .\n2. Откройте любую ссылку в канале.\n3. Вы будете перенаправлены в TikTok.\n4. Появится страница с данными.\n5. Найдите значение <code>Sessions_key</code>.\n6. Скопируйте его без изменений.\n7. Отправьте боту одним сообщением.\n\n• Пример:\n<code>b5999c2e4fe0b9c17d66467463391e08</code>",
    },
    "verifying": {
        "ar": "🔄 جاري التحقق من الجلسة...",
        "en": "🔄 Verifying session...",
        "ru": "🔄 Проверка сессии...",
    },
    "session_invalid": {
        "ar": "❌ الجلسة غير صالحة أو منتهية.\nتأكد من نسخ sessionid بشكل صحيح وحاول مرة أخرى.",
        "en": "❌ Invalid or expired session.\nMake sure you copied the sessionid correctly and try again.",
        "ru": "❌ Сессия недействительна или истекла.\nУбедитесь, что вы правильно скопировали sessionid.",
    },
    "session_success": {
        "ar": "✅ تم تسجيل الدخول بنجاح!",
        "en": "✅ Successfully logged in!",
        "ru": "✅ Успешный вход!",
    },
    "control_panel": {
        "ar": "🎛 <b>لوحة التحكم</b>\n\n👤 الحساب: @{username}\n📛 الاسم: {nickname}\n👥 المتابعين: {followers}\n👤 يتابع: {following}\n\n<blockquote>اختر العملية المطلوبة من الأزرار بالأسفل.</blockquote>",
        "en": "🎛 <b>Control Panel</b>\n\n👤 Account: @{username}\n📛 Name: {nickname}\n👥 Followers: {followers}\n👤 Following: {following}\n\n<blockquote>Choose an action from the buttons below.</blockquote>",
        "ru": "🎛 <b>Панель управления</b>\n\n👤 Аккаунт: @{username}\n📛 Имя: {nickname}\n👥 Подписчики: {followers}\n👤 Подписки: {following}\n\n<blockquote>Выберите действие из кнопок ниже.</blockquote>",
    },
    "confirm_unfollow": {
        "ar": "⚠️ <b>تأكيد إلغاء المتابعات</b>\n\n<blockquote>سيتم إلغاء متابعة جميع الحسابات ({count}).\nهذا الإجراء لا يمكن التراجع عنه!</blockquote>",
        "en": "⚠️ <b>Confirm Unfollow All</b>\n\n<blockquote>All accounts ({count}) will be unfollowed.\nThis action cannot be undone!</blockquote>",
        "ru": "⚠️ <b>Подтвердите отписку</b>\n\n<blockquote>Все аккаунты ({count}) будут отписаны.\nЭто действие нельзя отменить!</blockquote>",
    },
    "confirm_repost": {
        "ar": "⚠️ <b>تأكيد حذف الريبوستات</b>\n\n<blockquote>سيتم حذف جميع الريبوستات من حسابك.\nهذا الإجراء لا يمكن التراجع عنه!</blockquote>",
        "en": "⚠️ <b>Confirm Remove Reposts</b>\n\n<blockquote>All reposts will be removed from your account.\nThis action cannot be undone!</blockquote>",
        "ru": "⚠️ <b>Подтвердите удаление репостов</b>\n\n<blockquote>Все репосты будут удалены.\nЭто действие нельзя отменить!</blockquote>",
    },
    "lang_changed": {
        "ar": "✅ تم تغيير اللغة إلى العربية",
        "en": "✅ Language changed to English",
        "ru": "✅ Язык изменён на русский",
    },
    "btn_private": {"ar": "🔐 القسم الخاص", "en": "🔐 Private Section", "ru": "🔐 Приватный раздел"},
    "btn_search": {"ar": "🔍 قسم البحث", "en": "🔍 Search Section", "ru": "🔍 Раздел поиска"},
    "btn_lang": {"ar": "🌐 تغيير اللغة", "en": "🌐 Change Language", "ru": "🌐 Сменить язык"},
    "btn_unfollow": {"ar": "🔓 إلغاء المتابعات", "en": "🔓 Unfollow All", "ru": "🔓 Отписаться от всех"},
    "btn_repost": {"ar": "🗑 إزالة الريبوستات", "en": "🗑 Remove Reposts", "ru": "🗑 Удалить репосты"},
    "btn_delete_session": {"ar": "🚫 حذف الجلسة", "en": "🚫 Delete Session", "ru": "🚫 Удалить сессию"},
    "btn_add_account": {"ar": "➕ إضافة حساب", "en": "➕ Add Account", "ru": "➕ Добавить аккаунт"},
    "btn_back": {"ar": "🔙 رجوع", "en": "🔙 Back", "ru": "🔙 Назад"},
    "btn_confirm": {"ar": "✅ نعم، نفّذ", "en": "✅ Yes, proceed", "ru": "✅ Да, выполнить"},
    "btn_cancel": {"ar": "❌ إلغاء", "en": "❌ Cancel", "ru": "❌ Отмена"},
    "session_deleted": {
        "ar": "✅ تم حذف الجلسة بنجاح.",
        "en": "✅ Session deleted successfully.",
        "ru": "✅ Сессия успешно удалена.",
    },
    "cancelled": {
        "ar": "❌ تم إلغاء العملية.",
        "en": "❌ Operation cancelled.",
        "ru": "❌ Операция отменена.",
    },
    "search_email": {
        "ar": "📧 أرسل البريد الإلكتروني للبحث عنه:",
        "en": "📧 Send the email to search for:",
        "ru": "📧 Отправьте электронную почту для поиска:",
    },
    "search_phone": {
        "ar": "📱 أرسل رقم الهاتف للبحث عنه (مع رمز الدولة):\nمثال: +966501234567",
        "en": "📱 Send the phone number to search for (with country code):\nExample: +12025550123",
        "ru": "📱 Отправьте номер телефона для поиска (с кодом страны):\nПример: +79001234567",
    },
    "search_found": {
        "ar": "✅ <b>تم العثور على حساب مرتبط!</b>\n\n{info}",
        "en": "✅ <b>Linked account found!</b>\n\n{info}",
        "ru": "✅ <b>Найден связанный аккаунт!</b>\n\n{info}",
    },
    "search_not_found": {
        "ar": "❌ لم يتم العثور على حساب مرتبط بهذا {type}.",
        "en": "❌ No linked account found for this {type}.",
        "ru": "❌ Связанный аккаунт не найден для этого {type}.",
    },
    "search_error": {
        "ar": "❌ حدث خطأ أثناء البحث. يرجى المحاولة لاحقاً.",
        "en": "❌ An error occurred during search. Please try again later.",
        "ru": "❌ Произошла ошибка при поиске. Попробуйте позже.",
    },
    "invalid_format": {
        "ar": "❌ صيغة غير صحيحة. يرجى إدخال {type} صحيح.",
        "en": "❌ Invalid format. Please enter a valid {type}.",
        "ru": "❌ Неверный формат. Введите правильный {type}.",
    },
    "btn_search_email": {"ar": "📧 البحث بالبريد", "en": "📧 Search by Email", "ru": "📧 Поиск по email"},
    "btn_search_phone": {"ar": "📱 البحث بالهاتف", "en": "📱 Search by Phone", "ru": "📱 Поиск по телефону"},
    "btn_search_username": {"ar": "🔍 البحث باليوزر", "en": "🔍 Search by Username", "ru": "🔍 Поиск по имени"},
}

def t(key, chat_id):
    """جلب النص بلغة المستخدم"""
    lang = user_lang.get(chat_id, "ar")
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("ar", ""))

# === القواميس ===
LANGUAGE_MAP = {
    "ar": "عربي", "en": "إنجليزي", "fr": "فرنسي", "es": "إسباني",
    "de": "ألماني", "tr": "تركي", "ru": "روسي", "pt": "برتغالي",
    "id": "إندونيسي", "ja": "ياباني", "ko": "كوري", "hi": "هندي",
    "it": "إيطالي", "th": "تايلاندي", "vi": "فيتنامي", "ms": "ماليزي",
    "fil": "فلبيني", "zh": "صيني", "nl": "هولندي", "pl": "بولندي",
    "uk": "أوكراني", "sv": "سويدي", "ro": "روماني", "cs": "تشيكي",
    "el": "يوناني", "he": "عبري", "da": "دنماركي", "fi": "فنلندي",
    "hu": "مجري", "no": "نرويجي", "sk": "سلوفاكي", "bg": "بلغاري",
}

COUNTRY_MAP = {
    "SA": "السعودية 🇸🇦", "AE": "الإمارات 🇦🇪", "EG": "مصر 🇪🇬",
    "KW": "الكويت 🇰🇼", "BH": "البحرين 🇧🇭", "QA": "قطر 🇶🇦",
    "OM": "عُمان 🇴🇲", "IQ": "العراق 🇮🇶", "JO": "الأردن 🇯🇴",
    "LB": "لبنان 🇱🇧", "SY": "سوريا 🇸🇾", "PS": "فلسطين 🇵🇸",
    "YE": "اليمن 🇾🇪", "LY": "ليبيا 🇱🇾", "TN": "تونس 🇹🇳",
    "DZ": "الجزائر 🇩🇿", "MA": "المغرب 🇲🇦", "SD": "السودان 🇸🇩",
    "US": "الولايات المتحدة 🇺🇸", "GB": "بريطانيا 🇬🇧",
    "CA": "كندا 🇨🇦", "AU": "أستراليا 🇦🇺", "DE": "ألمانيا 🇩🇪",
    "FR": "فرنسا 🇫🇷", "TR": "تركيا 🇹🇷", "RU": "روسيا 🇷🇺",
    "IN": "الهند 🇮🇳", "PK": "باكستان 🇵🇰", "BR": "البرازيل 🇧🇷",
    "ID": "إندونيسيا 🇮🇩", "MY": "ماليزيا 🇲🇾", "PH": "الفلبين 🇵🇭",
    "TH": "تايلاند 🇹🇭", "VN": "فيتنام 🇻🇳", "JP": "اليابان 🇯🇵",
    "KR": "كوريا الجنوبية 🇰🇷", "CN": "الصين 🇨🇳", "MX": "المكسيك 🇲🇽",
    "ES": "إسبانيا 🇪🇸", "IT": "إيطاليا 🇮🇹", "NL": "هولندا 🇳🇱",
    "SG": "سنغافورة 🇸🇬", "NG": "نيجيريا 🇳🇬", "ZA": "جنوب أفريقيا 🇿🇦",
    "PL": "بولندا 🇵🇱", "SE": "السويد 🇸🇪", "NO": "النرويج 🇳🇴",
    "DK": "الدنمارك 🇩🇰", "FI": "فنلندا 🇫🇮", "IE": "أيرلندا 🇮🇪",
    "NZ": "نيوزيلندا 🇳🇿", "AR": "الأرجنتين 🇦🇷", "CL": "تشيلي 🇨🇱",
    "CO": "كولومبيا 🇨🇴", "PE": "بيرو 🇵🇪",
}

STAR_PRICE = 350

# === الدوال المساعدة ===
def format_number(num):
    if isinstance(num, str):
        return num
    if num >= 1000000000:
        return f"{num/1000000000:.2f}B"
    elif num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num:,}"
    return str(num)

def get_account_age(create_time):
    try:
        created_at_dt = datetime.fromtimestamp(create_time)
        now = datetime.now()
        diff = now - created_at_dt
        days = diff.days
        years = days // 365
        remaining = days % 365
        months = remaining // 30
        
        parts = []
        if years > 0: parts.append(f"{years} سنة")
        if months > 0: parts.append(f"{months} شهر")
        if not parts: parts.append(f"{days} يوم")
        return " و ".join(parts)
    except:
        return "غير متوفر"

def timestamp_to_date(timestamp):
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    except:
        return "غير متوفر"

# === دوال TikTok API ===
def get_tikwm_user(username):
    """جلب معلومات المستخدم عبر TikWM API"""
    try:
        url = f"https://www.tikwm.com/api/user/info?unique_id={username}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0:
                return data.get("data")
    except:
        pass
    return None

def get_countik_userinfo(sec_uid):
    """جلب معلومات إضافية عبر Countik"""
    try:
        url = f"https://countik.com/api/userinfo?sec_user_id={sec_uid}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def get_countik_analyze(sec_uid):
    """تحليل الحساب عبر Countik"""
    try:
        url = f"https://countik.com/api/analyze?sec_user_id={sec_uid}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def get_region_from_videos(username, video_id):
    """محاولة استنتاج الدولة من الفيديو"""
    try:
        url = f"https://www.tikwm.com/api/video/info?url=https://www.tiktok.com/@{username}/video/{video_id}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("region")
    except:
        pass
    return None

def get_stories(username):
    """جلب الستوري"""
    try:
        url = f"https://www.tikwm.com/api/user/posts?unique_id={username}&count=10"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json().get("data")
    except:
        pass
    return None

def verify_session(session_key):
    """التحقق من صحة sessionid وجلب معلومات الحساب"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': f'sessionid={session_key}; sid_tt={session_key}',
    }
    try:
        r = requests.get('https://www.tiktok.com/api/user/detail/?device_id=7315123456789012345', headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("userInfo"):
                return data.get("userInfo")
    except:
        pass
    return None

def get_following_list(session_key, user_id, count=100):
    """جلب قائمة المتابَعين (الأشخاص الذين يتابعهم الحساب)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': f'sessionid={session_key}; sid_tt={session_key}',
    }
    following = []
    cursor = 0
    try:
        while len(following) < count:
            url = f'https://www.tiktok.com/api/user/list/?count=30&cursor={cursor}&type=1&user_id={user_id}'
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                users = data.get("userList", []) or data.get("user_list", [])
                if not users: break
                following.extend(users)
                if not data.get("hasMore", False): break
                cursor = data.get("cursor", 0)
            else:
                break
            time.sleep(1)
    except:
        pass
    return following[:count]

def unfollow_user(session_key, target_uid, target_sec_uid):
    """إلغاء متابعة مستخدم"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': f'sessionid={session_key}; sid_tt={session_key}',
        'Referer': 'https://www.tiktok.com/',
    }
    try:
        url = f'https://www.tiktok.com/api/commit/follow/user/?type=0&object_id={target_uid}&sec_user_id={target_sec_uid}'
        r = requests.post(url, headers=headers, timeout=15)
        return r.status_code == 200 and r.json().get("status_code") == 0
    except:
        return False

def remove_repost(session_key, video_id):
    """حذف ريبوست"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': f'sessionid={session_key}; sid_tt={session_key}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    try:
        url = 'https://www.tiktok.com/passport/repost/item/delete/'
        data = {'item_id': video_id}
        r = requests.post(url, data=data, headers=headers, timeout=15)
        return r.status_code == 200
    except:
        return False

def search_by_email_tiktok(email, session_key=None):
    """البحث عن حساب تيك توك عبر البريد الإلكتروني"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    # محاولة 1: عبر API داخلي (يتطلب session)
    if session_key:
        try:
            auth_headers = headers.copy()
            auth_headers['Cookie'] = f'sessionid={session_key}; sid_tt={session_key}'
            r = requests.get(f'https://www.tiktok.com/api/user/find_by_email/?email={email}', headers=auth_headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("user"): return data["user"]
        except:
            pass
    
    # محاولة 2: عبر passport (فحص وجود الحساب)
    try:
        r = requests.post(
            'https://www.tiktok.com/passport/web/email/check_availability/',
            data={'email': email},
            headers=headers,
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("data") and data["data"].get("is_registered"):
                return {"exists": True, "masked_email": email}
    except:
        pass
    return None

def search_by_phone_tiktok(phone, session_key=None):
    """البحث عن حساب تيك توك عبر رقم الهاتف"""
    clean_phone = phone.replace("+", "").replace(" ", "")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    # محاولة 1: عبر contact sync (تتطلب session)
    if session_key:
        try:
            auth_headers = headers.copy()
            auth_headers['Cookie'] = f'sessionid={session_key}; sid_tt={session_key}'
            auth_headers['Content-Type'] = 'application/json'
            payload = json.dumps({"contacts": [{"phone": clean_phone, "contact_name": "search"}]})
            r = requests.post(
                'https://www.tiktok.com/api/user/find_contacts/',
                data=payload,
                headers=auth_headers,
                timeout=15
            )
            if r.status_code == 200:
                data = r.json()
                contacts = data.get("contacts", []) or data.get("data", {}).get("contacts", [])
                if contacts:
                    return contacts[0]
        except:
            pass
    
    # محاولة 2: عبر password reset flow
    try:
        r = requests.post(
            'https://www.tiktok.com/passport/web/send_code/',
            data={'mobile': clean_phone, 'type': '2', 'account_sdk_source': 'web'},
            headers=headers,
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("data") and data["data"].get("mask_mobile"):
                return {"masked_phone": data["data"]["mask_mobile"], "exists": True}
            elif data.get("message") == "success":
                return {"exists": True, "phone": phone}
    except:
        pass
    
    # محاولة 3: عبر account check
    try:
        r = requests.post(
            'https://www.tiktok.com/passport/web/account/check/',
            data={'mobile': clean_phone, 'scene': 'find_account'},
            headers=headers,
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("data"):
                return data["data"]
    except:
        pass
    
    return None

# === دالة تحميل فيديو تيك توك ===
def download_tiktok_video(url):
    """تحميل فيديو تيك توك بدون علامة مائية - يرجع رابط التحميل ومعلومات الفيديو"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    # محاولة 1: عبر tikwm API (الأسرع والأفضل)
    try:
        r = requests.get(
            f'https://www.tikwm.com/api/?url={url}&hd=1',
            headers=headers,
            timeout=20
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0 and data.get("data"):
                video_data = data["data"]
                play_url = video_data.get("hdplay") or video_data.get("play") or video_data.get("wmplay")
                if play_url:
                    return {
                        "play_url": play_url,
                        "title": video_data.get("title", ""),
                        "author": video_data.get("author", {}).get("unique_id", ""),
                        "duration": video_data.get("duration", 0),
                        "cover": video_data.get("cover", ""),
                    }
    except:
        pass
    
    # محاولة 2: عبر tikwm POST
    try:
        r = requests.post(
            'https://www.tikwm.com/api/',
            data={'url': url, 'hd': '1'},
            headers=headers,
            timeout=20
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0 and data.get("data"):
                video_data = data["data"]
                play_url = video_data.get("hdplay") or video_data.get("play") or video_data.get("wmplay")
                if play_url:
                    return {
                        "play_url": play_url,
                        "title": video_data.get("title", ""),
                        "author": video_data.get("author", {}).get("unique_id", ""),
                        "duration": video_data.get("duration", 0),
                        "cover": video_data.get("cover", ""),
                    }
    except:
        pass
    
    # محاولة 3: عبر صفحة تيك توك مباشرة (scraping)
    try:
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if r.status_code == 200:
            import re as re_mod
            match = re_mod.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', r.text)
            if match:
                page_data = json.loads(match.group(1))
                default_scope = page_data.get('__DEFAULT_SCOPE__', {})
                detail = default_scope.get('webapp.video-detail', {})
                item = detail.get('itemInfo', {}).get('itemStruct', {})
                if item:
                    video = item.get('video', {})
                    # جلب رابط التحميل من bitrateInfo
                    bitrate_info = video.get('bitrateInfo', [])
                    play_url = None
                    if bitrate_info:
                        url_list = bitrate_info[0].get('PlayAddr', {}).get('UrlList', [])
                        if url_list:
                            play_url = url_list[0]
                    if not play_url:
                        play_url = video.get('downloadAddr') or video.get('playAddr')
                    
                    if play_url:
                        return {
                            "play_url": play_url,
                            "title": item.get("desc", ""),
                            "author": item.get("author", {}).get("uniqueId", ""),
                            "duration": video.get("duration", 0),
                            "cover": video.get("cover", ""),
                        }
    except:
        pass
    
    return None

# === دوال الاشتراك الإجباري والأدمن ===
def is_subscribed(user_id):
    for channel in FORCED_CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            # إذا فشل البوت في التحقق (مثلاً ليس أدمن في القناة)
            continue
    return True

def get_forced_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for channel in FORCED_CHANNELS:
        try:
            chat = bot.get_chat(channel)
            title = chat.title
            url = f"https://t.me/{chat.username}" if chat.username else f"https://t.me/{channel}"
            markup.add(types.InlineKeyboardButton(f"اشترك في: {title}", url=url))
        except:
            markup.add(types.InlineKeyboardButton(f"اشترك هنا: {channel}", url=f"https://t.me/{channel.replace('@', '')}"))
    markup.add(types.InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_sub"))
    return markup

def admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("إحصائيات 📊", callback_data="admin_stats"),
        types.InlineKeyboardButton("إرسال جماعي 📢", callback_data="admin_broadcast"),
    )
    markup.add(
        types.InlineKeyboardButton("إضافة قناة ➕", callback_data="admin_add_channel"),
        types.InlineKeyboardButton("حذف قناة ➖", callback_data="admin_del_channel"),
    )
    markup.add(
        types.InlineKeyboardButton("قائمة القنوات 📋", callback_data="admin_list_channels"),
    )
    return markup

# === أمر البداية ===
@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id
    user = message.from_user
    
    # إشعار مستخدم جديد
    if chat_id not in all_users:
        all_users.append(chat_id)
        save_data(USERS_FILE, all_users)
        try:
            admin_msg = (
                f"👤 مستخدم جديد بدأ البوت:\n\n"
                f"├ الاسم: {user.first_name}\n"
                f"├ اليوزر: @{user.username if user.username else 'لا يوجد'}\n"
                f"└ الآيدي: <code>{chat_id}</code>"
            )
            bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")
        except:
            pass

    # تحقق من الاشتراك الإجباري
    if not is_subscribed(chat_id):
        bot.send_message(chat_id, "⚠️ عذراً، يجب عليك الاشتراك في قنوات البوت أولاً لتتمكن من استخدامه.", reply_markup=get_forced_markup())
        return

    if chat_id not in user_lang:
        user_lang[chat_id] = "ar"
    
    first_name = message.from_user.first_name if message.from_user and message.from_user.first_name else ""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(t("btn_private", chat_id), callback_data="menu_private"),
        types.InlineKeyboardButton(t("btn_search", chat_id), callback_data="menu_search"),
    )
    markup.add(
        types.InlineKeyboardButton(t("btn_lang", chat_id), callback_data="menu_lang"),
    )
    
    welcome_text = t("welcome", chat_id).format(first_name=first_name)
    welcome_text += "\n\n🤖 TikWahmbot"
    bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=markup)

# === أمر الأدمن ===
@bot.message_handler(commands=["admin"])
def send_admin(message):
    if message.chat.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, "مرحباً بك في لوحة تحكم الأدمن 🔐", reply_markup=admin_panel())

# === معالجة الدفع ===
@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    payload = message.successful_payment.invoice_payload
    parts = payload.split("|")
    if len(parts) == 2:
        response = (
            "✅ تم الدفع بنجاح!\n\n"
            "⏳ هذه الميزة قيد التطوير حالياً.\n"
            "🔜 قريباً - ساعات محددة ونضيفها!\n\n"
            "شكراً لدعمك 💎\n\nTikWahmbot"
        )
        bot.send_message(message.chat.id, response)

# === معالجة Callbacks ===
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data
    
    # تحقق من الاشتراك عند الضغط على زر التحقق
    if data == "check_sub":
        if is_subscribed(chat_id):
            bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح، يمكنك الآن استخدام البوت.")
            bot.delete_message(chat_id, call.message.message_id)
            send_welcome(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات بعد!", show_alert=True)
        return

    # === لوحة تحكم الأدمن ===
    if chat_id == ADMIN_ID:
        if data == "admin_stats":
            stats = (
                f"📊 إحصائيات البوت:\n\n"
                f"├ عدد المستخدمين: {len(all_users)}\n"
                f"├ عدد القنوات الإجبارية: {len(FORCED_CHANNELS)}\n"
                f"└ عدد الجلسات النشطة: {len(user_sessions)}"
            )
            bot.edit_message_text(stats, chat_id, call.message.message_id, reply_markup=admin_panel())
        
        elif data == "admin_broadcast":
            user_states[chat_id] = {"state": "waiting_broadcast"}
            bot.send_message(chat_id, "أرسل الرسالة التي تريد إرسالها للجميع (نص فقط):")
        
        elif data == "admin_add_channel":
            user_states[chat_id] = {"state": "waiting_add_channel"}
            bot.send_message(chat_id, "أرسل معرف القناة (مثال: @TikWahm):")
            
        elif data == "admin_del_channel":
            if not FORCED_CHANNELS:
                bot.answer_callback_query(call.id, "لا توجد قنوات لحذفها")
                return
            markup = types.InlineKeyboardMarkup()
            for ch in FORCED_CHANNELS:
                markup.add(types.InlineKeyboardButton(ch, callback_data=f"delch_{ch}"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_main"))
            bot.edit_message_text("اختر القناة المراد حذفها:", chat_id, call.message.message_id, reply_markup=markup)
            
        elif data == "admin_list_channels":
            if not FORCED_CHANNELS:
                bot.answer_callback_query(call.id, "لا توجد قنوات مضافة")
                return
            msg = "📋 قائمة القنوات الإجبارية:\n\n" + "\n".join(FORCED_CHANNELS)
            bot.edit_message_text(msg, chat_id, call.message.message_id, reply_markup=admin_panel())
            
        elif data == "admin_main":
            bot.edit_message_text("مرحباً بك في لوحة تحكم الأدمن 🔐", chat_id, call.message.message_id, reply_markup=admin_panel())
            
        elif data.startswith("delch_"):
            ch = data.replace("delch_", "")
            if ch in FORCED_CHANNELS:
                FORCED_CHANNELS.remove(ch)
                save_data(CHANNELS_FILE, FORCED_CHANNELS)
                bot.answer_callback_query(call.id, f"تم حذف القناة {ch}")
                # تحديث القائمة
                handle_callback(type('obj', (object,), {'message': call.message, 'data': 'admin_del_channel', 'id': call.id, 'from_user': call.from_user}))
            return

    # === القائمة الرئيسية ===
    if data == "menu_main":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(t("btn_private", chat_id), callback_data="menu_private"),
            types.InlineKeyboardButton(t("btn_search", chat_id), callback_data="menu_search"),
        )
        markup.add(
            types.InlineKeyboardButton(t("btn_lang", chat_id), callback_data="menu_lang"),
        )
        first_name = ""
        if call.from_user and call.from_user.first_name:
            first_name = call.from_user.first_name
        welcome_text = t("welcome", chat_id).format(first_name=first_name)
        welcome_text += "\n\nTikWahmbot"
        try:
            bot.edit_message_text(welcome_text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=markup)
    
    # === تغيير اللغة ===
    elif data == "menu_lang":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton("🇸🇦 عربي", callback_data="set_lang_ar"),
            types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
            types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
        )
        markup.add(types.InlineKeyboardButton(t("btn_back", chat_id), callback_data="menu_main"))
        try:
            bot.edit_message_text("🌐 اختر اللغة / Choose language / Выберите язык:", chat_id, call.message.message_id, reply_markup=markup)
        except:
            bot.send_message(chat_id, "🌐 اختر اللغة / Choose language / Выберите язык:", reply_markup=markup)
    
    elif data.startswith("set_lang_"):
        lang = data.replace("set_lang_", "")
        user_lang[chat_id] = lang
        bot.answer_callback_query(call.id, t("lang_changed", chat_id))
        # إعادة عرض القائمة الرئيسية
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(t("btn_private", chat_id), callback_data="menu_private"),
            types.InlineKeyboardButton(t("btn_search", chat_id), callback_data="menu_search"),
        )
        markup.add(
            types.InlineKeyboardButton(t("btn_lang", chat_id), callback_data="menu_lang"),
        )
        first_name = ""
        if call.from_user and call.from_user.first_name:
            first_name = call.from_user.first_name
        welcome_text = t("welcome", chat_id).format(first_name=first_name)
        welcome_text += "\n\nTikWahmbot"
        try:
            bot.edit_message_text(welcome_text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=markup)
    
    # === قسم البحث (معدل - مع أزرار البحث بالبريد والهاتف) ===
    elif data == "menu_search":
        bot.answer_callback_query(call.id)
        lang = user_lang.get(chat_id, "ar")
        search_texts = {
            "ar": "🔍 <b>قسم البحث</b>\n\n<blockquote>اختر طريقة البحث أو أرسل يوزر تيك توك مباشرة.</blockquote>",
            "en": "🔍 <b>Search Section</b>\n\n<blockquote>Choose a search method or send a TikTok username directly.</blockquote>",
            "ru": "🔍 <b>Раздел поиска</b>\n\n<blockquote>Выберите метод поиска или отправьте имя пользователя TikTok напрямую.</blockquote>",
        }
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(t("btn_search_email", chat_id), callback_data="search_by_email"),
            types.InlineKeyboardButton(t("btn_search_phone", chat_id), callback_data="search_by_phone"),
        )
        markup.add(types.InlineKeyboardButton(t("btn_back", chat_id), callback_data="menu_main"))
        footer = "\n\nTikWahmbot"
        try:
            bot.edit_message_text(search_texts.get(lang, search_texts["ar"]) + footer, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, search_texts.get(lang, search_texts["ar"]) + footer, parse_mode="HTML", reply_markup=markup)
    
    # === البحث بالبريد ===
    elif data == "search_by_email":
        bot.answer_callback_query(call.id)
        user_states[chat_id] = {"state": "waiting_email"}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(t("btn_cancel", chat_id), callback_data="cancel_action"))
        try:
            bot.edit_message_text(t("search_email", chat_id), chat_id, call.message.message_id, reply_markup=markup)
        except:
            bot.send_message(chat_id, t("search_email", chat_id), reply_markup=markup)
    
    # === البحث بالهاتف ===
    elif data == "search_by_phone":
        bot.answer_callback_query(call.id)
        user_states[chat_id] = {"state": "waiting_phone"}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(t("btn_cancel", chat_id), callback_data="cancel_action"))
        try:
            bot.edit_message_text(t("search_phone", chat_id), chat_id, call.message.message_id, reply_markup=markup)
        except:
            bot.send_message(chat_id, t("search_phone", chat_id), reply_markup=markup)
    
    # === القسم الخاص ===
    elif data == "menu_private":
        bot.answer_callback_query(call.id)
        
        # تحقق إذا عنده حساب مسجل
        if chat_id in user_sessions and user_sessions[chat_id].get("session_key"):
            # عرض لوحة التحكم
            show_control_panel(chat_id, call.message.message_id)
        else:
            # لا يوجد حساب
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton(t("btn_add_account", chat_id), callback_data="add_account"),
                types.InlineKeyboardButton(t("btn_back", chat_id), callback_data="menu_main"),
            )
            footer = "\n\nTikWahmbot"
            try:
                bot.edit_message_text(
                    t("private_section", chat_id) + "\n\n" + t("no_accounts", chat_id) + footer,
                    chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup
                )
            except:
                bot.send_message(chat_id, t("private_section", chat_id) + "\n\n" + t("no_accounts", chat_id) + footer, parse_mode="HTML", reply_markup=markup)
    
    # === إضافة حساب ===
    elif data == "add_account":
        bot.answer_callback_query(call.id)
        user_states[chat_id] = {"state": "waiting_session"}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(t("btn_cancel", chat_id), callback_data="cancel_action"))
        try:
            bot.edit_message_text(t("add_account_guide", chat_id), chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, t("add_account_guide", chat_id), parse_mode="HTML", reply_markup=markup)
    
    # === لوحة التحكم - إلغاء المتابعات ===
    elif data == "action_unfollow":
        bot.answer_callback_query(call.id)
        session = user_sessions.get(chat_id, {})
        following_count = session.get("following", 0)
        
        text = t("confirm_unfollow", chat_id).format(count=following_count)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(t("btn_confirm", chat_id), callback_data="exec_unfollow"),
            types.InlineKeyboardButton(t("btn_cancel", chat_id), callback_data="menu_private"),
        )
        try:
            bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
    
    # === لوحة التحكم - حذف الريبوستات ===
    elif data == "action_repost":
        bot.answer_callback_query(call.id)
        text = t("confirm_repost", chat_id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(t("btn_confirm", chat_id), callback_data="exec_repost"),
            types.InlineKeyboardButton(t("btn_cancel", chat_id), callback_data="menu_private"),
        )
        try:
            bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
    
    # === تنفيذ إلغاء المتابعات ===
    elif data == "exec_unfollow":
        bot.answer_callback_query(call.id, "جاري التنفيذ...")
        session = user_sessions.get(chat_id, {})
        session_key = session.get("session_key")
        
        if not session_key:
            bot.send_message(chat_id, "❌ لا توجد جلسة. أضف حسابك أولاً.")
            return
        
        def do_unfollow():
            bot.send_message(chat_id, "⏳ جاري إلغاء المتابعات...")
            my_user_id = session.get("user_id")
            if not my_user_id:
                bot.send_message(chat_id, "❌ لا يوجد معرف حساب. أعد إضافة حسابك.")
                return
            following = get_following_list(session_key, my_user_id)
            
            if not following:
                bot.send_message(chat_id, "✅ لا يوجد حسابات متابَعة!")
                return
            
            total = len(following)
            success = 0
            failed = 0
            
            for i, user in enumerate(following, 1):
                uid = user.get("user", {}).get("id")
                sec_uid = user.get("user", {}).get("secUid")
                if uid and sec_uid:
                    if unfollow_user(session_key, uid, sec_uid):
                        success += 1
                    else:
                        failed += 1
                
                if i % 10 == 0:
                    bot.send_message(chat_id, f"⏳ {i}/{total} | ✅ {success} | ❌ {failed}")
                time.sleep(2)
            
            bot.send_message(chat_id, f"✅ اكتمل!\n\n📊 الإجمالي: {total}\n✅ نجح: {success}\n❌ فشل: {failed}\n\nTikWahmbot")
        
        threading.Thread(target=do_unfollow, daemon=True).start()
    
    # === تنفيذ حذف الريبوستات ===
    elif data == "exec_repost":
        bot.answer_callback_query(call.id, "جاري التنفيذ...")
        session = user_sessions.get(chat_id, {})
        session_key = session.get("session_key")
        
        if not session_key:
            bot.send_message(chat_id, "❌ لا توجد جلسة. أضف حسابك أولاً.")
            return
        
        def do_remove_reposts():
            bot.send_message(chat_id, "⏳ جاري حذف الريبوستات...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': f'sessionid={session_key}; sid_tt={session_key}',
            }
            
            reposts = []
            cursor = 0
            while True:
                try:
                    r = requests.get(f'https://www.tiktok.com/api/user/repost/list/?count=20&cursor={cursor}', headers=headers, timeout=15)
                    if r.status_code == 200:
                        data = r.json()
                        items = data.get("itemList", []) or data.get("item_list", [])
                        if not items:
                            break
                        reposts.extend(items)
                        if not data.get("hasMore", False):
                            break
                        cursor = data.get("cursor", 0)
                    else:
                        break
                except:
                    break
                time.sleep(1)
            
            if not reposts:
                bot.send_message(chat_id, "✅ لا يوجد ريبوستات!")
                return
            
            total = len(reposts)
            success = 0
            failed = 0
            
            for i, item in enumerate(reposts, 1):
                video_id = item.get("id") or item.get("video", {}).get("id")
                if video_id:
                    if remove_repost(session_key, video_id):
                        success += 1
                    else:
                        failed += 1
                if i % 10 == 0:
                    bot.send_message(chat_id, f"⏳ {i}/{total} | ✅ {success} | ❌ {failed}")
                time.sleep(2)
            
            bot.send_message(chat_id, f"✅ اكتمل!\n\n📊 الإجمالي: {total}\n✅ نجح: {success}\n❌ فشل: {failed}\n\nTikWahmbot")
        
        threading.Thread(target=do_remove_reposts, daemon=True).start()
    
    # === حذف الجلسة ===
    elif data == "delete_session":
        bot.answer_callback_query(call.id)
        if chat_id in user_sessions:
            del user_sessions[chat_id]
        bot.send_message(chat_id, t("session_deleted", chat_id) + "\n\nTikWahmbot")
    
    # === إلغاء ===
    elif data == "cancel_action":
        bot.answer_callback_query(call.id)
        if chat_id in user_states:
            del user_states[chat_id]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(t("btn_back", chat_id), callback_data="menu_main"))
        try:
            bot.edit_message_text(t("cancelled", chat_id), chat_id, call.message.message_id, reply_markup=markup)
        except:
            bot.send_message(chat_id, t("cancelled", chat_id))
    
    # === أزرار البحث ===
    elif data.startswith("story_"):
        username = data.replace("story_", "")
        bot.answer_callback_query(call.id, "جاري تحميل الستوري...")
        story_data = get_stories(username)
        if story_data and story_data.get("videos") and len(story_data["videos"]) > 0:
            stories = story_data["videos"]
            for i, story in enumerate(stories[:5], 1):
                video_url = story.get("play") or story.get("wmplay")
                if video_url:
                    try:
                        bot.send_video(chat_id, video_url, caption=f"📖 ستوري {i}/{len(stories)} - @{username}\n\nTikWahmbot")
                    except:
                        bot.send_message(chat_id, f"📖 ستوري {i}: {video_url}\n\nTikWahmbot")
        else:
            bot.send_message(chat_id, f"❌ لا يوجد ستوري متاح لـ @{username}\n\nTikWahmbot")
    
    elif data.startswith("level_"):
        username = data.replace("level_", "")
        bot.answer_callback_query(call.id, "جاري جلب المستوى...")
        
        user_data = get_tikwm_user(username)
        if not user_data:
            bot.send_message(chat_id, "❌ خطأ في جلب البيانات.")
            return
        
        sec_uid = user_data.get("user", {}).get("secUid", "")
        stats = user_data.get("stats", {})
        followers = stats.get("followerCount", 0)
        likes = stats.get("heartCount", 0)
        videos_count = stats.get("videoCount", 0)
        digg_count = stats.get("diggCount", 0)
        
        analyze_data = get_countik_analyze(sec_uid) if sec_uid else None
        earnings = analyze_data.get("earnings") if analyze_data else None
        engagement = analyze_data.get("engagement_rates") if analyze_data else None
        performance = analyze_data.get("performance") if analyze_data else None
        hashtags_data = analyze_data.get("hashtags", []) if analyze_data else []
        
        ins_id = user_data.get("user", {}).get("ins_id", "") or None
        twitter_id = user_data.get("user", {}).get("twitter_id", "") or None
        youtube_title = user_data.get("user", {}).get("youtube_channel_title", "") or None
        
        avg_likes = likes // videos_count if videos_count > 0 else 0
        engagement_rate = "غير متوفر"
        if followers > 0 and videos_count > 0:
            eng_rate = ((likes / videos_count) / followers) * 100
            engagement_rate = f"{eng_rate:.2f}%"
        
        level_text = f"📊 مستوى حساب @{username}\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        level_text += f"• الحسابات المربوطة\n├ انستقرام: {ins_id if ins_id else 'غير مربوط ❌'}\n├ تويتر: {twitter_id if twitter_id else 'غير مربوط ❌'}\n└ يوتيوب: {youtube_title if youtube_title else 'غير مربوط ❌'}\n\n"
        level_text += f"• إحصائيات متقدمة\n├ إعجابات أعطاها: {format_number(digg_count)}\n├ متوسط الإعجابات/فيديو: {format_number(avg_likes)}\n└ معدل التفاعل: {engagement_rate}\n\n"
        
        if earnings:
            level_text += f"• الأرباح التقديرية\n├ الحد الأدنى: ${earnings.get('min', 0):.2f}\n└ الحد الأقصى: ${earnings.get('max', 0):.2f}\n\n"
        if engagement:
            level_text += f"• معدلات التفاعل\n├ الإعجابات: {engagement.get('likes_rate', 0)}%\n├ التعليقات: {engagement.get('comments_rate', 0)}%\n├ المشاركات: {engagement.get('shares_rate', 0)}%\n└ الإجمالي: {engagement.get('total_rate', 0)}%\n\n"
        if performance:
            level_text += f"• متوسط الأداء\n├ المشاهدات: {format_number(performance.get('avgViews', 0))}\n├ الإعجابات: {format_number(performance.get('avgLikes', 0))}\n├ التعليقات: {format_number(performance.get('avgComments', 0))}\n└ المشاركات: {format_number(performance.get('avgShares', 0))}\n\n"
        if hashtags_data:
            level_text += f"• أكثر الهاشتاقات\n"
            for h in hashtags_data[:5]:
                if isinstance(h, dict):
                    level_text += f"├ #{h.get('name', '')} ({h.get('count', 0)}x)\n"
        
        level_text += "\nTikWahmbot"
        bot.send_message(chat_id, level_text)
    
    elif data.startswith("pay_"):
        parts = data.split("_", 2)
        if len(parts) == 3:
            action = parts[1]
            username = parts[2]
            titles = {
                "followers": "👥 عرض قائمة المتابعين",
                "following": "👤 عرض قائمة المتابَعين",
                "binding": "🔗 كشف نوع ربط الحساب",
            }
            title = titles.get(action, "ميزة مدفوعة")
            description = f"الحصول على {title} لحساب @{username}"
            payload = f"{action}|{username}"
            try:
                prices = [types.LabeledPrice(label=title, amount=STAR_PRICE)]
                bot.send_invoice(
                    chat_id=chat_id, title=title, description=description,
                    invoice_payload=payload, provider_token="", currency="XTR", prices=prices,
                )
                bot.answer_callback_query(call.id)
            except Exception as e:
                bot.answer_callback_query(call.id, f"خطأ: {e}", show_alert=True)

def show_control_panel(chat_id, message_id=None):
    """عرض لوحة التحكم"""
    session = user_sessions.get(chat_id, {})
    text = t("control_panel", chat_id).format(
        username=session.get("username", "?"),
        nickname=session.get("nickname", "?"),
        followers=format_number(session.get("followers", 0)),
        following=format_number(session.get("following", 0)),
    )
    text += "\n\nTikWahmbot"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(t("btn_unfollow", chat_id), callback_data="action_unfollow"),
        types.InlineKeyboardButton(t("btn_repost", chat_id), callback_data="action_repost"),
    )
    markup.add(
        types.InlineKeyboardButton(t("btn_delete_session", chat_id), callback_data="delete_session"),
    )
    markup.add(
        types.InlineKeyboardButton(t("btn_back", chat_id), callback_data="menu_main"),
    )
    
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)
            return
        except:
            pass
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

# === معالجة الرسائل ===
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip() if message.text else ""
    
    # تحقق من الاشتراك الإجباري
    if not is_subscribed(chat_id):
        bot.send_message(chat_id, "⚠️ عذراً، يجب عليك الاشتراك في قنوات البوت أولاً لتتمكن من استخدامه.", reply_markup=get_forced_markup())
        return

    if chat_id not in user_lang:
        user_lang[chat_id] = "ar"
    
    # === معالجة حالات الأدمن ===
    state = user_states.get(chat_id, {})
    if chat_id == ADMIN_ID:
        if state.get("state") == "waiting_broadcast":
            del user_states[chat_id]
            success = 0
            failed = 0
            bot.send_message(chat_id, f"⏳ جاري الإرسال إلى {len(all_users)} مستخدم...")
            for uid in all_users:
                try:
                    bot.send_message(uid, text + "\n\nTikWahmbot")
                    success += 1
                except:
                    failed += 1
                time.sleep(0.1)
            bot.send_message(chat_id, f"✅ اكتمل الإرسال!\n├ نجح: {success}\n└ فشل: {failed}")
            return
            
        elif state.get("state") == "waiting_add_channel":
            del user_states[chat_id]
            if text.startswith("@") or text.lstrip("-").isdigit():
                if text not in FORCED_CHANNELS:
                    FORCED_CHANNELS.append(text)
                    save_data(CHANNELS_FILE, FORCED_CHANNELS)
                    bot.send_message(chat_id, f"✅ تم إضافة القناة {text} بنجاح.")
                else:
                    bot.send_message(chat_id, "⚠️ القناة مضافة بالفعل.")
            else:
                bot.send_message(chat_id, "❌ معرف قناة غير صحيح.")
            return

    # === حالة انتظار session_key (معدل - تحقق تلقائي بدون طلب يوزرنيم) ===
    if state.get("state") == "waiting_session":
        session_key = text.strip()
        # التحقق من شكل الـ session (32 حرف hex)
        if len(session_key) == 32 and all(c in '0123456789abcdef' for c in session_key):
            bot.send_chat_action(chat_id, 'typing')
            bot.send_message(chat_id, t("verifying", chat_id))
            
            # التحقق الحقيقي من الجلسة عبر TikTok API
            user_info = verify_session(session_key)
            if user_info:
                # الجلسة شغالة - نسحب المعلومات تلقائياً
                user = user_info.get("user", {})
                stats = user_info.get("stats", {})
                username = user.get("uniqueId", "?")
                nickname = user.get("nickname", "?")
                user_id = user.get("id", "")
                followers = stats.get("followerCount", 0)
                following_count = stats.get("followingCount", 0)
                
                user_sessions[chat_id] = {
                    "session_key": session_key,
                    "username": username,
                    "nickname": nickname,
                    "user_id": user_id,
                    "followers": followers,
                    "following": following_count,
                }
                del user_states[chat_id]
                
                bot.send_message(chat_id, t("session_success", chat_id))
                show_control_panel(chat_id)
            else:
                # الجلسة غير صالحة
                del user_states[chat_id]
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(t("btn_add_account", chat_id), callback_data="add_account"),
                    types.InlineKeyboardButton(t("btn_back", chat_id), callback_data="menu_main"),
                )
                bot.send_message(chat_id, t("session_invalid", chat_id), reply_markup=markup)
        else:
            bot.send_message(chat_id, "❌ صيغة الجلسة غير صحيحة. يجب أن تكون 32 حرف. حاول مرة أخرى.")
        return
    
    # === حالة البحث بالبريد الإلكتروني ===
    if state.get("state") == "waiting_email":
        email = text.strip()
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            bot.send_chat_action(chat_id, 'typing')
            bot.send_message(chat_id, "🔍 جاري البحث عن البريد الإلكتروني...")
            
            # استخدام session_key إذا متوفر للبحث الأقوى
            user_session = user_sessions.get(chat_id, {})
            sk = user_session.get("session_key")
            result = search_by_email_tiktok(email, session_key=sk)
            if result:
                # تجميع المعلومات المتاحة
                info_parts = []
                if result.get("uniqueId"):
                    info_parts.append(f"├ اليوزر: @{result['uniqueId']}")
                if result.get("nickname"):
                    info_parts.append(f"├ الاسم: {result['nickname']}")
                if result.get("masked_email"):
                    info_parts.append(f"├ البريد: {result['masked_email']}")
                if result.get("exists"):
                    info_parts.append(f"├ الحالة: حساب موجود ✅")
                if result.get("uid"):
                    info_parts.append(f"├ المعرف: {result['uid']}")
                
                if not info_parts:
                    info_parts.append("├ الحالة: حساب موجود ✅")
                
                info_text = "\n".join(info_parts)
                bot.send_message(chat_id, t("search_found", chat_id).format(info=info_text) + "\n\nTikWahmbot", parse_mode="HTML")
            else:
                lang = user_lang.get(chat_id, "ar")
                type_name = "البريد الإلكتروني" if lang == "ar" else ("email" if lang == "en" else "электронной почте")
                bot.send_message(chat_id, t("search_not_found", chat_id).format(type=type_name) + "\n\nTikWahmbot")
            
            del user_states[chat_id]
        else:
            lang = user_lang.get(chat_id, "ar")
            type_name = "بريد إلكتروني" if lang == "ar" else ("email" if lang == "en" else "email")
            bot.send_message(chat_id, t("invalid_format", chat_id).format(type=type_name))
        return
    
    # === حالة البحث برقم الهاتف ===
    if state.get("state") == "waiting_phone":
        phone = text.strip()
        if re.match(r"^\+?\d{10,15}$", phone):
            bot.send_chat_action(chat_id, 'typing')
            bot.send_message(chat_id, "🔍 جاري البحث عن رقم الهاتف...")
            
            # استخدام session_key إذا متوفر للبحث الأقوى
            user_session = user_sessions.get(chat_id, {})
            sk = user_session.get("session_key")
            result = search_by_phone_tiktok(phone, session_key=sk)
            if result:
                # تجميع المعلومات المتاحة
                info_parts = []
                if result.get("uniqueId"):
                    info_parts.append(f"├ اليوزر: @{result['uniqueId']}")
                if result.get("nickname"):
                    info_parts.append(f"├ الاسم: {result['nickname']}")
                if result.get("masked_phone"):
                    info_parts.append(f"├ الرقم: {result['masked_phone']}")
                if result.get("exists"):
                    info_parts.append(f"├ الحالة: حساب موجود ✅")
                if result.get("uid"):
                    info_parts.append(f"├ المعرف: {result['uid']}")
                
                if not info_parts:
                    info_parts.append("├ الحالة: حساب موجود ✅")
                
                info_text = "\n".join(info_parts)
                bot.send_message(chat_id, t("search_found", chat_id).format(info=info_text) + "\n\nTikWahmbot", parse_mode="HTML")
            else:
                lang = user_lang.get(chat_id, "ar")
                type_name = "رقم الهاتف" if lang == "ar" else ("phone number" if lang == "en" else "номеру телефона")
                bot.send_message(chat_id, t("search_not_found", chat_id).format(type=type_name) + "\n\nTikWahmbot")
            
            del user_states[chat_id]
        else:
            lang = user_lang.get(chat_id, "ar")
            type_name = "رقم هاتف" if lang == "ar" else ("phone number" if lang == "en" else "номер телефона")
            bot.send_message(chat_id, t("invalid_format", chat_id).format(type=type_name))
        return
    
    # === تحميل فيديو تيك توك ===
    is_video_link = ("tiktok.com/" in text and "/video/" in text) or "vm.tiktok.com/" in text or "vt.tiktok.com/" in text
    if is_video_link:
        bot.send_chat_action(chat_id, 'typing')
        bot.reply_to(message, "⬇️ جاري تحميل الفيديو... ⏳")
        
        video_result = download_tiktok_video(text.strip())
        if video_result and video_result.get("play_url"):
            play_url = video_result["play_url"]
            title = video_result.get("title", "")
            author = video_result.get("author", "")
            duration = video_result.get("duration", 0)
            
            caption = f"🎬 TikWahm - تحميل فيديو\n"
            if author:
                caption += f"├ المستخدم: @{author}\n"
            if title:
                caption += f"├ الوصف: {title[:100]}\n"
            if duration:
                caption += f"└ المدة: {duration} ثانية\n"
            caption += f"\n🤖 @TikWahmbot"
            
            try:
                bot.send_video(chat_id, play_url, caption=caption)
            except:
                try:
                    bot.send_message(chat_id, f"⬇️ رابط التحميل:\n{play_url}\n\n{caption}")
                except:
                    bot.send_message(chat_id, f"⬇️ رابط التحميل:\n{play_url}")
        else:
            bot.send_message(chat_id, "❌ فشل تحميل الفيديو. تأكد من صحة الرابط وحاول مرة أخرى.\n\nTikWahmbot")
        return
    
    # === البحث عن حساب تيك توك ===
    username = text.replace("@", "")
    if "tiktok.com/" in username:
        username = username.split("tiktok.com/")[1].split("/")[0].split("?")[0].replace("@", "")
    
    if not username or len(username) < 2:
        bot.reply_to(message, "❌ يرجى إرسال اسم مستخدم صحيح.\n\nTikWahmbot")
        return
    
    bot.send_chat_action(chat_id, 'typing')
    bot.reply_to(message, f"🔍 جاري البحث عن {username}...\nقد يستغرق بضع ثوانٍ ⏳")
    
    user_data = get_tikwm_user(username)
    if not user_data:
        bot.send_message(chat_id, f"❌ لم يتم العثور على حساب {username}\n\nTikWahmbot")
        return
    
    user = user_data.get("user", {})
    stats = user_data.get("stats", {})
    sec_uid = user.get("secUid", "")
    
    countik_info = get_countik_userinfo(sec_uid) if sec_uid else None
    analyze_data = get_countik_analyze(sec_uid) if sec_uid else None
    
    user_id = user.get("id", "غير متوفر")
    unique_id = user.get("uniqueId", "غير متوفر")
    nickname = user.get("nickname", "غير متوفر")
    signature = user.get("signature", "") or "لا يوجد"
    verified = user.get("verified", False)
    private_account = user.get("privateAccount", False)
    secret = user.get("secret", False)
    is_under_18 = user.get("isUnderAge18", False)
    open_favorite = user.get("openFavorite", False)
    is_ad_virtual = user.get("isADVirtual", False)
    ftc = user.get("ftc", False)
    create_time = user.get("createTime", 0)
    
    followers = stats.get("followerCount", 0)
    following = stats.get("followingCount", 0)
    likes = stats.get("heartCount", 0)
    videos_count = stats.get("videoCount", 0)
    friends = stats.get("friendCount", 0)
    
    language = "غير متوفر"
    if countik_info:
        lang_code = countik_info.get("language", "")
        if lang_code:
            language = LANGUAGE_MAP.get(lang_code, lang_code)
    
    region = "غير متوفر"
    video_id_for_region = None
    if analyze_data and analyze_data.get("videos"):
        video_id_for_region = analyze_data["videos"][0].get("id")
    if video_id_for_region:
        region_code = get_region_from_videos(username, video_id_for_region)
        if region_code:
            region = COUNTRY_MAP.get(region_code.upper(), region_code)
    
    story_status = user.get("UserStoryStatus", 0)
    has_story = story_status > 0
    
    caption_text = (
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 TikWahm - معلومات تيك توك\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"• معلومات الحساب\n"
        f"├ اسم المستخدم: {unique_id}\n"
        f"├ المعرف: {user_id}\n"
        f"├ الاسم: {nickname}\n"
        f"├ المتابعين: {format_number(followers)}\n"
        f"├ يتابع: {format_number(following)}\n"
        f"├ الأصدقاء: {format_number(friends)}\n"
        f"├ الإعجابات: {format_number(likes)}\n"
        f"├ الفيديوهات: {format_number(videos_count)}\n"
        f"├ تاريخ الإنشاء: {timestamp_to_date(create_time)}\n"
        f"├ عمر الحساب: {get_account_age(create_time) if create_time else 'غير متوفر'}\n"
        f"├ 🌍 الدولة: {region}\n"
        f"├ 🗣 اللغة: {language}\n"
        f"├ حساب موثق: {'نعم ✅' if verified else 'لا ❌'}\n"
        f"├ حساب خاص: {'نعم 🔒' if private_account else 'لا ❌'}\n"
        f"├ حساب سري: {'نعم 🔒' if secret else 'لا ❌'}\n"
        f"├ المفضلة مفتوحة: {'نعم ✅' if open_favorite else 'لا ❌'}\n"
        f"├ أقل من 18 سنة: {'نعم ⚠️' if is_under_18 else 'لا ❌'}\n"
        f"├ متوافق FTC: {'نعم ✅' if ftc else 'لا ❌'}\n"
        f"└ حساب إعلانات وهمي: {'نعم ⚠️' if is_ad_virtual else 'لا ❌'}\n\n"
        f"• البايو: {signature}\n"
    )
    
    url_in_bio = re.findall(r'https?://[^\s]+', signature)
    if url_in_bio:
        caption_text += f"• الرابط في البايو: {url_in_bio[0]}\n"
    
    caption_text += f"\n🔗 https://www.tiktok.com/@{unique_id}\n"
    caption_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    caption_text += f"🤖 @TikWahmbot"
    
    # الأزرار
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👥 عرض المتابعين 💎", callback_data=f"pay_followers_{unique_id}"),
        types.InlineKeyboardButton("👤 عرض المتابَعين 💎", callback_data=f"pay_following_{unique_id}"),
    )
    markup.add(
        types.InlineKeyboardButton("📖 تحميل الستوري 🆓", callback_data=f"story_{unique_id}"),
    )
    markup.add(
        types.InlineKeyboardButton("📊 كشف مستوى الحساب 🆓", callback_data=f"level_{unique_id}"),
        types.InlineKeyboardButton("🔗 كشف نوع الربط 💎", callback_data=f"pay_binding_{unique_id}"),
    )
    
    # إرسال
    avatar_url = user.get("avatarLarger") or user.get("avatarMedium") or user.get("avatarThumb")
    
    try:
        if avatar_url:
            if len(caption_text) > 1024:
                short_caption = (
                    f"📱 معلومات @{unique_id}\n"
                    f"├ الاسم: {nickname}\n"
                    f"├ المتابعين: {format_number(followers)}\n"
                    f"├ الإعجابات: {format_number(likes)}\n"
                    f"├ 🌍 الدولة: {region}\n"
                    f"└ 🗣 اللغة: {language}\n"
                    f"\n🤖 @TikWahmbot"
                )
                bot.send_photo(chat_id, avatar_url, caption=short_caption)
                bot.send_message(chat_id, caption_text)
            else:
                bot.send_photo(chat_id, avatar_url, caption=caption_text)
        else:
            bot.send_message(chat_id, caption_text)
    except Exception as e:
        print(f"Error: {e}")
        try:
            bot.send_message(chat_id, caption_text)
        except:
            bot.send_message(chat_id, f"معلومات @{unique_id}\nالمتابعين: {format_number(followers)}\n\nTikWahmbot")
    
    # أزرار
    try:
        bot.send_message(chat_id, "⬇️ خيارات إضافية:", reply_markup=markup)
    except:
        pass

print("✅ TikWahm Bot started successfully!")
print(f"🌐 Web server running on port {os.environ.get('PORT', 10000)}")
bot.polling(none_stop=True)
all_users = load_data(USERS_FILE, [])

# === تخزين بيانات المستخدمين ===
user_states = {}   # {chat_id: {"state": "...", "data": {...}}}
user_sessions = {} # {chat_id: {"session_key": "...", "username": "...", "user_id": "..."}}
user_lang = {}     # {chat_id: "ar" / "en" / "ru"}

# === الترجمات ===
TEXTS = {
    "welcome": {
        "ar": "• مرحباً {first_name} °.° في TikWahm - معلومات تيك توك 🎵\n\n<blockquote>بوت متقدم يوفر مجموعة قوية من أدوات TikTok، ويتيح لك استخراج المعلومات العامة والمتقدمة للحسابات، وتحميل الستوري، واستخدام أدوات إدارة الحساب.</blockquote>\n\n<b>أرسل يوزر أو رابط مقطع.</b>\n\n<blockquote>يمكنك استخدام الأقسام من الأزرار بالأسفل.</blockquote>",
        "en": "• Welcome {first_name} °.° to TikWahm - TikTok Info 🎵\n\n<blockquote>An advanced bot that provides powerful TikTok tools, allowing you to extract public and advanced account information, download stories, and use account management tools.</blockquote>\n\n<b>Send a username or video link.</b>\n\n<blockquote>You can use sections from the buttons below.</blockquote>",
        "ru": "• Добро пожаловать {first_name} °.° в TikWahm - TikTok Info 🎵\n\n<blockquote>Продвинутый бот с мощными инструментами TikTok, позволяющий извлекать информацию об аккаунтах, скачивать сторис и управлять аккаунтом.</blockquote>\n\n<b>Отправьте имя пользователя или ссылку.</b>\n\n<blockquote>Используйте разделы из кнопок ниже.</blockquote>",
    },
    "private_section": {
        "ar": "🔐 <b>مرحباً بك في القسم الخاص</b>\n\n<blockquote>يمكنك من خلال هذا القسم التحكم الكامل بحسابك بسهولة وأمان، واستخدام أدوات الإدارة والخدمات المرتبطة بالحساب.</blockquote>\n\n<blockquote>استخدم الأزرار بالأسفل للوصول إلى الخدمات المتاحة.</blockquote>",
        "en": "🔐 <b>Welcome to the Private Section</b>\n\n<blockquote>Through this section, you can fully control your account easily and securely, and use management tools and account-related services.</blockquote>\n\n<blockquote>Use the buttons below to access available services.</blockquote>",
        "ru": "🔐 <b>Добро пожаловать в приватный раздел</b>\n\n<blockquote>В этом разделе вы можете полностью управлять своим аккаунтом безопасно и легко.</blockquote>\n\n<blockquote>Используйте кнопки ниже для доступа к услугам.</blockquote>",
    },
    "no_accounts": {
        "ar": "❌ لا توجد حسابات، يرجى إضافة حساب واحد على الأقل.",
        "en": "❌ No accounts found. Please add at least one account.",
        "ru": "❌ Аккаунты не найдены. Добавьте хотя бы один аккаунт.",
    },
    "add_account_guide": {
        "ar": "<b>Get Sessions 👤:</b>\n\n1. ادخل إلى قناة @get_session .\n2. بعد ذلك افتح أي رابط موجود داخل القناة.\n3. عند الضغط على الرابط سيتم توجيهك إلى تيك توك.\n4. ستظهر لك صفحة تحتوي على عدة بيانات.\n5. ابحث عن القيمة المسماة <code>Sessions_key</code>.\n6. انسخ Sessions_key فقط كما هو تمامًا دون تعديل.\n7. ثم أرسله إلى البوت في رسالة واحدة\n\n• مثل:\n<code>b5999c2e4fe0b9c17d66467463391e08</code>",
        "en": "<b>Get Sessions 👤:</b>\n\n1. Go to @get_session channel.\n2. Open any link inside the channel.\n3. You will be redirected to TikTok.\n4. A page with data will appear.\n5. Find the value named <code>Sessions_key</code>.\n6. Copy Sessions_key exactly as it is.\n7. Send it to the bot in one message.\n\n• Example:\n<code>b5999c2e4fe0b9c17d66467463391e08</code>",
        "ru": "<b>Получить Sessions 👤:</b>\n\n1. Перейдите в канал @get_session .\n2. Откройте любую ссылку в канале.\n3. Вы будете перенаправлены в TikTok.\n4. Появится страница с данными.\n5. Найдите значение <code>Sessions_key</code>.\n6. Скопируйте его без изменений.\n7. Отправьте боту одним сообщением.\n\n• Пример:\n<code>b5999c2e4fe0b9c17d66467463391e08</code>",
    },
    "verifying": {
        "ar": "🔄 جاري التحقق من الجلسة...",
        "en": "🔄 Verifying session...",
        "ru": "🔄 Проверка сессии...",
    },
    "session_invalid": {
        "ar": "❌ الجلسة غير صالحة أو منتهية.\nتأكد من نسخ sessionid بشكل صحيح وحاول مرة أخرى.",
        "en": "❌ Invalid or expired session.\nMake sure you copied the sessionid correctly and try again.",
        "ru": "❌ Сессия недействительна или истекла.\nУбедитесь, что вы правильно скопировали sessionid.",
    },
    "session_success": {
        "ar": "✅ تم تسجيل الدخول بنجاح!",
        "en": "✅ Successfully logged in!",
        "ru": "✅ Успешный вход!",
    },
    "control_panel": {
        "ar": "🎛 <b>لوحة التحكم</b>\n\n👤 الحساب: @{username}\n📛 الاسم: {nickname}\n👥 المتابعين: {followers}\n👤 يتابع: {following}\n\n<blockquote>اختر العملية المطلوبة من الأزرار بالأسفل.</blockquote>",
        "en": "🎛 <b>Control Panel</b>\n\n👤 Account: @{username}\n📛 Name: {nickname}\n👥 Followers: {followers}\n👤 Following: {following}\n\n<blockquote>Choose an action from the buttons below.</blockquote>",
        "ru": "🎛 <b>Панель управления</b>\n\n👤 Аккаунт: @{username}\n📛 Имя: {nickname}\n👥 Подписчики: {followers}\n👤 Подписки: {following}\n\n<blockquote>Выберите действие из кнопок ниже.</blockquote>",
    },
    "confirm_unfollow": {
        "ar": "⚠️ <b>تأكيد إلغاء المتابعات</b>\n\n<blockquote>سيتم إلغاء متابعة جميع الحسابات ({count}).\nهذا الإجراء لا يمكن التراجع عنه!</blockquote>",
        "en": "⚠️ <b>Confirm Unfollow All</b>\n\n<blockquote>All accounts ({count}) will be unfollowed.\nThis action cannot be undone!</blockquote>",
        "ru": "⚠️ <b>Подтвердите отписку</b>\n\n<blockquote>Все аккаунты ({count}) будут отписаны.\nЭто действие нельзя отменить!</blockquote>",
    },
    "confirm_repost": {
        "ar": "⚠️ <b>تأكيد حذف الريبوستات</b>\n\n<blockquote>سيتم حذف جميع الريبوستات من حسابك.\nهذا الإجراء لا يمكن التراجع عنه!</blockquote>",
        "en": "⚠️ <b>Confirm Remove Reposts</b>\n\n<blockquote>All reposts will be removed from your account.\nThis action cannot be undone!</blockquote>",
        "ru": "⚠️ <b>Подтвердите удаление репостов</b>\n\n<blockquote>Все репосты будут удалены.\nЭто действие нельзя отменить!</blockquote>",
    },
    "lang_changed": {
        "ar": "✅ تم تغيير اللغة إلى العربية",
        "en": "✅ Language changed to English",
        "ru": "✅ Язык изменён на русский",
    },
    "btn_private": {"ar": "🔐 القسم الخاص", "en": "🔐 Private Section", "ru": "🔐 Приватный раздел"},
    "btn_search": {"ar": "🔍 قسم البحث", "en": "🔍 Search Section", "ru": "🔍 Раздел поиска"},
    "btn_lang": {"ar": "🌐 تغيير اللغة", "en": "🌐 Change Language", "ru": "🌐 Сменить язык"},
    "btn_unfollow": {"ar": "🔓 إلغاء المتابعات", "en": "🔓 Unfollow All", "ru": "🔓 Отписаться от всех"},
    "btn_repost": {"ar": "🗑 إزالة الريبوستات", "en": "🗑 Remove Reposts", "ru": "🗑 Удалить репосты"},
    "btn_delete_session": {"ar": "🚫 حذف الجلسة", "en": "🚫 Delete Session", "ru": "🚫 Удалить сессию"},
    "btn_add_account": {"ar": "➕ إضافة حساب", "en": "➕ Add Account", "ru": "➕ Добавить аккаунт"},
    "btn_back": {"ar": "🔙 رجوع", "en": "🔙 Back", "ru": "🔙 Назад"},
    "btn_confirm": {"ar": "✅ نعم، نفّذ", "en": "✅ Yes, proceed", "ru": "✅ Да, выполнить"},
    "btn_cancel": {"ar": "❌ إلغاء", "en": "❌ Cancel", "ru": "❌ Отмена"},
    "session_deleted": {
        "ar": "✅ تم حذف الجلسة بنجاح.",
        "en": "✅ Session deleted successfully.",
        "ru": "✅ Сессия успешно удалена.",
    },
    "cancelled": {
        "ar": "❌ تم إلغاء العملية.",
        "en": "❌ Operation cancelled.",
        "ru": "❌ Операция отменена.",
    },
    "search_email": {
        "ar": "📧 أرسل البريد الإلكتروني للبحث عنه:",
        "en": "📧 Send the email to search for:",
        "ru": "📧 Отправьте электронную почту для поиска:",
    },
    "search_phone": {
        "ar": "📱 أرسل رقم الهاتف للبحث عنه (مع رمز الدولة):\nمثال: +966501234567",
        "en": "📱 Send the phone number to search for (with country code):\nExample: +12025550123",
        "ru": "📱 Отправьте номер телефона для поиска (с кодом страны):\nПример: +79001234567",
    },
    "search_found": {
        "ar": "✅ <b>تم العثور على حساب مرتبط!</b>\n\n{info}",
        "en": "✅ <b>Linked account found!</b>\n\n{info}",
        "ru": "✅ <b>Найден связанный аккаунт!</b>\n\n{info}",
    },
    "search_not_found": {
        "ar": "❌ لم يتم العثور على حساب مرتبط بهذا {type}.",
        "en": "❌ No linked account found for this {type}.",
        "ru": "❌ Связанный аккаунт не найден для этого {type}.",
    },
    "search_error": {
        "ar": "❌ حدث خطأ أثناء البحث. يرجى المحاولة لاحقاً.",
        "en": "❌ An error occurred during search. Please try again later.",
        "ru": "❌ Произошла ошибка при поиске. Попробуйте позже.",
    },
    "invalid_format": {
        "ar": "❌ صيغة غير صحيحة. يرجى إدخال {type} صحيح.",
        "en": "❌ Invalid format. Please enter a valid {type}.",
        "ru": "❌ Неверный формат. Введите правильный {type}.",
    },
    "btn_search_email": {"ar": "📧 البحث بالبريد", "en": "📧 Search by Email", "ru": "📧 Поиск по email"},
    "btn_search_phone": {"ar": "📱 البحث بالهاتف", "en": "📱 Search by Phone", "ru": "📱 Поиск по телефону"},
    "btn_search_username": {"ar": "🔍 البحث باليوزر", "en": "🔍 Search by Username", "ru": "🔍 Поиск по имени"},
}

def t(key, chat_id):
    """جلب النص بلغة المستخدم"""
    lang = user_lang.get(chat_id, "ar")
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("ar", ""))

# === القواميس ===
LANGUAGE_MAP = {
    "ar": "عربي", "en": "إنجليزي", "fr": "فرنسي", "es": "إسباني",
    "de": "ألماني", "tr": "تركي", "ru": "روسي", "pt": "برتغالي",
    "id": "إندونيسي", "ja": "ياباني", "ko": "كوري", "hi": "هندي",
    "it": "إيطالي", "th": "تايلاندي", "vi": "فيتنامي", "ms": "ماليزي",
    "fil": "فلبيني", "zh": "صيني", "nl": "هولندي", "pl": "بولندي",
    "uk": "أوكراني", "sv": "سويدي", "ro": "روماني", "cs": "تشيكي",
    "el": "يوناني", "he": "عبري", "da": "دنماركي", "fi": "فنلندي",
    "hu": "مجري", "no": "نرويجي", "sk": "سلوفاكي", "bg": "بلغاري",
}

COUNTRY_MAP = {
    "SA": "السعودية 🇸🇦", "AE": "الإمارات 🇦🇪", "EG": "مصر 🇪🇬",
    "KW": "الكويت 🇰🇼", "BH": "البحرين 🇧🇭", "QA": "قطر 🇶🇦",
    "OM": "عُمان 🇴🇲", "IQ": "العراق 🇮🇶", "JO": "الأردن 🇯🇴",
    "LB": "لبنان 🇱🇧", "SY": "سوريا 🇸🇾", "PS": "فلسطين 🇵🇸",
    "YE": "اليمن 🇾🇪", "LY": "ليبيا 🇱🇾", "TN": "تونس 🇹🇳",
    "DZ": "الجزائر 🇩🇿", "MA": "المغرب 🇲🇦", "SD": "السودان 🇸🇩",
    "US": "الولايات المتحدة 🇺🇸", "GB": "بريطانيا 🇬🇧",
    "CA": "كندا 🇨🇦", "AU": "أستراليا 🇦🇺", "DE": "ألمانيا 🇩🇪",
    "FR": "فرنسا 🇫🇷", "TR": "تركيا 🇹🇷", "RU": "روسيا 🇷🇺",
    "IN": "الهند 🇮🇳", "PK": "باكستان 🇵🇰", "BR": "البرازيل 🇧🇷",
    "ID": "إندونيسيا 🇮🇩", "MY": "ماليزيا 🇲🇾", "PH": "الفلبين 🇵🇭",
    "TH": "تايلاند 🇹🇭", "VN": "فيتنام 🇻🇳", "JP": "اليابان 🇯🇵",
    "KR": "كوريا الجنوبية 🇰🇷", "CN": "الصين 🇨🇳", "MX": "المكسيك 🇲🇽",
    "ES": "إسبانيا 🇪🇸", "IT": "إيطاليا 🇮🇹", "NL": "هولندا 🇳🇱",
    "SG": "سنغافورة 🇸🇬", "NG": "نيجيريا 🇳🇬", "ZA": "جنوب أفريقيا 🇿🇦",
    "PL": "بولندا 🇵🇱", "SE": "السويد 🇸🇪", "NO": "النرويج 🇳🇴",
    "DK": "الدنمارك 🇩🇰", "FI": "فنلندا 🇫🇮", "IE": "أيرلندا 🇮🇪",
    "NZ": "نيوزيلندا 🇳🇿", "AR": "الأرجنتين 🇦🇷", "CL": "تشيلي 🇨🇱",
    "CO": "كولومبيا 🇨🇴", "PE": "بيرو 🇵🇪",
}

STAR_PRICE = 350

# === الدوال المساعدة ===
def format_number(num):
    if isinstance(num, str):
        return num
    if num >= 1000000000:
        return f"{num/1000000000:.2f}B"
    elif num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num:,}"
    return str(num)

def get_account_age(create_time):
    try:
        created_at_dt = datetime.fromtimestamp(create_time)
        now = datetime.now()
        diff = now - created_at_dt
        days = diff.days
        years = days // 365
        remaining = days % 365
        months = remaining // 30
        
        parts = []
        if years > 0: parts.append(f"{years} سنة")
        if months > 0: parts.append(f"{months} شهر")
        if not parts: parts.append(f"{days} يوم")
        return " و ".join(parts)
    except:
        return "غير متوفر"

def timestamp_to_date(timestamp):
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    except:
        return "غير متوفر"

# === دوال TikTok API ===
def get_tikwm_user(username):
    """جلب معلومات المستخدم عبر TikWM API"""
    try:
        url = f"https://www.tikwm.com/api/user/info?unique_id={username}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0:
                return data.get("data")
    except:
        pass
    return None

def get_countik_userinfo(sec_uid):
    """جلب معلومات إضافية عبر Countik"""
    try:
        url = f"https://countik.com/api/userinfo?sec_user_id={sec_uid}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def get_countik_analyze(sec_uid):
    """تحليل الحساب عبر Countik"""
    try:
        url = f"https://countik.com/api/analyze?sec_user_id={sec_uid}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def get_region_from_videos(username, video_id):
    """محاولة استنتاج الدولة من الفيديو"""
    try:
        url = f"https://www.tikwm.com/api/video/info?url=https://www.tiktok.com/@{username}/video/{video_id}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("region")
    except:
        pass
    return None

def get_stories(username):
    """جلب الستوري"""
    try:
        url = f"https://www.tikwm.com/api/user/posts?unique_id={username}&count=10"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json().get("data")
    except:
        pass
    return None

def verify_session(session_key):
    """التحقق من صحة sessionid وجلب معلومات الحساب"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': f'sessionid={session_key}; sid_tt={session_key}',
    }
    try:
        r = requests.get('https://www.tiktok.com/api/user/detail/?device_id=7315123456789012345', headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("userInfo"):
                return data.get("userInfo")
    except:
        pass
    return None

def get_following_list(session_key, user_id, count=100):
    """جلب قائمة المتابَعين (الأشخاص الذين يتابعهم الحساب)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': f'sessionid={session_key}; sid_tt={session_key}',
    }
    following = []
    cursor = 0
    try:
        while len(following) < count:
            url = f'https://www.tiktok.com/api/user/list/?count=30&cursor={cursor}&type=1&user_id={user_id}'
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                users = data.get("userList", []) or data.get("user_list", [])
                if not users: break
                following.extend(users)
                if not data.get("hasMore", False): break
                cursor = data.get("cursor", 0)
            else:
                break
            time.sleep(1)
    except:
        pass
    return following[:count]

def unfollow_user(session_key, target_uid, target_sec_uid):
    """إلغاء متابعة مستخدم"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': f'sessionid={session_key}; sid_tt={session_key}',
        'Referer': 'https://www.tiktok.com/',
    }
    try:
        url = f'https://www.tiktok.com/api/commit/follow/user/?type=0&object_id={target_uid}&sec_user_id={target_sec_uid}'
        r = requests.post(url, headers=headers, timeout=15)
        return r.status_code == 200 and r.json().get("status_code") == 0
    except:
        return False

def remove_repost(session_key, video_id):
    """حذف ريبوست"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': f'sessionid={session_key}; sid_tt={session_key}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    try:
        url = 'https://www.tiktok.com/passport/repost/item/delete/'
        data = {'item_id': video_id}
        r = requests.post(url, data=data, headers=headers, timeout=15)
        return r.status_code == 200
    except:
        return False

def search_by_email_tiktok(email, session_key=None):
    """البحث عن حساب تيك توك عبر البريد الإلكتروني"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    # محاولة 1: عبر API داخلي (يتطلب session)
    if session_key:
        try:
            auth_headers = headers.copy()
            auth_headers['Cookie'] = f'sessionid={session_key}; sid_tt={session_key}'
            r = requests.get(f'https://www.tiktok.com/api/user/find_by_email/?email={email}', headers=auth_headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("user"): return data["user"]
        except:
            pass
    
    # محاولة 2: عبر passport (فحص وجود الحساب)
    try:
        r = requests.post(
            'https://www.tiktok.com/passport/web/email/check_availability/',
            data={'email': email},
            headers=headers,
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("data") and data["data"].get("is_registered"):
                return {"exists": True, "masked_email": email}
    except:
        pass
    return None

def search_by_phone_tiktok(phone, session_key=None):
    """البحث عن حساب تيك توك عبر رقم الهاتف"""
    clean_phone = phone.replace("+", "").replace(" ", "")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    # محاولة 1: عبر contact sync (تتطلب session)
    if session_key:
        try:
            auth_headers = headers.copy()
            auth_headers['Cookie'] = f'sessionid={session_key}; sid_tt={session_key}'
            auth_headers['Content-Type'] = 'application/json'
            payload = json.dumps({"contacts": [{"phone": clean_phone, "contact_name": "search"}]})
            r = requests.post(
                'https://www.tiktok.com/api/user/find_contacts/',
                data=payload,
                headers=auth_headers,
                timeout=15
            )
            if r.status_code == 200:
                data = r.json()
                contacts = data.get("contacts", []) or data.get("data", {}).get("contacts", [])
                if contacts:
                    return contacts[0]
        except:
            pass
    
    # محاولة 2: عبر password reset flow
    try:
        r = requests.post(
            'https://www.tiktok.com/passport/web/send_code/',
            data={'mobile': clean_phone, 'type': '2', 'account_sdk_source': 'web'},
            headers=headers,
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("data") and data["data"].get("mask_mobile"):
                return {"masked_phone": data["data"]["mask_mobile"], "exists": True}
            elif data.get("message") == "success":
                return {"exists": True, "phone": phone}
    except:
        pass
    
    # محاولة 3: عبر account check
    try:
        r = requests.post(
            'https://www.tiktok.com/passport/web/account/check/',
            data={'mobile': clean_phone, 'scene': 'find_account'},
            headers=headers,
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("data"):
                return data["data"]
    except:
        pass
    
    return None

# === دالة تحميل فيديو تيك توك ===
def download_tiktok_video(url):
    """تحميل فيديو تيك توك بدون علامة مائية - يرجع رابط التحميل ومعلومات الفيديو"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    # محاولة 1: عبر tikwm API (الأسرع والأفضل)
    try:
        r = requests.get(
            f'https://www.tikwm.com/api/?url={url}&hd=1',
            headers=headers,
            timeout=20
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0 and data.get("data"):
                video_data = data["data"]
                play_url = video_data.get("hdplay") or video_data.get("play") or video_data.get("wmplay")
                if play_url:
                    return {
                        "play_url": play_url,
                        "title": video_data.get("title", ""),
                        "author": video_data.get("author", {}).get("unique_id", ""),
                        "duration": video_data.get("duration", 0),
                        "cover": video_data.get("cover", ""),
                    }
    except:
        pass
    
    # محاولة 2: عبر tikwm POST
    try:
        r = requests.post(
            'https://www.tikwm.com/api/',
            data={'url': url, 'hd': '1'},
            headers=headers,
            timeout=20
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0 and data.get("data"):
                video_data = data["data"]
                play_url = video_data.get("hdplay") or video_data.get("play") or video_data.get("wmplay")
                if play_url:
                    return {
                        "play_url": play_url,
                        "title": video_data.get("title", ""),
                        "author": video_data.get("author", {}).get("unique_id", ""),
                        "duration": video_data.get("duration", 0),
                        "cover": video_data.get("cover", ""),
                    }
    except:
        pass
    
    # محاولة 3: عبر صفحة تيك توك مباشرة (scraping)
    try:
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if r.status_code == 200:
            import re as re_mod
            match = re_mod.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', r.text)
            if match:
                page_data = json.loads(match.group(1))
                default_scope = page_data.get('__DEFAULT_SCOPE__', {})
                detail = default_scope.get('webapp.video-detail', {})
                item = detail.get('itemInfo', {}).get('itemStruct', {})
                if item:
                    video = item.get('video', {})
                    # جلب رابط التحميل من bitrateInfo
                    bitrate_info = video.get('bitrateInfo', [])
                    play_url = None
                    if bitrate_info:
                        url_list = bitrate_info[0].get('PlayAddr', {}).get('UrlList', [])
                        if url_list:
                            play_url = url_list[0]
                    if not play_url:
                        play_url = video.get('downloadAddr') or video.get('playAddr')
                    
                    if play_url:
                        return {
                            "play_url": play_url,
                            "title": item.get("desc", ""),
                            "author": item.get("author", {}).get("uniqueId", ""),
                            "duration": video.get("duration", 0),
                            "cover": video.get("cover", ""),
                        }
    except:
        pass
    
    return None

# === دوال الاشتراك الإجباري والأدمن ===
def is_subscribed(user_id):
    for channel in FORCED_CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            # إذا فشل البوت في التحقق (مثلاً ليس أدمن في القناة)
            continue
    return True

def get_forced_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for channel in FORCED_CHANNELS:
        try:
            chat = bot.get_chat(channel)
            title = chat.title
            url = f"https://t.me/{chat.username}" if chat.username else f"https://t.me/{channel}"
            markup.add(types.InlineKeyboardButton(f"اشترك في: {title}", url=url))
        except:
            markup.add(types.InlineKeyboardButton(f"اشترك هنا: {channel}", url=f"https://t.me/{channel.replace('@', '')}"))
    markup.add(types.InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_sub"))
    return markup

def admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("إحصائيات 📊", callback_data="admin_stats"),
        types.InlineKeyboardButton("إرسال جماعي 📢", callback_data="admin_broadcast"),
    )
    markup.add(
        types.InlineKeyboardButton("إضافة قناة ➕", callback_data="admin_add_channel"),
        types.InlineKeyboardButton("حذف قناة ➖", callback_data="admin_del_channel"),
    )
    markup.add(
        types.InlineKeyboardButton("قائمة القنوات 📋", callback_data="admin_list_channels"),
    )
    return markup

# === أمر البداية ===
@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id
    user = message.from_user
    
    # إشعار مستخدم جديد
    if chat_id not in all_users:
        all_users.append(chat_id)
        save_data(USERS_FILE, all_users)
        try:
            admin_msg = (
                f"👤 مستخدم جديد بدأ البوت:\n\n"
                f"├ الاسم: {user.first_name}\n"
                f"├ اليوزر: @{user.username if user.username else 'لا يوجد'}\n"
                f"└ الآيدي: <code>{chat_id}</code>"
            )
            bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")
        except:
            pass

    # تحقق من الاشتراك الإجباري
    if not is_subscribed(chat_id):
        bot.send_message(chat_id, "⚠️ عذراً، يجب عليك الاشتراك في قنوات البوت أولاً لتتمكن من استخدامه.", reply_markup=get_forced_markup())
        return

    if chat_id not in user_lang:
        user_lang[chat_id] = "ar"
    
    first_name = message.from_user.first_name if message.from_user and message.from_user.first_name else ""
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(t("btn_private", chat_id), callback_data="menu_private"),
        types.InlineKeyboardButton(t("btn_search", chat_id), callback_data="menu_search"),
    )
    markup.add(
        types.InlineKeyboardButton(t("btn_lang", chat_id), callback_data="menu_lang"),
    )
    
    welcome_text = t("welcome", chat_id).format(first_name=first_name)
    welcome_text += "\n\n🤖 TikWahmbot"
    bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=markup)

# === أمر الأدمن ===
@bot.message_handler(commands=["admin"])
def send_admin(message):
    if message.chat.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, "مرحباً بك في لوحة تحكم الأدمن 🔐", reply_markup=admin_panel())

# === معالجة الدفع ===
@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    payload = message.successful_payment.invoice_payload
    parts = payload.split("|")
    if len(parts) == 2:
        response = (
            "✅ تم الدفع بنجاح!\n\n"
            "⏳ هذه الميزة قيد التطوير حالياً.\n"
            "🔜 قريباً - ساعات محددة ونضيفها!\n\n"
            "شكراً لدعمك 💎\n\nTikWahmbot"
        )
        bot.send_message(message.chat.id, response)

# === معالجة Callbacks ===
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data
    
    # تحقق من الاشتراك عند الضغط على زر التحقق
    if data == "check_sub":
        if is_subscribed(chat_id):
            bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح، يمكنك الآن استخدام البوت.")
            bot.delete_message(chat_id, call.message.message_id)
            send_welcome(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات بعد!", show_alert=True)
        return

    # === لوحة تحكم الأدمن ===
    if chat_id == ADMIN_ID:
        if data == "admin_stats":
            stats = (
                f"📊 إحصائيات البوت:\n\n"
                f"├ عدد المستخدمين: {len(all_users)}\n"
                f"├ عدد القنوات الإجبارية: {len(FORCED_CHANNELS)}\n"
                f"└ عدد الجلسات النشطة: {len(user_sessions)}"
            )
            bot.edit_message_text(stats, chat_id, call.message.message_id, reply_markup=admin_panel())
        
        elif data == "admin_broadcast":
            user_states[chat_id] = {"state": "waiting_broadcast"}
            bot.send_message(chat_id, "أرسل الرسالة التي تريد إرسالها للجميع (نص فقط):")
        
        elif data == "admin_add_channel":
            user_states[chat_id] = {"state": "waiting_add_channel"}
            bot.send_message(chat_id, "أرسل معرف القناة (مثال: @TikWahm):")
            
        elif data == "admin_del_channel":
            if not FORCED_CHANNELS:
                bot.answer_callback_query(call.id, "لا توجد قنوات لحذفها")
                return
            markup = types.InlineKeyboardMarkup()
            for ch in FORCED_CHANNELS:
                markup.add(types.InlineKeyboardButton(ch, callback_data=f"delch_{ch}"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_main"))
            bot.edit_message_text("اختر القناة المراد حذفها:", chat_id, call.message.message_id, reply_markup=markup)
            
        elif data == "admin_list_channels":
            if not FORCED_CHANNELS:
                bot.answer_callback_query(call.id, "لا توجد قنوات مضافة")
                return
            msg = "📋 قائمة القنوات الإجبارية:\n\n" + "\n".join(FORCED_CHANNELS)
            bot.edit_message_text(msg, chat_id, call.message.message_id, reply_markup=admin_panel())
            
        elif data == "admin_main":
            bot.edit_message_text("مرحباً بك في لوحة تحكم الأدمن 🔐", chat_id, call.message.message_id, reply_markup=admin_panel())
            
        elif data.startswith("delch_"):
            ch = data.replace("delch_", "")
            if ch in FORCED_CHANNELS:
                FORCED_CHANNELS.remove(ch)
                save_data(CHANNELS_FILE, FORCED_CHANNELS)
                bot.answer_callback_query(call.id, f"تم حذف القناة {ch}")
                # تحديث القائمة
                handle_callback(type('obj', (object,), {'message': call.message, 'data': 'admin_del_channel', 'id': call.id, 'from_user': call.from_user}))
            return

    # === القائمة الرئيسية ===
    if data == "menu_main":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(t("btn_private", chat_id), callback_data="menu_private"),
            types.InlineKeyboardButton(t("btn_search", chat_id), callback_data="menu_search"),
        )
        markup.add(
            types.InlineKeyboardButton(t("btn_lang", chat_id), callback_data="menu_lang"),
        )
        first_name = ""
        if call.from_user and call.from_user.first_name:
            first_name = call.from_user.first_name
        welcome_text = t("welcome", chat_id).format(first_name=first_name)
        welcome_text += "\n\nTikWahmbot"
        try:
            bot.edit_message_text(welcome_text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=markup)
    
    # === تغيير اللغة ===
    elif data == "menu_lang":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.add(
            types.InlineKeyboardButton("🇸🇦 عربي", callback_data="set_lang_ar"),
            types.InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en"),
            types.InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru"),
        )
        markup.add(types.InlineKeyboardButton(t("btn_back", chat_id), callback_data="menu_main"))
        try:
            bot.edit_message_text("🌐 اختر اللغة / Choose language / Выберите язык:", chat_id, call.message.message_id, reply_markup=markup)
        except:
            bot.send_message(chat_id, "🌐 اختر اللغة / Choose language / Выберите язык:", reply_markup=markup)
    
    elif data.startswith("set_lang_"):
        lang = data.replace("set_lang_", "")
        user_lang[chat_id] = lang
        bot.answer_callback_query(call.id, t("lang_changed", chat_id))
        # إعادة عرض القائمة الرئيسية
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(t("btn_private", chat_id), callback_data="menu_private"),
            types.InlineKeyboardButton(t("btn_search", chat_id), callback_data="menu_search"),
        )
        markup.add(
            types.InlineKeyboardButton(t("btn_lang", chat_id), callback_data="menu_lang"),
        )
        first_name = ""
        if call.from_user and call.from_user.first_name:
            first_name = call.from_user.first_name
        welcome_text = t("welcome", chat_id).format(first_name=first_name)
        welcome_text += "\n\nTikWahmbot"
        try:
            bot.edit_message_text(welcome_text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=markup)
    
    # === قسم البحث (معدل - مع أزرار البحث بالبريد والهاتف) ===
    elif data == "menu_search":
        bot.answer_callback_query(call.id)
        lang = user_lang.get(chat_id, "ar")
        search_texts = {
            "ar": "🔍 <b>قسم البحث</b>\n\n<blockquote>اختر طريقة البحث أو أرسل يوزر تيك توك مباشرة.</blockquote>",
            "en": "🔍 <b>Search Section</b>\n\n<blockquote>Choose a search method or send a TikTok username directly.</blockquote>",
            "ru": "🔍 <b>Раздел поиска</b>\n\n<blockquote>Выберите метод поиска или отправьте имя пользователя TikTok напрямую.</blockquote>",
        }
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(t("btn_search_email", chat_id), callback_data="search_by_email"),
            types.InlineKeyboardButton(t("btn_search_phone", chat_id), callback_data="search_by_phone"),
        )
        markup.add(types.InlineKeyboardButton(t("btn_back", chat_id), callback_data="menu_main"))
        footer = "\n\nTikWahmbot"
        try:
            bot.edit_message_text(search_texts.get(lang, search_texts["ar"]) + footer, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, search_texts.get(lang, search_texts["ar"]) + footer, parse_mode="HTML", reply_markup=markup)
    
    # === البحث بالبريد ===
    elif data == "search_by_email":
        bot.answer_callback_query(call.id)
        user_states[chat_id] = {"state": "waiting_email"}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(t("btn_cancel", chat_id), callback_data="cancel_action"))
        try:
            bot.edit_message_text(t("search_email", chat_id), chat_id, call.message.message_id, reply_markup=markup)
        except:
            bot.send_message(chat_id, t("search_email", chat_id), reply_markup=markup)
    
    # === البحث بالهاتف ===
    elif data == "search_by_phone":
        bot.answer_callback_query(call.id)
        user_states[chat_id] = {"state": "waiting_phone"}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(t("btn_cancel", chat_id), callback_data="cancel_action"))
        try:
            bot.edit_message_text(t("search_phone", chat_id), chat_id, call.message.message_id, reply_markup=markup)
        except:
            bot.send_message(chat_id, t("search_phone", chat_id), reply_markup=markup)
    
    # === القسم الخاص ===
    elif data == "menu_private":
        bot.answer_callback_query(call.id)
        
        # تحقق إذا عنده حساب مسجل
        if chat_id in user_sessions and user_sessions[chat_id].get("session_key"):
            # عرض لوحة التحكم
            show_control_panel(chat_id, call.message.message_id)
        else:
            # لا يوجد حساب
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton(t("btn_add_account", chat_id), callback_data="add_account"),
                types.InlineKeyboardButton(t("btn_back", chat_id), callback_data="menu_main"),
            )
            footer = "\n\nTikWahmbot"
            try:
                bot.edit_message_text(
                    t("private_section", chat_id) + "\n\n" + t("no_accounts", chat_id) + footer,
                    chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup
                )
            except:
                bot.send_message(chat_id, t("private_section", chat_id) + "\n\n" + t("no_accounts", chat_id) + footer, parse_mode="HTML", reply_markup=markup)
    
    # === إضافة حساب ===
    elif data == "add_account":
        bot.answer_callback_query(call.id)
        user_states[chat_id] = {"state": "waiting_session"}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(t("btn_cancel", chat_id), callback_data="cancel_action"))
        try:
            bot.edit_message_text(t("add_account_guide", chat_id), chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, t("add_account_guide", chat_id), parse_mode="HTML", reply_markup=markup)
    
    # === لوحة التحكم - إلغاء المتابعات ===
    elif data == "action_unfollow":
        bot.answer_callback_query(call.id)
        session = user_sessions.get(chat_id, {})
        following_count = session.get("following", 0)
        
        text = t("confirm_unfollow", chat_id).format(count=following_count)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(t("btn_confirm", chat_id), callback_data="exec_unfollow"),
            types.InlineKeyboardButton(t("btn_cancel", chat_id), callback_data="menu_private"),
        )
        try:
            bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
    
    # === لوحة التحكم - حذف الريبوستات ===
    elif data == "action_repost":
        bot.answer_callback_query(call.id)
        text = t("confirm_repost", chat_id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(t("btn_confirm", chat_id), callback_data="exec_repost"),
            types.InlineKeyboardButton(t("btn_cancel", chat_id), callback_data="menu_private"),
        )
        try:
            bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        except:
            bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
    
    # === تنفيذ إلغاء المتابعات ===
    elif data == "exec_unfollow":
        bot.answer_callback_query(call.id, "جاري التنفيذ...")
        session = user_sessions.get(chat_id, {})
        session_key = session.get("session_key")
        
        if not session_key:
            bot.send_message(chat_id, "❌ لا توجد جلسة. أضف حسابك أولاً.")
            return
        
        def do_unfollow():
            bot.send_message(chat_id, "⏳ جاري إلغاء المتابعات...")
            my_user_id = session.get("user_id")
            if not my_user_id:
                bot.send_message(chat_id, "❌ لا يوجد معرف حساب. أعد إضافة حسابك.")
                return
            following = get_following_list(session_key, my_user_id)
            
            if not following:
                bot.send_message(chat_id, "✅ لا يوجد حسابات متابَعة!")
                return
            
            total = len(following)
            success = 0
            failed = 0
            
            for i, user in enumerate(following, 1):
                uid = user.get("user", {}).get("id")
                sec_uid = user.get("user", {}).get("secUid")
                if uid and sec_uid:
                    if unfollow_user(session_key, uid, sec_uid):
                        success += 1
                    else:
                        failed += 1
                
                if i % 10 == 0:
                    bot.send_message(chat_id, f"⏳ {i}/{total} | ✅ {success} | ❌ {failed}")
                time.sleep(2)
            
            bot.send_message(chat_id, f"✅ اكتمل!\n\n📊 الإجمالي: {total}\n✅ نجح: {success}\n❌ فشل: {failed}\n\nTikWahmbot")
        
        threading.Thread(target=do_unfollow, daemon=True).start()
    
    # === تنفيذ حذف الريبوستات ===
    elif data == "exec_repost":
        bot.answer_callback_query(call.id, "جاري التنفيذ...")
        session = user_sessions.get(chat_id, {})
        session_key = session.get("session_key")
        
        if not session_key:
            bot.send_message(chat_id, "❌ لا توجد جلسة. أضف حسابك أولاً.")
            return
        
        def do_remove_reposts():
            bot.send_message(chat_id, "⏳ جاري حذف الريبوستات...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Cookie': f'sessionid={session_key}; sid_tt={session_key}',
            }
            
            reposts = []
            cursor = 0
            while True:
                try:
                    r = requests.get(f'https://www.tiktok.com/api/user/repost/list/?count=20&cursor={cursor}', headers=headers, timeout=15)
                    if r.status_code == 200:
                        data = r.json()
                        items = data.get("itemList", []) or data.get("item_list", [])
                        if not items:
                            break
                        reposts.extend(items)
                        if not data.get("hasMore", False):
                            break
                        cursor = data.get("cursor", 0)
                    else:
                        break
                except:
                    break
                time.sleep(1)
            
            if not reposts:
                bot.send_message(chat_id, "✅ لا يوجد ريبوستات!")
                return
            
            total = len(reposts)
            success = 0
            failed = 0
            
            for i, item in enumerate(reposts, 1):
                video_id = item.get("id") or item.get("video", {}).get("id")
                if video_id:
                    if remove_repost(session_key, video_id):
                        success += 1
                    else:
                        failed += 1
                if i % 10 == 0:
                    bot.send_message(chat_id, f"⏳ {i}/{total} | ✅ {success} | ❌ {failed}")
                time.sleep(2)
            
            bot.send_message(chat_id, f"✅ اكتمل!\n\n📊 الإجمالي: {total}\n✅ نجح: {success}\n❌ فشل: {failed}\n\nTikWahmbot")
        
        threading.Thread(target=do_remove_reposts, daemon=True).start()
    
    # === حذف الجلسة ===
    elif data == "delete_session":
        bot.answer_callback_query(call.id)
        if chat_id in user_sessions:
            del user_sessions[chat_id]
        bot.send_message(chat_id, t("session_deleted", chat_id) + "\n\nTikWahmbot")
    
    # === إلغاء ===
    elif data == "cancel_action":
        bot.answer_callback_query(call.id)
        if chat_id in user_states:
            del user_states[chat_id]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(t("btn_back", chat_id), callback_data="menu_main"))
        try:
            bot.edit_message_text(t("cancelled", chat_id), chat_id, call.message.message_id, reply_markup=markup)
        except:
            bot.send_message(chat_id, t("cancelled", chat_id))
    
    # === أزرار البحث ===
    elif data.startswith("story_"):
        username = data.replace("story_", "")
        bot.answer_callback_query(call.id, "جاري تحميل الستوري...")
        story_data = get_stories(username)
        if story_data and story_data.get("videos") and len(story_data["videos"]) > 0:
            stories = story_data["videos"]
            for i, story in enumerate(stories[:5], 1):
                video_url = story.get("play") or story.get("wmplay")
                if video_url:
                    try:
                        bot.send_video(chat_id, video_url, caption=f"📖 ستوري {i}/{len(stories)} - @{username}\n\nTikWahmbot")
                    except:
                        bot.send_message(chat_id, f"📖 ستوري {i}: {video_url}\n\nTikWahmbot")
        else:
            bot.send_message(chat_id, f"❌ لا يوجد ستوري متاح لـ @{username}\n\nTikWahmbot")
    
    elif data.startswith("level_"):
        username = data.replace("level_", "")
        bot.answer_callback_query(call.id, "جاري جلب المستوى...")
        
        user_data = get_tikwm_user(username)
        if not user_data:
            bot.send_message(chat_id, "❌ خطأ في جلب البيانات.")
            return
        
        sec_uid = user_data.get("user", {}).get("secUid", "")
        stats = user_data.get("stats", {})
        followers = stats.get("followerCount", 0)
        likes = stats.get("heartCount", 0)
        videos_count = stats.get("videoCount", 0)
        digg_count = stats.get("diggCount", 0)
        
        analyze_data = get_countik_analyze(sec_uid) if sec_uid else None
        earnings = analyze_data.get("earnings") if analyze_data else None
        engagement = analyze_data.get("engagement_rates") if analyze_data else None
        performance = analyze_data.get("performance") if analyze_data else None
        hashtags_data = analyze_data.get("hashtags", []) if analyze_data else []
        
        ins_id = user_data.get("user", {}).get("ins_id", "") or None
        twitter_id = user_data.get("user", {}).get("twitter_id", "") or None
        youtube_title = user_data.get("user", {}).get("youtube_channel_title", "") or None
        
        avg_likes = likes // videos_count if videos_count > 0 else 0
        engagement_rate = "غير متوفر"
        if followers > 0 and videos_count > 0:
            eng_rate = ((likes / videos_count) / followers) * 100
            engagement_rate = f"{eng_rate:.2f}%"
        
        level_text = f"📊 مستوى حساب @{username}\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        level_text += f"• الحسابات المربوطة\n├ انستقرام: {ins_id if ins_id else 'غير مربوط ❌'}\n├ تويتر: {twitter_id if twitter_id else 'غير مربوط ❌'}\n└ يوتيوب: {youtube_title if youtube_title else 'غير مربوط ❌'}\n\n"
        level_text += f"• إحصائيات متقدمة\n├ إعجابات أعطاها: {format_number(digg_count)}\n├ متوسط الإعجابات/فيديو: {format_number(avg_likes)}\n└ معدل التفاعل: {engagement_rate}\n\n"
        
        if earnings:
            level_text += f"• الأرباح التقديرية\n├ الحد الأدنى: ${earnings.get('min', 0):.2f}\n└ الحد الأقصى: ${earnings.get('max', 0):.2f}\n\n"
        if engagement:
            level_text += f"• معدلات التفاعل\n├ الإعجابات: {engagement.get('likes_rate', 0)}%\n├ التعليقات: {engagement.get('comments_rate', 0)}%\n├ المشاركات: {engagement.get('shares_rate', 0)}%\n└ الإجمالي: {engagement.get('total_rate', 0)}%\n\n"
        if performance:
            level_text += f"• متوسط الأداء\n├ المشاهدات: {format_number(performance.get('avgViews', 0))}\n├ الإعجابات: {format_number(performance.get('avgLikes', 0))}\n├ التعليقات: {format_number(performance.get('avgComments', 0))}\n└ المشاركات: {format_number(performance.get('avgShares', 0))}\n\n"
        if hashtags_data:
            level_text += f"• أكثر الهاشتاقات\n"
            for h in hashtags_data[:5]:
                if isinstance(h, dict):
                    level_text += f"├ #{h.get('name', '')} ({h.get('count', 0)}x)\n"
        
        level_text += "\nTikWahmbot"
        bot.send_message(chat_id, level_text)
    
    elif data.startswith("pay_"):
        parts = data.split("_", 2)
        if len(parts) == 3:
            action = parts[1]
            username = parts[2]
            titles = {
                "followers": "👥 عرض قائمة المتابعين",
                "following": "👤 عرض قائمة المتابَعين",
                "binding": "🔗 كشف نوع ربط الحساب",
            }
            title = titles.get(action, "ميزة مدفوعة")
            description = f"الحصول على {title} لحساب @{username}"
            payload = f"{action}|{username}"
            try:
                prices = [types.LabeledPrice(label=title, amount=STAR_PRICE)]
                bot.send_invoice(
                    chat_id=chat_id, title=title, description=description,
                    invoice_payload=payload, provider_token="", currency="XTR", prices=prices,
                )
                bot.answer_callback_query(call.id)
            except Exception as e:
                bot.answer_callback_query(call.id, f"خطأ: {e}", show_alert=True)

def show_control_panel(chat_id, message_id=None):
    """عرض لوحة التحكم"""
    session = user_sessions.get(chat_id, {})
    text = t("control_panel", chat_id).format(
        username=session.get("username", "?"),
        nickname=session.get("nickname", "?"),
        followers=format_number(session.get("followers", 0)),
        following=format_number(session.get("following", 0)),
    )
    text += "\n\nTikWahmbot"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(t("btn_unfollow", chat_id), callback_data="action_unfollow"),
        types.InlineKeyboardButton(t("btn_repost", chat_id), callback_data="action_repost"),
    )
    markup.add(
        types.InlineKeyboardButton(t("btn_delete_session", chat_id), callback_data="delete_session"),
    )
    markup.add(
        types.InlineKeyboardButton(t("btn_back", chat_id), callback_data="menu_main"),
    )
    
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)
            return
        except:
            pass
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

# === معالجة الرسائل ===
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip() if message.text else ""
    
    # تحقق من الاشتراك الإجباري
    if not is_subscribed(chat_id):
        bot.send_message(chat_id, "⚠️ عذراً، يجب عليك الاشتراك في قنوات البوت أولاً لتتمكن من استخدامه.", reply_markup=get_forced_markup())
        return

    if chat_id not in user_lang:
        user_lang[chat_id] = "ar"
    
    # === معالجة حالات الأدمن ===
    state = user_states.get(chat_id, {})
    if chat_id == ADMIN_ID:
        if state.get("state") == "waiting_broadcast":
            del user_states[chat_id]
            success = 0
            failed = 0
            bot.send_message(chat_id, f"⏳ جاري الإرسال إلى {len(all_users)} مستخدم...")
            for uid in all_users:
                try:
                    bot.send_message(uid, text + "\n\nTikWahmbot")
                    success += 1
                except:
                    failed += 1
                time.sleep(0.1)
            bot.send_message(chat_id, f"✅ اكتمل الإرسال!\n├ نجح: {success}\n└ فشل: {failed}")
            return
            
        elif state.get("state") == "waiting_add_channel":
            del user_states[chat_id]
            if text.startswith("@") or text.lstrip("-").isdigit():
                if text not in FORCED_CHANNELS:
                    FORCED_CHANNELS.append(text)
                    save_data(CHANNELS_FILE, FORCED_CHANNELS)
                    bot.send_message(chat_id, f"✅ تم إضافة القناة {text} بنجاح.")
                else:
                    bot.send_message(chat_id, "⚠️ القناة مضافة بالفعل.")
            else:
                bot.send_message(chat_id, "❌ معرف قناة غير صحيح.")
            return

    # === حالة انتظار session_key (معدل - تحقق تلقائي بدون طلب يوزرنيم) ===
    if state.get("state") == "waiting_session":
        session_key = text.strip()
        # التحقق من شكل الـ session (32 حرف hex)
        if len(session_key) == 32 and all(c in '0123456789abcdef' for c in session_key):
            bot.send_chat_action(chat_id, 'typing')
            bot.send_message(chat_id, t("verifying", chat_id))
            
            # التحقق الحقيقي من الجلسة عبر TikTok API
            user_info = verify_session(session_key)
            if user_info:
                # الجلسة شغالة - نسحب المعلومات تلقائياً
                user = user_info.get("user", {})
                stats = user_info.get("stats", {})
                username = user.get("uniqueId", "?")
                nickname = user.get("nickname", "?")
                user_id = user.get("id", "")
                followers = stats.get("followerCount", 0)
                following_count = stats.get("followingCount", 0)
                
                user_sessions[chat_id] = {
                    "session_key": session_key,
                    "username": username,
                    "nickname": nickname,
                    "user_id": user_id,
                    "followers": followers,
                    "following": following_count,
                }
                del user_states[chat_id]
                
                bot.send_message(chat_id, t("session_success", chat_id))
                show_control_panel(chat_id)
            else:
                # الجلسة غير صالحة
                del user_states[chat_id]
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(t("btn_add_account", chat_id), callback_data="add_account"),
                    types.InlineKeyboardButton(t("btn_back", chat_id), callback_data="menu_main"),
                )
                bot.send_message(chat_id, t("session_invalid", chat_id), reply_markup=markup)
        else:
            bot.send_message(chat_id, "❌ صيغة الجلسة غير صحيحة. يجب أن تكون 32 حرف. حاول مرة أخرى.")
        return
    
    # === حالة البحث بالبريد الإلكتروني ===
    if state.get("state") == "waiting_email":
        email = text.strip()
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            bot.send_chat_action(chat_id, 'typing')
            bot.send_message(chat_id, "🔍 جاري البحث عن البريد الإلكتروني...")
            
            # استخدام session_key إذا متوفر للبحث الأقوى
            user_session = user_sessions.get(chat_id, {})
            sk = user_session.get("session_key")
            result = search_by_email_tiktok(email, session_key=sk)
            if result:
                # تجميع المعلومات المتاحة
                info_parts = []
                if result.get("uniqueId"):
                    info_parts.append(f"├ اليوزر: @{result['uniqueId']}")
                if result.get("nickname"):
                    info_parts.append(f"├ الاسم: {result['nickname']}")
                if result.get("masked_email"):
                    info_parts.append(f"├ البريد: {result['masked_email']}")
                if result.get("exists"):
                    info_parts.append(f"├ الحالة: حساب موجود ✅")
                if result.get("uid"):
                    info_parts.append(f"├ المعرف: {result['uid']}")
                
                if not info_parts:
                    info_parts.append("├ الحالة: حساب موجود ✅")
                
                info_text = "\n".join(info_parts)
                bot.send_message(chat_id, t("search_found", chat_id).format(info=info_text) + "\n\nTikWahmbot", parse_mode="HTML")
            else:
                lang = user_lang.get(chat_id, "ar")
                type_name = "البريد الإلكتروني" if lang == "ar" else ("email" if lang == "en" else "электронной почте")
                bot.send_message(chat_id, t("search_not_found", chat_id).format(type=type_name) + "\n\nTikWahmbot")
            
            del user_states[chat_id]
        else:
            lang = user_lang.get(chat_id, "ar")
            type_name = "بريد إلكتروني" if lang == "ar" else ("email" if lang == "en" else "email")
            bot.send_message(chat_id, t("invalid_format", chat_id).format(type=type_name))
        return
    
    # === حالة البحث برقم الهاتف ===
    if state.get("state") == "waiting_phone":
        phone = text.strip()
        if re.match(r"^\+?\d{10,15}$", phone):
            bot.send_chat_action(chat_id, 'typing')
            bot.send_message(chat_id, "🔍 جاري البحث عن رقم الهاتف...")
            
            # استخدام session_key إذا متوفر للبحث الأقوى
            user_session = user_sessions.get(chat_id, {})
            sk = user_session.get("session_key")
            result = search_by_phone_tiktok(phone, session_key=sk)
            if result:
                # تجميع المعلومات المتاحة
                info_parts = []
                if result.get("uniqueId"):
                    info_parts.append(f"├ اليوزر: @{result['uniqueId']}")
                if result.get("nickname"):
                    info_parts.append(f"├ الاسم: {result['nickname']}")
                if result.get("masked_phone"):
                    info_parts.append(f"├ الرقم: {result['masked_phone']}")
                if result.get("exists"):
                    info_parts.append(f"├ الحالة: حساب موجود ✅")
                if result.get("uid"):
                    info_parts.append(f"├ المعرف: {result['uid']}")
                
                if not info_parts:
                    info_parts.append("├ الحالة: حساب موجود ✅")
                
                info_text = "\n".join(info_parts)
                bot.send_message(chat_id, t("search_found", chat_id).format(info=info_text) + "\n\nTikWahmbot", parse_mode="HTML")
            else:
                lang = user_lang.get(chat_id, "ar")
                type_name = "رقم الهاتف" if lang == "ar" else ("phone number" if lang == "en" else "номеру телефона")
                bot.send_message(chat_id, t("search_not_found", chat_id).format(type=type_name) + "\n\nTikWahmbot")
            
            del user_states[chat_id]
        else:
            lang = user_lang.get(chat_id, "ar")
            type_name = "رقم هاتف" if lang == "ar" else ("phone number" if lang == "en" else "номер телефона")
            bot.send_message(chat_id, t("invalid_format", chat_id).format(type=type_name))
        return
    
    # === تحميل فيديو تيك توك ===
    is_video_link = ("tiktok.com/" in text and "/video/" in text) or "vm.tiktok.com/" in text or "vt.tiktok.com/" in text
    if is_video_link:
        bot.send_chat_action(chat_id, 'typing')
        bot.reply_to(message, "⬇️ جاري تحميل الفيديو... ⏳")
        
        video_result = download_tiktok_video(text.strip())
        if video_result and video_result.get("play_url"):
            play_url = video_result["play_url"]
            title = video_result.get("title", "")
            author = video_result.get("author", "")
            duration = video_result.get("duration", 0)
            
            caption = f"🎬 TikWahm - تحميل فيديو\n"
            if author:
                caption += f"├ المستخدم: @{author}\n"
            if title:
                caption += f"├ الوصف: {title[:100]}\n"
            if duration:
                caption += f"└ المدة: {duration} ثانية\n"
            caption += f"\n🤖 @TikWahmbot"
            
            try:
                bot.send_video(chat_id, play_url, caption=caption)
            except:
                try:
                    bot.send_message(chat_id, f"⬇️ رابط التحميل:\n{play_url}\n\n{caption}")
                except:
                    bot.send_message(chat_id, f"⬇️ رابط التحميل:\n{play_url}")
        else:
            bot.send_message(chat_id, "❌ فشل تحميل الفيديو. تأكد من صحة الرابط وحاول مرة أخرى.\n\nTikWahmbot")
        return
    
    # === البحث عن حساب تيك توك ===
    username = text.replace("@", "")
    if "tiktok.com/" in username:
        username = username.split("tiktok.com/")[1].split("/")[0].split("?")[0].replace("@", "")
    
    if not username or len(username) < 2:
        bot.reply_to(message, "❌ يرجى إرسال اسم مستخدم صحيح.\n\nTikWahmbot")
        return
    
    bot.send_chat_action(chat_id, 'typing')
    bot.reply_to(message, f"🔍 جاري البحث عن {username}...\nقد يستغرق بضع ثوانٍ ⏳")
    
    user_data = get_tikwm_user(username)
    if not user_data:
        bot.send_message(chat_id, f"❌ لم يتم العثور على حساب {username}\n\nTikWahmbot")
        return
    
    user = user_data.get("user", {})
    stats = user_data.get("stats", {})
    sec_uid = user.get("secUid", "")
    
    countik_info = get_countik_userinfo(sec_uid) if sec_uid else None
    analyze_data = get_countik_analyze(sec_uid) if sec_uid else None
    
    user_id = user.get("id", "غير متوفر")
    unique_id = user.get("uniqueId", "غير متوفر")
    nickname = user.get("nickname", "غير متوفر")
    signature = user.get("signature", "") or "لا يوجد"
    verified = user.get("verified", False)
    private_account = user.get("privateAccount", False)
    secret = user.get("secret", False)
    is_under_18 = user.get("isUnderAge18", False)
    open_favorite = user.get("openFavorite", False)
    is_ad_virtual = user.get("isADVirtual", False)
    ftc = user.get("ftc", False)
    create_time = user.get("createTime", 0)
    
    followers = stats.get("followerCount", 0)
    following = stats.get("followingCount", 0)
    likes = stats.get("heartCount", 0)
    videos_count = stats.get("videoCount", 0)
    friends = stats.get("friendCount", 0)
    
    language = "غير متوفر"
    if countik_info:
        lang_code = countik_info.get("language", "")
        if lang_code:
            language = LANGUAGE_MAP.get(lang_code, lang_code)
    
    region = "غير متوفر"
    video_id_for_region = None
    if analyze_data and analyze_data.get("videos"):
        video_id_for_region = analyze_data["videos"][0].get("id")
    if video_id_for_region:
        region_code = get_region_from_videos(username, video_id_for_region)
        if region_code:
            region = COUNTRY_MAP.get(region_code.upper(), region_code)
    
    story_status = user.get("UserStoryStatus", 0)
    has_story = story_status > 0
    
    caption_text = (
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 TikWahm - معلومات تيك توك\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"• معلومات الحساب\n"
        f"├ اسم المستخدم: {unique_id}\n"
        f"├ المعرف: {user_id}\n"
        f"├ الاسم: {nickname}\n"
        f"├ المتابعين: {format_number(followers)}\n"
        f"├ يتابع: {format_number(following)}\n"
        f"├ الأصدقاء: {format_number(friends)}\n"
        f"├ الإعجابات: {format_number(likes)}\n"
        f"├ الفيديوهات: {format_number(videos_count)}\n"
        f"├ تاريخ الإنشاء: {timestamp_to_date(create_time)}\n"
        f"├ عمر الحساب: {get_account_age(create_time) if create_time else 'غير متوفر'}\n"
        f"├ 🌍 الدولة: {region}\n"
        f"├ 🗣 اللغة: {language}\n"
        f"├ حساب موثق: {'نعم ✅' if verified else 'لا ❌'}\n"
        f"├ حساب خاص: {'نعم 🔒' if private_account else 'لا ❌'}\n"
        f"├ حساب سري: {'نعم 🔒' if secret else 'لا ❌'}\n"
        f"├ المفضلة مفتوحة: {'نعم ✅' if open_favorite else 'لا ❌'}\n"
        f"├ أقل من 18 سنة: {'نعم ⚠️' if is_under_18 else 'لا ❌'}\n"
        f"├ متوافق FTC: {'نعم ✅' if ftc else 'لا ❌'}\n"
        f"└ حساب إعلانات وهمي: {'نعم ⚠️' if is_ad_virtual else 'لا ❌'}\n\n"
        f"• البايو: {signature}\n"
    )
    
    url_in_bio = re.findall(r'https?://[^\s]+', signature)
    if url_in_bio:
        caption_text += f"• الرابط في البايو: {url_in_bio[0]}\n"
    
    caption_text += f"\n🔗 https://www.tiktok.com/@{unique_id}\n"
    caption_text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    caption_text += f"🤖 @TikWahmbot"
    
    # الأزرار
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👥 عرض المتابعين 💎", callback_data=f"pay_followers_{unique_id}"),
        types.InlineKeyboardButton("👤 عرض المتابَعين 💎", callback_data=f"pay_following_{unique_id}"),
    )
    markup.add(
        types.InlineKeyboardButton("📖 تحميل الستوري 🆓", callback_data=f"story_{unique_id}"),
    )
    markup.add(
        types.InlineKeyboardButton("📊 كشف مستوى الحساب 🆓", callback_data=f"level_{unique_id}"),
        types.InlineKeyboardButton("🔗 كشف نوع الربط 💎", callback_data=f"pay_binding_{unique_id}"),
    )
    
    # إرسال
    avatar_url = user.get("avatarLarger") or user.get("avatarMedium") or user.get("avatarThumb")
    
    try:
        if avatar_url:
            if len(caption_text) > 1024:
                short_caption = (
                    f"📱 معلومات @{unique_id}\n"
                    f"├ الاسم: {nickname}\n"
                    f"├ المتابعين: {format_number(followers)}\n"
                    f"├ الإعجابات: {format_number(likes)}\n"
                    f"├ 🌍 الدولة: {region}\n"
                    f"└ 🗣 اللغة: {language}\n"
                    f"\n🤖 @TikWahmbot"
                )
                bot.send_photo(chat_id, avatar_url, caption=short_caption)
                bot.send_message(chat_id, caption_text)
            else:
                bot.send_photo(chat_id, avatar_url, caption=caption_text)
        else:
            bot.send_message(chat_id, caption_text)
    except Exception as e:
        print(f"Error: {e}")
        try:
            bot.send_message(chat_id, caption_text)
        except:
            bot.send_message(chat_id, f"معلومات @{unique_id}\nالمتابعين: {format_number(followers)}\n\nTikWahmbot")
    
    # أزرار
    try:
        bot.send_message(chat_id, "⬇️ خيارات إضافية:", reply_markup=markup)
    except:
        pass

print("✅ TikWahm Bot started successfully!")
bot.polling(none_stop=True)
