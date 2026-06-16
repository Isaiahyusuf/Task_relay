"""
Internationalization (i18n) module for TaskRelay Bot.
Supports English (en), Pashto/Afghan (ps), and Burmese (my).
"""

LANGUAGES: dict[str, str] = {
    "en": "🇬🇧 English",
    "ps": "🇦🇫 پښتو",
    "my": "🇲🇲 မြန်မာ",
}

DEFAULT_LANG = "en"

# Map: English button text → {lang_code: translated_text}
BUTTONS: dict[str, dict[str, str]] = {
    # --- Common ---
    "Language":                   {"en": "🌐 Language",                  "ps": "🌐 ژبه",                           "my": "🌐 ဘာသာစကား"},
    "Help":                       {"en": "Help",                          "ps": "مرسته",                            "my": "အကူအညီ"},
    "About":                      {"en": "About",                         "ps": "معلومات",                          "my": "အကြောင်း"},
    "Delete My Account":          {"en": "Delete My Account",             "ps": "زما حساب ړنګ کړئ",                 "my": "ကျွန်ုပ်အကောင့်ဖျက်ရန်"},
    "Main Menu":                  {"en": "Main Menu",                     "ps": "اصلي مینو",                        "my": "ပင်မမီနူး"},
    "Switch Role":                {"en": "Switch Role",                   "ps": "رول بدل کړئ",                      "my": "အခန်းကဏ္ဍပြောင်းရန်"},

    # --- Jobs (shared across roles) ---
    "New Job":                    {"en": "New Job",                       "ps": "کار نوی",                          "my": "အလုပ်အသစ်"},
    "Job History":                {"en": "Job History",                   "ps": "د کار تاریخ",                      "my": "အလုပ်မှတ်တမ်း"},
    "Archive Jobs":               {"en": "Archive Jobs",                  "ps": "کارونه آرشیف کول",                 "my": "အလုပ်များသိမ်းဆည်းရန်"},
    "View Archived":              {"en": "View Archived",                 "ps": "آرشیف شوي وګورئ",                  "my": "သိမ်းဆည်းထားသောများကြည့်ရန်"},
    "View Jobs":                  {"en": "View Jobs",                     "ps": "کارونه وګورئ",                     "my": "အလုပ်များကြည့်ရန်"},
    "Create Job":                 {"en": "Create Job",                    "ps": "کار جوړ کړئ",                      "my": "အလုပ်ဖန်တီးရန်"},

    # --- Supervisor jobs ---
    "My Jobs":                    {"en": "My Jobs",                       "ps": "زما کارونه",                       "my": "ကျွန်ုပ်အလုပ်များ"},
    "Pending Jobs":               {"en": "Pending Jobs",                  "ps": "تمه لرونکي کارونه",                "my": "စောင့်ဆိုင်းနေသောအလုပ်များ"},
    "Active Jobs":                {"en": "Active Jobs",                   "ps": "فعال کارونه",                      "my": "လက်ရှိအလုပ်များ"},
    "Submitted Jobs":             {"en": "Submitted Jobs",                "ps": "سپارل شوي کارونه",                 "my": "တင်သွင်းပြီးသောအလုပ်များ"},
    "View Availability":          {"en": "View Availability",             "ps": "شتون وګورئ",                       "my": "ရနိုင်မှုကြည့်ရန်"},

    # --- Subcontractor jobs ---
    "Available Jobs":             {"en": "Available Jobs",                "ps": "موجوده کارونه",                    "my": "ရနိုင်သောအလုပ်များ"},
    "My Active Jobs":             {"en": "My Active Jobs",                "ps": "زما فعال کارونه",                  "my": "ကျွန်ုပ်လက်ရှိအလုပ်များ"},
    "Start Work":                 {"en": "Start Work",                    "ps": "کار پیل کړئ",                      "my": "အလုပ်စတင်ရန်"},
    "Submit Job":                 {"en": "Submit Job",                    "ps": "کار سپاره کړئ",                    "my": "အလုပ်တင်သွင်းရန်"},

    # --- Availability ---
    "Available":                  {"en": "Available",                     "ps": "شتون لري",                         "my": "ရနိုင်သည်"},
    "Busy":                       {"en": "Busy",                          "ps": "بوخت",                             "my": "ရှုပ်နေသည်"},
    "Away":                       {"en": "Away",                          "ps": "لیرې",                             "my": "ထွက်သွားသည်"},
    "My Availability":            {"en": "My Availability",               "ps": "زما شتون",                         "my": "ကျွန်ုပ်ရနိုင်မှု"},
    "Report Unavailability":      {"en": "Report Unavailability",         "ps": "د نه شتون راپور",                  "my": "မရနိုင်ကြောင်းတင်ပြရန်"},
    "Request Availability":       {"en": "Request Availability",          "ps": "د شتون غوښتنه",                    "my": "ရနိုင်မှုတောင်းရန်"},
    "Weekly Availability":        {"en": "Weekly Availability",           "ps": "اونیز شتون",                       "my": "အပတ်ရနိုင်မှု"},

    # --- Safety ---
    "Site Safety Checklist":      {"en": "Site Safety Checklist",         "ps": "د سایټ خوندیتوب چک لیست",         "my": "နေရာဘေးကင်းရေးစစ်ဆေးမှု"},
    "Upload Site Photos":         {"en": "Upload Site Photos",            "ps": "د سایټ عکسونه اپلوډ کړئ",         "my": "နေရာဓာတ်ပုံများတင်ရန်"},
    "My Submissions":             {"en": "My Submissions",                "ps": "زما سپارښتنې",                     "my": "ကျွန်ုပ်တင်သွင်းမှုများ"},
    "Safety Submissions":         {"en": "Safety Submissions",            "ps": "د خوندیتوب سپارښتنې",              "my": "ဘေးကင်းရေးတင်သွင်းမှုများ"},
    "Filter Safety Submissions":  {"en": "Filter Safety Submissions",     "ps": "د خوندیتوب سپارښتنې فلټر کول",    "my": "ဘေးကင်းရေးတင်သွင်းမှုများစစ်ထုတ်ရန်"},
    "Export Safety CSV":          {"en": "Export Safety CSV",             "ps": "د خوندیتوب CSV صادرول",            "my": "ဘေးကင်းရေး CSV ထုတ်ရန်"},
    "Request Safety Checklist":   {"en": "Request Safety Checklist",      "ps": "د خوندیتوب چک لیست غوښتنه کول",   "my": "ဘေးကင်းရေးစစ်ဆေးမှုတောင်းရန်"},
    "Contact Supervisor":         {"en": "Contact Supervisor",            "ps": "سرپرست سره اړیکه ونیسئ",           "my": "ကြီးကြပ်သူနှင့်ဆက်သွယ်ရန်"},

    # --- Messaging ---
    "Send Message":               {"en": "Send Message",                  "ps": "پیغام واستوئ",                     "my": "မက်ဆေ့ပို့ရန်"},

    # --- Access codes ---
    "Manage Access Codes":        {"en": "Manage Access Codes",           "ps": "د لاسرسي کوډونو مدیریت",           "my": "ဝင်ရောက်ကုတ်စီမံရန်"},
    "Create Access Code":         {"en": "Create Access Code",            "ps": "د لاسرسي کوډ جوړ کړئ",            "my": "ဝင်ရောက်ကုတ်ဖန်တီးရန်"},
    "All Access Codes":           {"en": "All Access Codes",              "ps": "ټول لاسرسي کوډونه",                "my": "ဝင်ရောက်ကုတ်အားလုံး"},
    "Create Admin Code":          {"en": "Create Admin Code",             "ps": "د مدیر کوډ جوړ کړئ",               "my": "မန်နေဂျာကုတ်ဖန်တီးရန်"},
    "Create Manager Code":        {"en": "Create Manager Code",           "ps": "د مدیر کوډ جوړ کړئ",               "my": "မန်နေဂျာကုတ်ဖန်တီးရန်"},
    "Create Supervisor Code":     {"en": "Create Supervisor Code",        "ps": "د سرپرست کوډ جوړ کړئ",             "my": "ကြီးကြပ်သူကုတ်ဖန်တီးရန်"},
    "Create Subcontractor Code":  {"en": "Create Subcontractor Code",     "ps": "د مقاول کوډ جوړ کړئ",              "my": "အကြွင်းကုတ်ဖန်တီးရန်"},

    # --- User management ---
    "Manage Users":               {"en": "Manage Users",                  "ps": "د کاروونکو مدیریت",                "my": "အသုံးပြုသူများစီမံရန်"},
    "All Users":                  {"en": "All Users",                     "ps": "ټول کاروونکي",                     "my": "အသုံးပြုသူအားလုံး"},
    "View Admins":                {"en": "View Admins",                   "ps": "مدیران وګورئ",                     "my": "မန်နေဂျာများကြည့်ရန်"},
    "View Managers":              {"en": "View Managers",                 "ps": "مدیران وګورئ",                     "my": "မန်နေဂျာများကြည့်ရန်"},
    "View Supervisors":           {"en": "View Supervisors",              "ps": "سرپرستان وګورئ",                   "my": "ကြီးကြပ်သူများကြည့်ရန်"},
    "View Subcontractors":        {"en": "View Subcontractors",           "ps": "مقاولین وګورئ",                    "my": "အကြွင်းများကြည့်ရန်"},

    # --- Teams / Regions / Roles ---
    "View By Teams":              {"en": "View By Teams",                 "ps": "د ټولو لخوا وګورئ",                "my": "အဖွဲ့အလိုက်ကြည့်ရန်"},
    "View Regions":               {"en": "View Regions",                  "ps": "سیمې وګورئ",                       "my": "ဒေသများကြည့်ရန်"},
    "Manage Roles":               {"en": "Manage Roles",                  "ps": "رولونه مدیریت کول",                "my": "အခန်းကဏ္ဍများစီမံရန်"},
    "Manage Regions":             {"en": "Manage Regions",                "ps": "سیمې مدیریت کول",                  "my": "ဒေသများစီမံရန်"},
    "Manage Teams":               {"en": "Manage Teams",                  "ps": "ټولونه مدیریت کول",                "my": "အဖွဲ့များစီမံရန်"},

    # --- Role-switch return buttons ---
    "Return to Super Admin":      {"en": "Return to Super Admin",         "ps": "عمومي مدیر ته ستنیدل",             "my": "ဂျနရယ်မန်နေဂျာသို့ပြန်သွားရန်"},
    "Return to General Manager":  {"en": "Return to General Manager",     "ps": "عمومي مدیر ته ستنیدل",             "my": "ဂျနရယ်မန်နေဂျာသို့ပြန်သွားရန်"},
}

