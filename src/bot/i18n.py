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
}


def msg(key: str, lang: str = DEFAULT_LANG, **kwargs: str) -> str:
    """Return a translated message string, with optional format kwargs."""
    translations = MESSAGES.get(key, {})
    text = translations.get(lang, translations.get("en", key))
    if kwargs:
        text = text.format(**kwargs)
    return text
