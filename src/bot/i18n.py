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
    "btn_accept": {
        "en": "✅ Accept",
        "ps": "✅ قبول",
        "my": "✅ လက်ခံသည်",
    },
    "btn_decline": {
        "en": "❌ Decline",
        "ps": "❌ رد",
        "my": "❌ ငြင်းပယ်သည်",
    },
    "btn_start_job": {
        "en": "▶️ Start Job",
        "ps": "▶️ کار پیل کول",
        "my": "▶️ အလုပ်စတင်မည်",
    },
    "btn_submit_job": {
        "en": "📤 Submit Job",
        "ps": "📤 کار وسپارئ",
        "my": "📤 အလုပ်တင်သွင်းမည်",
    },
    "btn_submit_quote": {
        "en": "💰 Submit Quote",
        "ps": "💰 وړاندیز وسپارئ",
        "my": "💰 ကိုးကားစာ တင်မည်",
    },
    "btn_back": {
        "en": "⬅️ Back",
        "ps": "⬅️ شاته",
        "my": "⬅️ နောက်သို့",
    },
    "btn_cancel": {
        "en": "✖️ Cancel",
        "ps": "✖️ لغوه",
        "my": "✖️ ဖျက်သိမ်းမည်",
    },
    "btn_skip": {
        "en": "⏭ Skip",
        "ps": "⏭ پریږدئ",
        "my": "⏭ ကျော်သည်",
    },
    "btn_skip_photos": {
        "en": "⏭ Skip Photos",
        "ps": "⏭ عکسونه پریږدئ",
        "my": "⏭ ဓာတ်ပုံများကျော်မည်",
    },
    "btn_no_deadline": {
        "en": "📅 No Deadline",
        "ps": "📅 هیڅ وروستۍ نیټه نشته",
        "my": "📅 နောက်ဆုံးရက်မရှိ",
    },
    "btn_quote_job": {
        "en": "💬 Quote Job",
        "ps": "💬 د وړاندیز کار",
        "my": "💬 ကိုးကားစာအလုပ်",
    },
    "btn_preset_price_job": {
        "en": "💵 Preset Price Job",
        "ps": "💵 ټاکلی بیه کار",
        "my": "💵 ကြိုတင်သတ်မှတ်ဈေးနှုန်းအလုပ်",
    },
    "btn_view_quotes": {
        "en": "📋 View Quotes",
        "ps": "📋 وړاندیزونه وګورئ",
        "my": "📋 ကိုးကားစာများကြည့်မည်",
    },
    "btn_cancel_job": {
        "en": "🚫 Cancel Job",
        "ps": "🚫 کار لغوه کول",
        "my": "🚫 အလုပ်ဖျက်သိမ်းမည်",
    },
    "btn_view_submission": {
        "en": "📂 View Submission",
        "ps": "📂 سپارل شوی وګورئ",
        "my": "📂 တင်သွင်းမှုကြည့်မည်",
    },
    "btn_mark_complete": {
        "en": "✅ Mark Complete",
        "ps": "✅ بشپړ شوی وښایاست",
        "my": "✅ ပြီးစီးကြောင်းမှတ်သားမည်",
    },
    "btn_not_satisfied": {
        "en": "🔄 Not Satisfied",
        "ps": "🔄 نه راضي",
        "my": "🔄 မကျေနပ်ပါ",
    },
    "btn_accept_quote": {
        "en": "✅ Accept This Quote",
        "ps": "✅ دا وړاندیز قبول کول",
        "my": "✅ ဤကိုးကားစာလက်ခံမည်",
    },
    "btn_decline_quote": {
        "en": "❌ Decline Quote",
        "ps": "❌ وړاندیز رد کول",
        "my": "❌ ကိုးကားစာငြင်းပယ်မည်",
    },
    "btn_back_to_quotes": {
        "en": "⬅️ Back to Quotes",
        "ps": "⬅️ وړاندیزونو ته شاته",
        "my": "⬅️ ကိုးကားစာများသို့ပြန်မည်",
    },
    "btn_previous": {
        "en": "⬅️ Previous",
        "ps": "⬅️ مخکینی",
        "my": "⬅️ ယခင်",
    },
    "btn_next": {
        "en": "Next ➡️",
        "ps": "بعدی ➡️",
        "my": "နောက်တစ်ခု ➡️",
    },
    "btn_decline_schedule": {
        "en": "🗓 Scheduling conflict",
        "ps": "🗓 د وخت تعارض",
        "my": "🗓 အချိန်ဇယားတိုက်ခိုက်မှု",
    },
    "btn_decline_location": {
        "en": "📍 Location too far",
        "ps": "📍 ځای ډیر لیرې دی",
        "my": "📍 တည်နေရာအလွန်ဝေးသည်",
    },
    "btn_decline_busy": {
        "en": "⏰ Too busy",
        "ps": "⏰ ډیر مصروف",
        "my": "⏰ အလွန်အမင်းအလုပ်ရှုပ်သည်",
    },
    "btn_decline_custom": {
        "en": "✏️ Custom reason",
        "ps": "✏️ ځانګړی لامل",
        "my": "✏️ ကိုယ်ပိုင်အကြောင်းပြချက်",
    },
    "btn_available_inline": {
        "en": "🟢 Available",
        "ps": "🟢 شتون",
        "my": "🟢 ရနိုင်သည်",
    },
    "btn_busy_inline": {
        "en": "🟡 Busy",
        "ps": "🟡 مصروف",
        "my": "🟡 အလုပ်ရှုပ်သည်",
    },
    "btn_away_inline": {
        "en": "🔴 Away",
        "ps": "🔴 غایب",
        "my": "🔴 ထွက်ခွာသည်",
    },
    "btn_monday": {
        "en": "Monday",
        "ps": "دوشنبه",
        "my": "တနင်္လာ",
    },
    "btn_tuesday": {
        "en": "Tuesday",
        "ps": "سه‌شنبه",
        "my": "အင်္ဂါ",
    },
    "btn_wednesday": {
        "en": "Wednesday",
        "ps": "چارشنبه",
        "my": "ဗုဒ္ဓဟူး",
    },
    "btn_thursday": {
        "en": "Thursday",
        "ps": "پنجشنبه",
        "my": "ကြာသပတေး",
    },
    "btn_friday": {
        "en": "Friday",
        "ps": "جمعه",
        "my": "သောကြာ",
    },
    "btn_save_availability": {
        "en": "Save Availability ✅",
        "ps": "شتون خوندي کول ✅",
        "my": "ရနိုင်မှုသိမ်းဆည်းမည် ✅",
    },
    "btn_add_notes": {
        "en": "Add Notes 📝",
        "ps": "یادداشتونه اضافه کول 📝",
        "my": "မှတ်စုထည့်မည် 📝",
    },
    "btn_general_unavailability": {
        "en": "📢 General Unavailability",
        "ps": "📢 عمومي نه شتون",
        "my": "📢 ယေဘုယျမရနိုင်မှု",
    },
    "btn_yes_delete_account": {
        "en": "⚠️ Yes, Delete My Account",
        "ps": "⚠️ هو، زما حساب ړنګ کړئ",
        "my": "⚠️ ဟုတ်သည်၊ ကျွန်ုပ်၏အကောင့်ဖျက်သည်",
    },
    "btn_no_cancel": {
        "en": "❌ No, Cancel",
        "ps": "❌ نه، لغوه",
        "my": "❌ မဟုတ်ပါ၊ ဖျက်သိမ်းမည်",
    },
    "btn_acknowledge": {
        "en": "✅ Acknowledge",
        "ps": "✅ تایید",
        "my": "✅ အတည်ပြုသည်",
    },
    "btn_reply": {
        "en": "💬 Reply",
        "ps": "💬 ځواب ورکول",
        "my": "💬 ဖြေကြားမည်",
    },
    "btn_send_feedback": {
        "en": "💬 Send Feedback",
        "ps": "💬 نظر ولیږئ",
        "my": "💬 တုံ့ပြန်ချက်ပို့မည်",
    },
    "btn_acknowledged_done": {
        "en": "✅ Acknowledged",
        "ps": "✅ تایید شو",
        "my": "✅ အတည်ပြုပြီး",
    },
    "msg_already_responded": {
        "en": "You've already responded to this message.",
        "ps": "تاسو دمخه دې پیغام ته ځواب ورکړی دی.",
        "my": "သင်ဤမက်ဆေ့ကိုဖြေပြီးသားဖြစ်သည်။",
    },
    "msg_acknowledged_suffix": {
        "en": "\n\n✅ _You acknowledged this message_",
        "ps": "\n\n✅ _تاسو دا پیغام تایید کړ_",
        "my": "\n\n✅ _သင်ဤမက်ဆေ့ကိုအတည်ပြုပြီး_",
    },
    "msg_reply_prompt": {
        "en": "💬 *Reply to Message*\n\nType your reply:",
        "ps": "💬 *د پیغام ځواب*\n\nخپل ځواب ولیکئ:",
        "my": "💬 *မက်ဆေ့ကိုဖြေကြားမည်*\n\nသင်၏အဖြေရိုက်ထည့်ပါ:",
    },
    "msg_reply_cancelled": {
        "en": "Reply cancelled.",
        "ps": "ځواب لغوه شو.",
        "my": "ဖြေကြားမှုဖျက်သိမ်းပြီး။",
    },
    "msg_reply_sent": {
        "en": "✅ *Reply Sent*\n\nYour reply has been sent to the sender.",
        "ps": "✅ *ځواب ولیږل شو*\n\nستاسو ځواب لیږونکي ته ولیږل شو.",
        "my": "✅ *အဖြေပေးပို့ပြီး*\n\nသင်၏အဖြေပေးပို့သူထံပေးပို့ပြီးပြီ။",
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

    # ── Scheduler background alerts ──────────────────────────────────────────

    "pending_job_reminder": {
        "en": (
            "🔔 *Reminder: Pending Job*\n\n"
            "You have a job waiting for your response:\n\n"
            "*Job #{job_id}:* {title}\n\n"
            "Please accept or decline this job."
        ),
        "ps": (
            "🔔 *یادونه: تمه لرونکی کار*\n\n"
            "تاسو یو کار لرئ چې ستاسو ځواب ته انتظار لري:\n\n"
            "*کار #{job_id}:* {title}\n\n"
            "مهرباني وکړئ دا کار ومنئ یا رد کړئ."
        ),
        "my": (
            "🔔 *သတိပေးချက်: အလုပ်စောင့်ဆိုင်းနေသည်*\n\n"
            "သင်၏ဖြေကြားမှုကိုစောင့်နေသောအလုပ်ရှိသည်:\n\n"
            "*အလုပ် #{job_id}:* {title}\n\n"
            "ကျေးဇူးပြု၍ ဤအလုပ်ကိုလက်ခံ သို့မဟုတ် ငြင်းဆိုပါ။"
        ),
    },
    "job_auto_cancelled": {
        "en": (
            "⚠️ *Job Auto-Cancelled*\n\n"
            "Job #{job_id}: {title}\n\n"
            "This job was automatically cancelled after {hours} hours with no response."
        ),
        "ps": (
            "⚠️ *کار اتوماتیک لغوه شو*\n\n"
            "کار #{job_id}: {title}\n\n"
            "دا کار د {hours} ساعتونو وروسته بې ځوابه پاتې شو او اتوماتیک لغوه شو."
        ),
        "my": (
            "⚠️ *အလုပ်အလိုအလျောက်ဖျက်သိမ်းပြီး*\n\n"
            "အလုပ် #{job_id}: {title}\n\n"
            "ဤအလုပ်သည် {hours} နာရီကြာ ဖြေကြားမှုမရ၍ အလိုအလျောက်ဖျက်သိမ်းလိုက်သည်။"
        ),
    },

    # ── Auth / account messages ───────────────────────────────────────────────

    "account_delete_confirm": {
        "en": (
            "🗑️ *Delete Your Account*\n\n"
            "Are you sure you want to delete your account?\n\n"
            "*This action cannot be undone.*\n"
            "You will need a new access code to register again."
        ),
        "ps": (
            "🗑️ *ستاسو حساب ړنګ کړئ*\n\n"
            "ایا تاسو ډاډه یاست چې خپل حساب ړنګ کول غواړئ؟\n\n"
            "*دا کار بیرته نه شي کیدای.*\n"
            "تاسو به د بیا ثبتنام لپاره نوي د لاسرسي کوډ ته اړتیا ولرئ."
        ),
        "my": (
            "🗑️ *သင်၏အကောင့်ဖျက်ရန်*\n\n"
            "သင်၏အကောင့်ကိုဖျက်မည်မှာ သေချာပါသလား?\n\n"
            "*ဤလုပ်ဆောင်မှုကိုပြန်မလုပ်နိုင်ပါ။*\n"
            "ပြန်မှတ်ပုံတင်ရန် access code အသစ်လိုအပ်သည်။"
        ),
    },
    "account_deleted": {
        "en": "✅ Your account has been deleted.\n\nUse /start with a new access code to register again.",
        "ps": "✅ ستاسو حساب ړنګ شو.\n\nد بیا ثبتنام لپاره د نوي د لاسرسي کوډ سره /start وکاروئ.",
        "my": "✅ သင်၏အကောင့်ဖျက်ပြီးဖြစ်သည်။\n\nပြန်မှတ်ပုံတင်ရန် access code အသစ်ဖြင့် /start ကိုသုံးပါ။",
    },
    "account_delete_cancelled": {
        "en": "Cancelled. Your account is safe.",
        "ps": "لغوه شو. ستاسو حساب خوندي دی.",
        "my": "မဖျက်ပါ။ သင်၏အကောင့်ဘေးကင်းသည်။",
    },

    # ── Subcontractor action confirmations ────────────────────────────────────

    "job_accepted_confirm": {
        "en": (
            "✅ *Job Accepted!*\n\n"
            "Job #{job_id}: {title}\n"
            "Company: {company}\n\n"
            "Use 'My Active Jobs' to start the job when ready."
        ),
        "ps": (
            "✅ *کار ومنل شو!*\n\n"
            "کار #{job_id}: {title}\n"
            "شرکت: {company}\n\n"
            "کله چې تیار یاست د کار د پیل کولو لپاره 'زما فعال کارونه' وکاروئ."
        ),
        "my": (
            "✅ *အလုပ်လက်ခံပြီး!*\n\n"
            "အလုပ် #{job_id}: {title}\n"
            "ကုမ္ပဏီ: {company}\n\n"
            "အသင့်ဖြစ်သောအခါ 'ကျွန်ုပ်လက်ရှိအလုပ်များ' ကိုသုံးပါ။"
        ),
    },
    "job_marked_done_confirm": {
        "en": (
            "✅ *Job Marked as Done!*\n\n"
            "Job #{job_id}: {title}\n\n"
            "The supervisor has been notified and will review your work."
        ),
        "ps": (
            "✅ *کار بشپړ نښه شو!*\n\n"
            "کار #{job_id}: {title}\n\n"
            "سرپرست ته خبر ورکړل شوی او ستاسو کار به بیاکتنه کوي."
        ),
        "my": (
            "✅ *အလုပ်ပြီးစီးကြောင်းမှတ်သားပြီး!*\n\n"
            "အလုပ် #{job_id}: {title}\n\n"
            "ကြီးကြပ်သူကိုအကြောင်းကြားပြီး သင်၏အလုပ်ကိုသုံးသပ်မည်။"
        ),
    },
    "job_started_confirm": {
        "en": (
            "🚀 *Job Started!*\n\n"
            "Job #{job_id}: {title}\n\n"
            "You can mark the job as complete when finished."
        ),
        "ps": (
            "🚀 *کار پیل شو!*\n\n"
            "کار #{job_id}: {title}\n\n"
            "کله چې پای ته ورسیدئ کولی شئ کار بشپړ نښه کړئ."
        ),
        "my": (
            "🚀 *အလုပ်စတင်ပြီး!*\n\n"
            "အလုပ် #{job_id}: {title}\n\n"
            "ပြီးဆုံးသောအခါ အလုပ်ပြီးစီးကြောင်းမှတ်သားနိုင်သည်။"
        ),
    },
    "job_completed_confirm": {
        "en": (
            "🎉 *Job Completed!*\n\n"
            "Job #{job_id} has been marked as complete with photo evidence.\n\n"
            "Great work!"
        ),
        "ps": (
            "🎉 *کار بشپړ شو!*\n\n"
            "کار #{job_id} د عکس د شواهدو سره بشپړ نښه شوی.\n\n"
            "ښه کار!"
        ),
        "my": (
            "🎉 *အလုပ်ပြီးစီးပြီ!*\n\n"
            "အလုပ် #{job_id} ဓာတ်ပုံသက်သေနှင့်တကွ ပြီးစီးကြောင်းမှတ်သားပြီး။\n\n"
            "ကောင်းသောအလုပ်!"
        ),
    },
    "no_jobs_in_progress": {
        "en": (
            "📋 *Submit Job*\n\n"
            "You have no jobs in progress to submit.\n\n"
            "Start a job first from 'My Active Jobs'."
        ),
        "ps": (
            "📋 *کار سپارئ*\n\n"
            "تاسو د سپارلو لپاره پرمخ ولاړ کارونه نلرئ.\n\n"
            "لومړی 'زما فعال کارونه' نه کار پیل کړئ."
        ),
        "my": (
            "📋 *အလုပ်တင်သွင်းရန်*\n\n"
            "တင်သွင်းရန်ဆောင်ရွက်နေဆဲအလုပ်မရှိပါ။\n\n"
            "အရင်ဆုံး 'ကျွန်ုပ်လက်ရှိအလုပ်များ' မှ အလုပ်စတင်ပါ။"
        ),
    },
    "select_job_to_submit": {
        "en": "📋 *Submit Job*\n\nSelect a job to submit for supervisor review:",
        "ps": "📋 *کار سپارئ*\n\nد سرپرست بیاکتنې لپاره کار وټاکئ:",
        "my": "📋 *အလုပ်တင်သွင်းရန်*\n\nကြီးကြပ်သူသုံးသပ်ရန် အလုပ်ရွေးချယ်ပါ:",
    },
    "submission_notes_prompt": {
        "en": (
            "*Submit Job*\n\n"
            "Please provide any notes about the completed work\n"
            "(or send /skip to continue without notes):"
        ),
        "ps": (
            "*کار سپارئ*\n\n"
            "مهرباني وکړئ د بشپړ شوي کار لپاره یادداشتونه ولیکئ\n"
            "(یا بې یادداشتونو دوام لپاره /skip ولیکئ):"
        ),
        "my": (
            "*အလုပ်တင်သွင်းရန်*\n\n"
            "ပြီးစီးသောအလုပ်နှင့်ပတ်သက်သောမှတ်ချက်ထည့်ပါ\n"
            "(သို့မဟုတ် မှတ်ချက်မပါ ဆက်လက်ရန် /skip ပို့ပါ):"
        ),
    },
    "submission_photos_prompt": {
        "en": (
            "*Submit Job*\n\n"
            "Now please send photos as proof of completed work.\n"
            "You can send multiple photos. When done, type /done to submit."
        ),
        "ps": (
            "*کار سپارئ*\n\n"
            "اوس مهرباني وکړئ د بشپړ شوي کار د شواهدو لپاره عکسونه ولیږئ.\n"
            "تاسو کولی شئ ګڼ شمیر عکسونه ولیږئ. کله چې پای ته ورسیدئ /done ولیکئ."
        ),
        "my": (
            "*အလုပ်တင်သွင်းရန်*\n\n"
            "ပြီးစီးသောအလုပ်၏သက်သေအဖြစ် ဓာတ်ပုံများပေးပို့ပါ။\n"
            "ဓာတ်ပုံများစုစုပေးပို့နိုင်သည်။ ပြီးဆုံးသောအခါ /done ရိုက်ပါ။"
        ),
    },
    "photo_added_sub": {
        "en": "📷 Photo {count} added.\n\nSend more photos or type /done to submit.",
        "ps": "📷 عکس {count} اضافه شو.\n\nنور عکسونه ولیږئ یا د سپارلو لپاره /done ولیکئ.",
        "my": "📷 ဓာတ်ပုံ {count} ပေါင်းထည့်ပြီး။\n\nဓာတ်ပုံများပိုပို့ပါ သို့မဟုတ် တင်သွင်းရန် /done ရိုက်ပါ။",
    },
    "quote_notes_prompt": {
        "en": "Would you like to add any notes to your quote?\n\nType your notes or /skip to submit without notes:",
        "ps": "ایا غواړئ خپل نرخ نامې ته یادداشتونه اضافه کړئ؟\n\nخپل یادداشتونه ولیکئ یا بې یادداشتونو د سپارلو لپاره /skip ولیکئ:",
        "my": "သင်၏ကိုးကားမှုတွင် မှတ်ချက်များထည့်လိုပါသလား?\n\nမှတ်ချက်ရိုက်ပါ သို့မဟုတ် မှတ်ချက်မပါ တင်သွင်းရန် /skip ရိုက်ပါ:",
    },
    "quote_submitted_confirm": {
        "en": (
            "✅ *Quote Submitted!*\n\n"
            "Job #{job_id}\n"
            "Your Quote: {amount}\n\n"
            "The supervisor will review your quote and notify you if accepted."
        ),
        "ps": (
            "✅ *نرخ نامه سپارل شوه!*\n\n"
            "کار #{job_id}\n"
            "ستاسو نرخ: {amount}\n\n"
            "سرپرست به ستاسو نرخ نامه بیاکتنه وکړي او که قبول شي درته خبر درکوي."
        ),
        "my": (
            "✅ *ကိုးကားမှုတင်သွင်းပြီး!*\n\n"
            "အလုပ် #{job_id}\n"
            "သင်၏ကိုးကား: {amount}\n\n"
            "ကြီးကြပ်သူသင်၏ကိုးကားမှုကိုသုံးသပ်ပြီး လက်ခံပါကအကြောင်းကြားမည်။"
        ),
    },
    "submission_cancelled": {
        "en": "Job submission cancelled.",
        "ps": "د کار سپارل لغوه شو.",
        "my": "အလုပ်တင်သွင်းမှုပယ်ဖျက်ပြီး။",
    },
    "photo_required_prompt": {
        "en": "📷 Please send a photo as proof of completed work.\nType /done when finished or /cancel to cancel.",
        "ps": "📷 مهرباني وکړئ د بشپړ شوي کار د شواهدو لپاره عکس ولیږئ.\nکله چې پای ته ورسیدئ /done یا د لغوه کولو لپاره /cancel ولیکئ.",
        "my": "📷 ပြီးစီးသောအလုပ်၏သက်သေအဖြစ် ဓာတ်ပုံပေးပို့ပါ။\nပြီးဆုံးသောအခါ /done ကိုရိုက်ပါ သို့မဟုတ် ပယ်ဖျက်ရန် /cancel ရိုက်ပါ။",
    },
    "quote_cancelled": {
        "en": "Quote submission cancelled.",
        "ps": "د نرخ نامې سپارل لغوه شو.",
        "my": "ကိုးကားမှုတင်သွင်းမှုပယ်ဖျက်ပြီး။",
    },

    # ── Supervisor action confirmations ───────────────────────────────────────

    "job_creation_cancelled": {
        "en": "Job creation cancelled.",
        "ps": "د کار جوړول لغوه شو.",
        "my": "အလုပ်ဖန်တီးမှုပယ်ဖျက်ပြီး။",
    },
    "job_saved_draft": {
        "en": (
            "📝 *Job Saved as Draft!*\n\n"
            "Job #{job_id}: {title}\n\n"
            "You can send it later from 'My Jobs'."
        ),
        "ps": (
            "📝 *کار د مسودې په توګه خوندي شو!*\n\n"
            "کار #{job_id}: {title}\n\n"
            "تاسو کولی شئ وروسته 'زما کارونه' نه یې ولیږئ."
        ),
        "my": (
            "📝 *အလုပ်မူကြမ်းအဖြစ်သိမ်းဆည်းပြီး!*\n\n"
            "အလုပ် #{job_id}: {title}\n\n"
            "'ကျွန်ုပ်အလုပ်များ' မှ နောက်မှပေးပို့နိုင်သည်။"
        ),
    },

    # ── Deadline reminders ────────────────────────────────────────────────────

    "deadline_reminder": {
        "en": (
            "⏰ *Deadline Reminder*\n\n"
            "Job #{job_id}: {title}\n"
            "Deadline: *{deadline}*\n\n"
            "This job is due within 24 hours. Please make sure it is completed on time."
        ),
        "ps": (
            "⏰ *د ددلاین یادونه*\n\n"
            "کار #{job_id}: {title}\n"
            "ددلاین: *{deadline}*\n\n"
            "دا کار د ۲۴ ساعتونو دننه پای ته رسیږي. مهرباني وکړئ یې وخت کې بشپړ کړئ."
        ),
        "my": (
            "⏰ *နောက်ဆုံးရက်သတိပေးချက်*\n\n"
            "အလုပ် #{job_id}: {title}\n"
            "နောက်ဆုံးရက်: *{deadline}*\n\n"
            "ဤအလုပ်သည် ၂၄ နာရီအတွင်း ကုန်ဆုံးမည်ဖြစ်သည်။ အချိန်မီပြီးစေရန် သေချာပါစေ။"
        ),
    },

    "deadline_overdue_sub": {
        "en": (
            "🚨 *Job Overdue*\n\n"
            "Job #{job_id}: {title}\n"
            "Deadline was: *{deadline}*\n\n"
            "This job has passed its deadline and is not yet completed. "
            "Please submit it as soon as possible or contact your supervisor."
        ),
        "ps": (
            "🚨 *کار ناوخته*\n\n"
            "کار #{job_id}: {title}\n"
            "ددلاین و: *{deadline}*\n\n"
            "دا کار خپل ددلاین تیر کړی او لا هم بشپړ شوی نه دی. "
            "مهرباني وکړئ هر ژر یې وسپارئ یا خپل سرپرست سره اړیکه ونیسئ."
        ),
        "my": (
            "🚨 *အလုပ်နောက်ကျနေသည်*\n\n"
            "အလုပ် #{job_id}: {title}\n"
            "နောက်ဆုံးရက်ကား: *{deadline}*\n\n"
            "ဤအလုပ်သည် နောက်ဆုံးရက်လွန်ပြီး မပြီးသေးပါ။ "
            "တတ်နိုင်သမျှ အမြန်တင်သွင်းပါ သို့မဟုတ် သင်၏အကြီးအကဲနှင့် ဆက်သွယ်ပါ။"
        ),
    },

    "deadline_overdue_supervisor": {
        "en": (
            "🚨 *Overdue Job Alert*\n\n"
            "Job #{job_id}: {title}\n"
            "Assigned to: *{sub_name}*\n"
            "Deadline was: *{deadline}*\n\n"
            "This job has passed its deadline and has not been submitted yet. "
            "The subcontractor has been notified."
        ),
        "ps": (
            "🚨 *د ناوخته کار خبرداری*\n\n"
            "کار #{job_id}: {title}\n"
            "چا ته ورکول شو: *{sub_name}*\n"
            "ددلاین و: *{deadline}*\n\n"
            "دا کار خپل ددلاین تیر کړی او لا سپارل شوی نه دی. "
            "مقاول ته خبر ورکړل شوی دی."
        ),
        "my": (
            "🚨 *နောက်ကျသောအလုပ်သတိပေးချက်*\n\n"
            "အလုပ် #{job_id}: {title}\n"
            "တာဝန်ပေးထားသူ: *{sub_name}*\n"
            "နောက်ဆုံးရက်ကား: *{deadline}*\n\n"
            "ဤအလုပ်သည် နောက်ဆုံးရက်လွန်ပြီး မတင်သွင်းရသေးပါ။ "
            "အကြွင်းထံ အကြောင်းကြားပြီးဖြစ်သည်။"
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