# Build reverse lookup: any translated text → canonical English key
_REVERSE: dict[str, str] = {}
for _en_key, _translations in BUTTONS.items():
    for _lang, _text in _translations.items():
        _REVERSE[_text] = _en_key


def variants(english_key: str) -> frozenset[str]:
    """Return all language variants of an English button key."""
    if english_key not in BUTTONS:
        return frozenset({english_key})
    return frozenset(BUTTONS[english_key].values())


def all_menu_variants() -> frozenset[str]:
    """Return every translated text across all buttons and all languages."""
    result: set[str] = set()
    for translations in BUTTONS.values():
        result.update(translations.values())
    return frozenset(result)


def get_text(english_key: str, lang: str = DEFAULT_LANG) -> str:
    """Return the translated text for a button key in the given language."""
    if english_key not in BUTTONS:
        return english_key
    return BUTTONS[english_key].get(lang, BUTTONS[english_key].get("en", english_key))


def normalize(text: str) -> str:
    """Normalize any translated button text back to its English canonical form."""
    return _REVERSE.get(text, text)


# ── Message string translations ─────────────────────────────────────────────

MESSAGES: dict[str, dict[str, str]] = {
    "welcome_back": {
        "en": "Welcome back, {name}!\n\nYou are logged in as: *{role}*\n\nUse the menu below to navigate:",
        "ps": "ښه راغلاست، {name}!\n\nتاسو د *{role}* په توګه ننوتلي یاست\n\nد ناوي کارولو لپاره لاندې مینو وکاروئ:",
        "my": "ကြိုဆိုပါသည်၊ {name}!\n\nသင် *{role}* အနေဖြင့် ဝင်ရောက်နေသည်\n\nအောက်ပါမီနူးကိုအသုံးပြုပါ:",
    },
    "language_prompt": {
        "en": "*🌐 Language Settings*\n\nSelect your preferred language:",
        "ps": "*🌐 د ژبې ترتیبات*\n\nخپله غوره ژبه وټاکئ:",
        "my": "*🌐 ဘာသာစကားဆက်တင်*\n\nသင်နှစ်သက်သောဘာသာစကားရွေးချယ်ပါ:",
    },
    "language_set_en": {
        "en": "✅ Language set to English.",
        "ps": "✅ Language set to English.",
        "my": "✅ Language set to English.",
    },
    "language_set_ps": {
        "en": "✅ ژبه پښتو ته بدله شوه.",
        "ps": "✅ ژبه پښتو ته بدله شوه.",
        "my": "✅ ژبه پښتو ته بدله شوه.",
    },
    "language_set_my": {
        "en": "✅ ဘာသာစကား မြန်မာသို့ပြောင်းလဲပြီး။",
        "ps": "✅ ဘာသာစကား မြန်မာသို့ပြောင်းလဲပြီး။",
        "my": "✅ ဘာသာစကား မြန်မာသို့ပြောင်းလဲပြီး။",
    },

    # ── Notifications TO subcontractors (delivered in recipient's language) ──

    "broadcast_header": {
        "en": "📢 *Message from {sender}*\n\n",
        "ps": "📢 *{sender} لخوا پیغام*\n\n",
        "my": "📢 *{sender} ထံမှ မက်ဆေ့*\n\n",
    },
    "new_job_notification": {
        "en": (
            "🔔 *New Job Available*\n\n"
            "Job #{job_id}: {title}\n"
            "Location: {address}\n"
            "Price: {price}{deadline}\n\n"
            "Check 'Available Jobs' to accept this job!"
        ),
        "ps": (
            "🔔 *نوی کار موجود دی*\n\n"
            "کار #{job_id}: {title}\n"
            "ځای: {address}\n"
            "بیه: {price}{deadline}\n\n"
            "'موجوده کارونه' وګورئ ترڅو دا کار ومنئ!"
        ),
        "my": (
            "🔔 *အလုပ်အသစ်ရနိုင်သည်*\n\n"
            "အလုပ် #{job_id}: {title}\n"
            "နေရာ: {address}\n"
            "လစာ: {price}{deadline}\n\n"
            "'ရနိုင်သောအလုပ်များ' စစ်ဆေးပြီး ဤအလုပ်ကိုလက်ခံပါ!"
        ),
    },
    "quote_accepted_notification": {
        "en": (
            "🎉 *Your Quote Was Accepted!*\n\n"
            "Job #{job_id}: {title}\n"
            "Your Quote: *{amount}*\n\n"
            "Congratulations! The job is now assigned to you.\n"
            "Check 'My Active Jobs' to start working on it."
        ),
        "ps": (
            "🎉 *ستاسو نرخ نامه ومنل شوه!*\n\n"
            "کار #{job_id}: {title}\n"
            "ستاسو نرخ: *{amount}*\n\n"
            "مبارک شه! دا کار اوس تاسو ته ورکول شوی دی.\n"
            "'زما فعال کارونه' وګورئ ترڅو پرې کار پیل کړئ."
        ),
        "my": (
            "🎉 *သင်၏ကိုးကားမှုလက်ခံပြီး!*\n\n"
            "အလုပ် #{job_id}: {title}\n"
            "သင်၏ကိုးကားမှု: *{amount}*\n\n"
            "ဂုဏ်ယူပါသည်! ဤအလုပ်ကိုယခုသင့်ထံပေးအပ်ပြီး။\n"
            "'ကျွန်ုပ်လက်ရှိအလုပ်များ' စစ်ဆေးပြီးစတင်ပါ။"
        ),
    },
    "quote_declined_notification": {
        "en": (
            "❌ *Your Quote Was Declined*\n\n"
            "Job #{job_id}: {title}\n"
            "Amount: *{amount}*\n\n"
            "*Reason:* {reason}\n\n"
            "You can submit a new quote for this job if you wish."
        ),
        "ps": (
            "❌ *ستاسو نرخ نامه رد شوه*\n\n"
            "کار #{job_id}: {title}\n"
            "مقدار: *{amount}*\n\n"
            "*لامل:* {reason}\n\n"
            "که غواړئ کولی شئ د دې کار لپاره نوې نرخ نامه وسپارئ."
        ),
        "my": (
            "❌ *သင်၏ကိုးကားမှုငြင်းပယ်ခံရပြီး*\n\n"
            "အလုပ် #{job_id}: {title}\n"
            "ပမာဏ: *{amount}*\n\n"
            "*အကြောင်းရင်း:* {reason}\n\n"
            "လိုပါက ဤအလုပ်အတွက် ကိုးကားမှုအသစ်တင်သွင်းနိုင်သည်။"
        ),
    },
    "availability_request": {
        "en": (
            "*Availability Request*\n\n"
            "Your manager requested your weekly availability.\n"
            "Tap day buttons to toggle your availability, then tap Save.\n\n"
            "Monday ({mon})\n"
            "Tuesday ({tue})\n"
            "Wednesday ({wed})\n"
            "Thursday ({thu})\n"
            "Friday ({fri})"
        ),
        "ps": (
            "*د شتون غوښتنه*\n\n"
            "ستاسو مدیر ستاسو اونیز شتون غواړي.\n"
            "د خپل شتون لپاره د ورځې تڼۍ فشار ورکړئ، بیا خوندي کړئ.\n\n"
            "دوشنبه ({mon})\n"
            "سه شنبه ({tue})\n"
            "چهارشنبه ({wed})\n"
            "پنجشنبه ({thu})\n"
            "جمعه ({fri})"
        ),
        "my": (
            "*ရနိုင်မှုတောင်းဆိုမှု*\n\n"
            "သင်၏မန်နေဂျာသည် သင်၏အပတ်ရနိုင်မှုကိုတောင်းသည်။\n"
            "ရနိုင်မှုပြောင်းရန် နေ့ခလုတ်များနှိပ်ပြီး သိမ်းဆည်းပါ။\n\n"
            "တနင်္လာ ({mon})\n"
            "အင်္ဂါ ({tue})\n"
            "ဗုဒ္ဓဟူး ({wed})\n"
            "ကြာသပတေး ({thu})\n"
            "သောကြာ ({fri})"
        ),
    },
    "safety_checklist_request": {
        "en": (
            "🦺 Site Safety Checklist requested by {requester}.\n"
            "Please open 'Site Safety Checklist' and complete it before starting work.\n"
            "Note: {note}"
        ),
        "ps": (
            "🦺 د {requester} لخوا د سایټ خوندیتوب چک لیست غوښتنه شوې.\n"
            "مهرباني وکړئ 'د سایټ خوندیتوب چک لیست' پرانیزئ او د کار پیل کولو دمخه یې ډک کړئ.\n"
            "یادداشت: {note}"
        ),
        "my": (
            "🦺 {requester} မှ နေရာဘေးကင်းရေးစစ်ဆေးမှုတောင်းဆိုပြီး။\n"
            "အလုပ်မစမီ 'နေရာဘေးကင်းရေးစစ်ဆေးမှု' ဖွင့်ပြီးဖြည့်ပါ။\n"
            "မှတ်ချက်: {note}"
        ),
    },

    # ── Notifications TO supervisors/admins (delivered in recipient's language) ──

    "job_accepted_by_sub": {
        "en": "✅ *Job Accepted*\n\nJob #{job_id} ({title}) has been accepted by *{sub_name}*.\nCompany: *{company}*",
        "ps": "✅ *کار ومنل شو*\n\nکار #{job_id} ({title}) د *{sub_name}* لخوا منل شوی دی.\nشرکت: *{company}*",
        "my": "✅ *အလုပ်လက်ခံပြီး*\n\nအလုပ် #{job_id} ({title}) ကို *{sub_name}* လက်ခံသည်။\nကုမ္ပဏီ: *{company}*",
    },
    "job_marked_done_by_sub": {
        "en": (
            "✅ *Job Marked Done*\n\n"
            "Job #{job_id} ({title}) has been marked as done by *{sub_name}*.\n\n"
            "Please investigate and mark as completed if satisfied."
        ),
        "ps": (
            "✅ *کار بشپړ نښه شو*\n\n"
            "کار #{job_id} ({title}) د *{sub_name}* لخوا بشپړ نښه شوی دی.\n\n"
            "مهرباني وکړئ وڅیړئ او که راضي یاست بشپړ نښه یې کړئ."
        ),
        "my": (
            "✅ *အလုပ်ပြီးစီးကြောင်းမှတ်သားပြီး*\n\n"
            "အလုပ် #{job_id} ({title}) ကို *{sub_name}* ပြီးစီးကြောင်းမှတ်သားသည်။\n\n"
            "ကျေးဇူးပြု၍စစ်ဆေးပြီးကျေနပ်ပါကပြီးစီးကြောင်းမှတ်သားပါ။"
        ),
    },
    "job_submitted_by_sub": {
        "en": (
            "📋 *Job Submitted for Review*\n\n"
            "Job #{job_id}: {title}\n"
            "Submitted by: *{sub_name}*{company}{notes}\n\n"
            "📎 Photos ({photo_count}) attached below.\n"
            "Please review and mark as completed if satisfied."
        ),
        "ps": (
            "📋 *کار د بیاکتنې لپاره سپارل شو*\n\n"
            "کار #{job_id}: {title}\n"
            "سپارونکی: *{sub_name}*{company}{notes}\n\n"
            "📎 عکسونه ({photo_count}) لاندې ضمیمه دي.\n"
            "مهرباني وکړئ وڅیړئ او که راضي یاست بشپړ نښه یې کړئ."
        ),
        "my": (
            "📋 *အလုပ်သုံးသပ်ရန်တင်သွင်းပြီး*\n\n"
            "အလုပ် #{job_id}: {title}\n"
            "တင်သွင်းသူ: *{sub_name}*{company}{notes}\n\n"
            "📎 ဓာတ်ပုံများ ({photo_count}) အောက်တွင်ပူးတွဲပြီး။\n"
            "ကျေးဇူးပြု၍သုံးသပ်ပြီးကျေနပ်ပါကပြီးစီးကြောင်းမှတ်သားပါ။"
        ),
    },
    "new_quote_received": {
        "en": (
            "💬 *New Quote Received!*\n\n"
            "Job #{job_id}: {title}\n"
            "From: *{sub_name}*\n"
            "Quote Amount: *{amount}*{notes}\n\n"
            "Use 'View Quotes' to review all quotes for this job."
        ),
        "ps": (
            "💬 *نوې نرخ نامه راغله!*\n\n"
            "کار #{job_id}: {title}\n"
            "لخوا: *{sub_name}*\n"
            "نرخ: *{amount}*{notes}\n\n"
            "د دې کار ټولې نرخ نامې د 'نرخ نامې وګورئ' له لارې وڅیړئ."
        ),
        "my": (
            "💬 *ကိုးကားမှုအသစ်ရောက်ရှိပြီး!*\n\n"
            "အလုပ် #{job_id}: {title}\n"
            "မှ: *{sub_name}*\n"
            "ကိုးကားပမာဏ: *{amount}*{notes}\n\n"
            "ဤအလုပ်၏ကိုးကားမှုများ 'ကိုးကားမှုများကြည့်ရန်' ကိုသုံးပါ။"
        ),
    },
    "unavailability_job_specific": {
        "en": (
            "🔴 *Unavailability Notice*\n\n"
            "*{sub_name}* has reported unavailability for:\n\n"
            "Job #{job_id}: {title}\n"
            "Reason: {reason}{dates}"
        ),
        "ps": (
            "🔴 *د نه شتون خبرتیا*\n\n"
            "*{sub_name}* د لاندې کار لپاره د نه شتون راپور ورکړی دی:\n\n"
            "کار #{job_id}: {title}\n"
            "لامل: {reason}{dates}"
        ),
        "my": (
            "🔴 *မရနိုင်ကြောင်းသတိပေးချက်*\n\n"
            "*{sub_name}* ဤအလုပ်အတွက် မရနိုင်ကြောင်းတင်ပြသည်:\n\n"
            "အလုပ် #{job_id}: {title}\n"
            "အကြောင်းရင်း: {reason}{dates}"
        ),
    },
    "unavailability_general": {
        "en": (
            "🔴 *Unavailability Notice*\n\n"
            "*{sub_name}* has reported {scope} unavailability.\n\n"
            "{job_info}"
            "Reason: {reason}{dates}"
        ),
        "ps": (
            "🔴 *د نه شتون خبرتیا*\n\n"
            "*{sub_name}* {scope} نه شتون راپور ورکړی دی.\n\n"
            "{job_info}"
            "لامل: {reason}{dates}"
        ),
        "my": (
            "🔴 *မရနိုင်ကြောင်းသတိပေးချက်*\n\n"
            "*{sub_name}* {scope} မရနိုင်ကြောင်းတင်ပြသည်။\n\n"
            "{job_info}"
            "အကြောင်းရင်း: {reason}{dates}"
        ),
    },
    "unavailability_scope_job": {
        "en": "job-specific",
        "ps": "د ځانګړي کار",
        "my": "သတ်မှတ်အလုပ်",
    },
    "unavailability_scope_general": {
        "en": "general",
        "ps": "عمومي",
        "my": "ယေဘုယျ",
    },
    "availability_update": {
        "en": "📅 *Availability Update*\n\n*{sub_name}* has submitted their weekly availability.\n\nAvailable days: {days}",
        "ps": "📅 *د شتون تازه معلومات*\n\n*{sub_name}* خپل اونیز شتون سپارلی دی.\n\nموجود ورځې: {days}",
        "my": "📅 *ရနိုင်မှုအပ်ဒိတ်*\n\n*{sub_name}* ၏အပတ်ရနိုင်မှုတင်သွင်းပြီး。\n\nရနိုင်သောနေ့များ: {days}",
    },
    "message_acknowledged": {
        "en": "✅ *Message Acknowledged*\n\n*{responder}* has acknowledged your message:\n\n_{preview}_",
        "ps": "✅ *پیغام تایید شو*\n\n*{responder}* ستاسو پیغام تایید کړ:\n\n_{preview}_",
        "my": "✅ *မက်ဆေ့အတည်ပြုပြီး*\n\n*{responder}* သင်၏မက်ဆေ့ကိုအတည်ပြုသည်:\n\n_{preview}_",
    },
    "reply_received": {
        "en": "💬 *Reply Received*\n\n*{responder}* replied to your message:\n\n*Original:*\n_{preview}_\n\n*Reply:*\n{reply}",
        "ps": "💬 *ځواب راغی*\n\n*{responder}* ستاسو پیغام ته ځواب ورکړ:\n\n*اصلي:*\n_{preview}_\n\n*ځواب:*\n{reply}",
        "my": "💬 *အဖြေရောက်ရှိပြီး*\n\n*{responder}* သင်၏မက်ဆေ့ကိုဖြေသည်:\n\n*မူရင်း:*\n_{preview}_\n\n*အဖြေ:*\n{reply}",
    },
    "revision_requested": {
        "en": "🔄 *Revision Requested*\n\nJob #{job_id}: {title}\n\n*Supervisor Feedback:*\n{reason}\n\nPlease address the issues and resubmit your work.",
        "ps": "🔄 *د بیاکتنې غوښتنه*\n\nکار #{job_id}: {title}\n\n*د سرپرست نظر:*\n{reason}\n\nمهرباني وکړئ ستونزې حل کړئ او بیا یې وسپارئ.",
        "my": "🔄 *ပြင်ဆင်မှုတောင်းဆိုမှု*\n\nအလုပ် #{job_id}: {title}\n\n*ကြီးကြပ်သူမှတ်ချက်:*\n{reason}\n\nကျေးဇူးပြု၍ပြဿနာများဖြေရှင်းပြီးပြန်တင်သွင်းပါ။",
    },
    "supervisor_feedback": {
        "en": "💬 *Supervisor Feedback*\n\n*{sup_name}* has responded to your unavailability notice:\n\n_{feedback}_",
        "ps": "💬 *د سرپرست نظر*\n\n*{sup_name}* ستاسو د نه شتون خبرتیا ته ځواب ورکړ:\n\n_{feedback}_",
        "my": "💬 *ကြီးကြပ်သူမှတ်ချက်*\n\n*{sup_name}* သင်၏မရနိုင်ကြောင်းသတိပေးချက်ကိုဖြေသည်:\n\n_{feedback}_",
    },
    "safety_checklist_submitted": {
        "en": (
            "🦺 New Site Safety Checklist submitted\n"
            "Checklist ID: {checklist_id}\n"
            "Subcontractor: {sub_name}\n"
            "Site: {site}\n"
            "Safe to proceed: {safe}"
        ),
        "ps": (
            "🦺 د سایټ خوندیتوب نوی چک لیست سپارل شو\n"
            "د چک لیست ID: {checklist_id}\n"
            "مقاول: {sub_name}\n"
            "سایټ: {site}\n"
            "د مخکې تګ لپاره خوندي: {safe}"
        ),
        "my": (
            "🦺 နေရာဘေးကင်းရေးစစ်ဆေးမှုအသစ်တင်သွင်းပြီး\n"
            "စစ်ဆေးမှု ID: {checklist_id}\n"
            "အကြွင်း: {sub_name}\n"
            "နေရာ: {site}\n"
            "ဆက်လက်ရန်ဘေးကင်း: {safe}"
        ),
    },
}


async def get_recipient_lang(telegram_id: int) -> str:
    """Look up a user's stored language preference. Returns 'en' as fallback."""
    try:
        from src.bot.database import async_session
        from src.bot.database.models import User
        from sqlalchemy import select
        async with async_session() as session:
            result = await session.execute(
                select(User.language).where(User.telegram_id == telegram_id)
            )
            lang = result.scalar_one_or_none()
            return lang if lang in LANGUAGES else "en"
    except Exception:
        return "en"


def msg(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    """Return a translated message string, with optional format kwargs."""
    translations = MESSAGES.get(key, {})
    text = translations.get(lang, translations.get("en", key))
    if kwargs:
        text = text.format(**kwargs)
    return text
