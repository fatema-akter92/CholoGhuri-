import requests

SUPPORTED_LANGUAGES = [
    {"code": "bn", "name": "Bengali (বাংলা)", "speech_code": "bn-BD"},
    {"code": "en", "name": "English", "speech_code": "en-US"},
    {"code": "hi", "name": "Hindi (हिन्दी)", "speech_code": "hi-IN"},
    {"code": "ar", "name": "Arabic (العربية)", "speech_code": "ar-SA"},
    {"code": "ja", "name": "Japanese (日本語)", "speech_code": "ja-JP"},
    {"code": "fr", "name": "French (Français)", "speech_code": "fr-FR"},
    {"code": "es", "name": "Spanish (Español)", "speech_code": "es-ES"},
]

TRAVEL_PHRASES = [
    # Greetings & Basics
    {
        "id": 1,
        "category": "Greetings & Basics",
        "en": "Hello / Peace be upon you",
        "bn": "আসসালামু আলাইকুম / নমস্কার",
        "phonetic_bn": "Assalamu Alaikum / Nomoshkar",
        "hi": "नमस्ते",
        "ar": "السلام عليكم",
        "ja": "こんにちは",
        "fr": "Bonjour",
        "es": "Hola",
    },
    {
        "id": 2,
        "category": "Greetings & Basics",
        "en": "Thank you very much",
        "bn": "অনেক ধন্যবাদ",
        "phonetic_bn": "Onek dhonnobad",
        "hi": "बहुत धन्यवाद",
        "ar": "شكراً جزيلاً",
        "ja": "ありがとうございます",
        "fr": "Merci beaucoup",
        "es": "Muchas gracias",
    },
    {
        "id": 3,
        "category": "Greetings & Basics",
        "en": "Excuse me, can you help me?",
        "bn": "শুনুন, আমাকে একটু সাহায্য করতে পারবেন?",
        "phonetic_bn": "Shunun, amake ektu shahajjo korte parben?",
        "hi": "माफ कीजिए, क्या आप मेरी मदद कर सकते हैं?",
        "ar": "لو سمحت، هل يمكنك مساعدتي؟",
        "ja": "すみません、手伝っていただけますか？",
        "fr": "Excusez-moi, pouvez-vous m'aider ?",
        "es": "Disculpe, ¿puede ayudarme?",
    },
    {
        "id": 4,
        "category": "Greetings & Basics",
        "en": "I do not speak Bengali well",
        "bn": "আমি ভালো বাংলা বলতে পারি না",
        "phonetic_bn": "Ami bhalo Bangla bolte pari na",
        "hi": "मैं बंगाली ठीक से नहीं बोल पाता",
        "ar": "أنا لا أتحدث البنغالية جيداً",
        "ja": "ベンガル語があまり話せません",
        "fr": "Je ne parle pas bien bengali",
        "es": "No hablo bien bengalí",
    },
    # Transport & Directions
    {
        "id": 5,
        "category": "Transport & Directions",
        "en": "How much is the fare to go here?",
        "bn": "এখানে যেতে ভাড়া কত টাকা লাগবে?",
        "phonetic_bn": "Ekhane jete bhara koto taka lagbe?",
        "hi": "यहाँ जाने का किराया कितना होगा?",
        "ar": "كم الأجرة للذهاب إلى هنا؟",
        "ja": "ここまで運賃はいくらですか？",
        "fr": "Combien coûte le trajet jusqu'ici ?",
        "es": "¿Cuánto cuesta ir hasta aquí?",
    },
    {
        "id": 6,
        "category": "Transport & Directions",
        "en": "Please stop right here",
        "bn": "দয়া করে এখানেই থামান",
        "phonetic_bn": "Doya kore ekhanei thaman",
        "hi": "कृपया यहीं रुकें",
        "ar": "توقف هنا من فضلك",
        "ja": "ここで止めてください",
        "fr": "Arrêtez-vous ici s'il vous plaît",
        "es": "Por favor, pare aquí",
    },
    {
        "id": 7,
        "category": "Transport & Directions",
        "en": "Where is the nearest bus or train station?",
        "bn": "সবচেয়ে কাছের বাস বা রেল স্টেশন কোথায়?",
        "phonetic_bn": "Shobcheye kacher bus ba rail station kothay?",
        "hi": "सबसे नज़दीकी बस या रेलवे स्टेशन कहाँ है?",
        "ar": "أين أقرب محطة حافلات أو قطار؟",
        "ja": "一番近いバス停または駅はどこですか？",
        "fr": "Où est la gare ou l'arrêt de bus le plus proche ?",
        "es": "¿Dónde está la estación de autobús o tren más cercana?",
    },
    {
        "id": 8,
        "category": "Transport & Directions",
        "en": "Please use the meter",
        "bn": "দয়া করে মিটারে চলুন",
        "phonetic_bn": "Doya kore meter-e cholun",
        "hi": "कृपया मीटर से चलिए",
        "ar": "من فضلك استخدم العداد",
        "ja": "メーターを使ってください",
        "fr": "Veuillez utiliser le compteur",
        "es": "Por favor, use el taxímetro",
    },
    # Food, Halal & Allergies
    {
        "id": 9,
        "category": "Food, Halal & Allergies",
        "en": "Is this food Halal?",
        "bn": "এই খাবারটি কি হালাল?",
        "phonetic_bn": "Ei khabarti ki Halal?",
        "hi": "क्या यह खाना हलाल है?",
        "ar": "هل هذا الطعام حلال؟",
        "ja": "この料理はハラールですか？",
        "fr": "Est-ce que cette nourriture est halal ?",
        "es": "¿Esta comida es halal?",
    },
    {
        "id": 10,
        "category": "Food, Halal & Allergies",
        "en": "I have a nut / peanut allergy (No nuts please)",
        "bn": "আমার বাদামে এলার্জি আছে, বাদাম দেবেন না",
        "phonetic_bn": "Amar badame allergy ache, badam deben na",
        "hi": "मुझे मूंगफली/मेवे से एलर्जी है, कृपया न डालें",
        "ar": "لدي حساسية من المكسرات، بدون مكسرات من فضلك",
        "ja": "ナッツアレルギーがあります。ナッツは入れないでください",
        "fr": "Je suis allergique aux noix, sans noix s'il vous plaît",
        "es": "Soy alérgico a los frutos secos, sin frutos secos por favor",
    },
    {
        "id": 11,
        "category": "Food, Halal & Allergies",
        "en": "Vegetarian food only (No meat or fish)",
        "bn": "শুধুমাত্র নিরামিষ খাবার (মাংস বা মাছ ছাড়া)",
        "phonetic_bn": "Shudhumatro niramish khabar (mangsho ba mach chara)",
        "hi": "केवल शाकाहारी भोजन (मांस या मछली के बिना)",
        "ar": "طعام نباتي فقط (بدون لحم أو سمك)",
        "ja": "ベジタリアン料理のみ（肉・魚なし）",
        "fr": "Nourriture végétarienne uniquement (sans viande ni poisson)",
        "es": "Solo comida vegetariana (sin carne ni pescado)",
    },
    {
        "id": 12,
        "category": "Food, Halal & Allergies",
        "en": "Please make it less spicy and bottled water only",
        "bn": "ঝাল কম দেবেন এবং বোতলের পানি দিন",
        "phonetic_bn": "Jhal kom deben ebong botoler pani din",
        "hi": "कृपया कम तीखा बनाएं और बोतलबंद पानी दें",
        "ar": "اجعله أقل حرارة وأعطني ماءً معبأً من فضلك",
        "ja": "辛さ控えめで、ペットボトルの水をください",
        "fr": "Moins épicé et de l'eau en bouteille s'il vous plaît",
        "es": "Poco picante y agua embotellada por favor",
    },
    # Hotels & Shopping
    {
        "id": 13,
        "category": "Hotels & Shopping",
        "en": "How much does this cost?",
        "bn": "এটার দাম কত টাকা?",
        "phonetic_bn": "Etar dam koto taka?",
        "hi": "इसकी कीमत कितनी है?",
        "ar": "كم سعر هذا؟",
        "ja": "これはいくらですか？",
        "fr": "Combien cela coûte-t-il ?",
        "es": "¿Cuánto cuesta esto?",
    },
    {
        "id": 14,
        "category": "Hotels & Shopping",
        "en": "I have a hotel reservation",
        "bn": "আমার একটি হোটেল বুকিং আছে",
        "phonetic_bn": "Amar ekti hotel booking ache",
        "hi": "मेरी होटल बुकिंग है",
        "ar": "لدي حجز فندقي",
        "ja": "ホテルの予約があります",
        "fr": "J'ai une réservation d'hôtel",
        "es": "Tengo una reserva de hotel",
    },
    {
        "id": 15,
        "category": "Hotels & Shopping",
        "en": "Can you lower the price a little?",
        "bn": "দাম কি একটু কমানো যাবে?",
        "phonetic_bn": "Dam ki ektu komano jabe?",
        "hi": "क्या आप कीमत थोड़ी कम कर सकते हैं?",
        "ar": "هل يمكنك تخفيض السعر قليلاً؟",
        "ja": "もう少し安くなりますか？",
        "fr": "Pouvez-vous baisser un peu le prix ?",
        "es": "¿Puede bajar un poco el precio?",
    },
    # Emergency & Medical
    {
        "id": 16,
        "category": "Emergency & Medical",
        "en": "Emergency! Please call 999 or Tourist Police",
        "bn": "জরুরি অবস্থা! দয়া করে ৯৯৯ অথবা ট্যুরিস্ট পুলিশে কল করুন",
        "phonetic_bn": "Joruri obostha! Doya kore 999 othoba Tourist Police-e kol korun",
        "hi": "आपातकाल! कृपया 999 या टूरिस्ट पुलिस को कॉल करें",
        "ar": "طوارئ! يرجى الاتصال بالرقم 999 أو شرطة السياحة",
        "ja": "緊急事態です！999または観光警察に電話してください",
        "fr": "Urgence ! Veuillez appeler le 999 ou la police touristique",
        "es": "¡Emergencia! Por favor llame al 999 o a la policía turística",
    },
    {
        "id": 17,
        "category": "Emergency & Medical",
        "en": "Please take me to the nearest hospital",
        "bn": "দয়া করে আমাকে সবচেয়ে কাছের হাসপাতালে নিয়ে যান",
        "phonetic_bn": "Doya kore amake shobcheye kacher hashpatale niye jan",
        "hi": "कृपया मुझे सबसे नज़दीकी अस्पताल ले चलिए",
        "ar": "من فضلك خذني إلى أقرب مستشفى",
        "ja": "一番近い病院へ連れて行ってください",
        "fr": "Emmenez-moi à l'hôpital le plus proche s'il vous plaît",
        "es": "Lléveme al hospital más cercano por favor",
    },
    {
        "id": 18,
        "category": "Emergency & Medical",
        "en": "Where is a pharmacy / medicine shop?",
        "bn": "ওষুধের দোকান (ফার্মেসি) কোথায়?",
        "phonetic_bn": "Oshudher dokan (pharmacy) kothay?",
        "hi": "दवाई की दुकान (फार्मेसी) कहाँ है?",
        "ar": "أين توجد الصيدلية؟",
        "ja": "薬局はどこですか？",
        "fr": "Où est la pharmacie ?",
        "es": "¿Dónde hay una farmacia?",
    },
]

PHONETIC_WORD_MAP = {
    "hello": "Assalamu Alaikum / Nomoshkar",
    "hi": "Ohe / Salam",
    "thanks": "Dhonnobad",
    "thank you": "Onek dhonnobad",
    "yes": "Ji / Haan",
    "no": "Na",
    "please": "Doya kore",
    "sorry": "Dukkhito",
    "help": "Shahajjo",
    "water": "Pani",
    "food": "Khabar",
    "hotel": "Hotel",
    "hospital": "Hashpatal",
    "police": "Police",
    "toilet": "Washroom / Toilet",
    "how much": "Koto taka?",
    "where": "Kothay?",
    "airport": "Bimanbondor",
    "train": "Relgari / Train",
    "bus": "Bus",
    "boat": "Nouka / Launch",
    "beach": "Shomudro shoikot",
    "delicious": "Khub moja / Shushadu",
}

COMMON_EN_TO_BN = {
    "hello": "হ্যালো / আসসালামু আলাইকুম",
    "hi": "হ্যালো / কেমন আছেন?",
    "good morning": "সুপ্রভাত",
    "good afternoon": "শুভ অপরাহ্ন",
    "good evening": "শুভ সন্ধ্যা",
    "good night": "শুভ রাত্রি",
    "how are you": "আপনি কেমন আছেন?",
    "i am fine": "আমি ভালো আছি",
    "i am good": "আমি ভালো আছি",
    "what is your name": "আপনার নাম কী?",
    "nice to meet you": "আপনার সাথে দেখা হয়ে ভালো লাগলো",
    "i love bangladesh": "আমি বাংলাদেশকে ভালোবাসি",
    "welcome to bangladesh": "বাংলাদেশে স্বাগতম",
    "welcome": "স্বাগতম",
    "thank you": "ধন্যবাদ",
    "thanks": "ধন্যবাদ",
    "thank you very much": "অসংখ্য ধন্যবাদ",
    "you are welcome": "আপনাকে স্বাগতম",
    "please": "দয়া করে",
    "sorry": "দুঃখিত",
    "excuse me": "মাফ করবেন",
    "yes": "জি / হ্যাঁ",
    "no": "না",
    "goodbye": "বিদায়, আবার দেখা হবে",
    "bye": "আবার দেখা হবে",
    "see you again": "আবার দেখা হবে",
    "where is the hotel": "হোটেলটি কোথায়?",
    "take me to the hotel": "আমাকে হোটেলে নিয়ে চলুন",
    "where is cox's bazar": "কক্সবাজার কোথায়?",
    "where is coxs bazar": "কক্সবাজার কোথায়?",
    "how much does it cost": "এটির দাম কত?",
    "how much": "কত টাকা?",
    "this food is delicious": "এই খাবারটি খুবই সুস্বাদু",
    "i am hungry": "আমার ক্ষুধা লেগেছে",
    "i am thirsty": "আমার তৃষ্ণা পেয়েছে",
    "water please": "দয়া করে একটু পানি দিন",
    "i want water": "আমি পানি চাই",
    "help me": "আমাকে সাহায্য করুন",
    "i need help": "আমার সাহায্য প্রয়োজন",
    "can you help me": "আপনি কি আমাকে সাহায্য করতে পারেন?",
    "can you help me please": "দয়া করে আমাকে সাহায্য করতে পারবেন?",
    "where is the hospital": "হাসপাতাল কোথায়?",
    "where is the nearest hospital": "নিকটতম হাসপাতাল কোথায়?",
    "where is the police station": "থানা কোথায়?",
    "where is the washroom": "ওয়াশরুম বা টয়লেট কোথায়?",
    "where is the bathroom": "বাথরুম বা টয়লেট কোথায়?",
    "where is the airport": "বিমানবন্দর কোথায়?",
    "where is the train station": "রেল স্টেশন কোথায়?",
    "where is the bus stand": "বাস স্ট্যান্ড কোথায়?",
    "stop here": "এখানে থামুন",
    "turn left": "বামে ঘুরুন",
    "turn right": "ডানে ঘুরুন",
    "go straight": "সোজা যান",
    "very good": "খুব ভালো",
    "how much is the rickshaw fare": "রিকশা ভাড়া কত?",
    "how much is the bus ticket": "বাসের টিকিটের দাম কত?",
}

EN_TO_BN_WORDS = {
    "i": "আমি", "me": "আমাকে", "my": "আমার", "we": "আমরা", "our": "আমাদের",
    "you": "আপনি", "your": "আপনার", "he": "তিনি", "she": "তিনি", "they": "তারা",
    "this": "এটি", "that": "ওটি", "these": "এগুলো", "it": "এটি",
    "hello": "হ্যালো", "hi": "হ্যালো", "welcome": "স্বাগতম", "please": "দয়া করে",
    "thank": "ধন্যবাদ", "thanks": "ধন্যবাদ", "sorry": "দুঃখিত", "yes": "জি", "no": "না",
    "not": "না", "good": "ভালো", "great": "দারুণ", "nice": "সুন্দর", "beautiful": "সুন্দর",
    "very": "খুব", "fine": "ভালো", "morning": "সকাল", "afternoon": "বিকেল",
    "evening": "সন্ধ্যা", "night": "রাত", "today": "আজ", "tomorrow": "আগামীকাল",
    "yesterday": "গতকাল", "now": "এখন", "later": "পরে", "here": "এখানে", "there": "ওখানে",
    "where": "কোথায়", "what": "কী", "who": "কে", "when": "কখন", "why": "কেন",
    "how": "কীভাবে", "much": "কত", "many": "অনেক", "need": "প্রয়োজন", "want": "চাই",
    "like": "পছন্দ করি", "love": "ভালোবাসি", "go": "যেতে", "going": "যাচ্ছি",
    "come": "আসুন", "take": "নিয়ে চলুন", "stop": "থামুন", "help": "সাহায্য",
    "call": "কল করুন", "find": "খুঁজুন", "show": "দেখান", "speak": "বলি",
    "understand": "বুঝি", "know": "জানি", "eat": "খেতে", "drink": "পান করতে",
    "hungry": "ক্ষুধার্ত", "thirsty": "তৃষ্ণার্ত", "water": "পানি", "food": "খাবার",
    "rice": "ভাত", "biryani": "বিরিয়ানি", "tea": "চা", "coffee": "কফি",
    "fish": "মাছ", "chicken": "মুরগি", "beef": "গরুর মাংস", "spicy": "ঝাল",
    "sweet": "মিষ্টি", "delicious": "সুস্বাদু", "hot": "গরম", "cold": "ঠান্ডা",
    "clean": "পরিষ্কার", "safe": "নিরাপদ", "money": "টাকা", "price": "দাম",
    "fare": "ভাড়া", "cost": "খরচ", "ticket": "টিকিট", "bill": "বিল",
    "hotel": "হোটেল", "room": "রুম", "bed": "বিছানা", "hospital": "হাসপাতাল",
    "doctor": "ডাক্তার", "medicine": "ওষুধ", "pharmacy": "ফার্মেসি", "police": "পুলিশ",
    "toilet": "টয়লেট", "washroom": "ওয়াশরুম", "bathroom": "বাথরুম",
    "airport": "বিমানবন্দর", "station": "স্টেশন", "bus": "বাস", "train": "ট্রেন",
    "car": "গাড়ি", "rickshaw": "রিকশা", "boat": "নৌকা", "road": "রাস্তা",
    "street": "সড়ক", "market": "বাজার", "shop": "দোকান", "mosque": "মসজিদ",
    "temple": "মন্দির", "church": "গির্জা", "museum": "জাদুঘর", "beach": "সমুদ্র সৈকত",
    "sea": "সমুদ্র", "river": "নদী", "hill": "পাহাড়", "forest": "বন",
    "city": "শহর", "village": "গ্রাম", "bangladesh": "বাংলাদেশ", "dhaka": "ঢাকা",
    "sylhet": "সিলেট", "chattogram": "চট্টগ্রাম", "chittagong": "চট্টগ্রাম",
    "coxs": "কক্স", "cox's": "কক্স", "bazar": "বাজার", "rajshahi": "রাজশাহী",
    "khulna": "খুলনা", "barishal": "বরিশাল", "rangpur": "রংপুর", "sundarbans": "সুন্দরবন",
    "sajek": "সাজেক", "bandarban": "বান্দরবান", "rangamati": "রাঙামাটি",
    "left": "বামে", "right": "ডানে", "straight": "সোজা", "near": "কাছে", "far": "দূরে",
    "friend": "বন্ধু", "family": "পরিবার", "name": "নাম", "time": "সময়",
    "traditional": "ঐতিহ্যবাহী", "bengali": "বাঙালি", "local": "স্থানীয়", "halal": "হালাল",
}

_STOPWORDS_EN = {"is", "are", "am", "the", "a", "an", "of", "in", "on", "at", "to", "for", "from", "do", "does"}
_POISONED_OUTPUTS = ("ব্যাগোবো", "MYMEMORY WARNING", "INVALID", "PLEASE SELECT TWO DISTINCT", "QUERY LENGTH LIMIT")


def _normalize_phrase(text: str) -> str:
    return " ".join((text or "").lower().strip().rstrip("?.!,").split())


def _has_bengali(text: str) -> bool:
    return any("\u0980" <= ch <= "\u09FF" for ch in (text or ""))


def _has_devanagari(text: str) -> bool:
    return any("\u0900" <= ch <= "\u097F" for ch in (text or ""))


def _is_valid_translation(candidate: str, source_text: str, source_lang: str, target_lang: str) -> bool:
    clean = (candidate or "").strip()
    if not clean:
        return False
    upper = clean.upper()
    if any(p in upper or p in clean for p in _POISONED_OUTPUTS):
        return False
    if target_lang == "bn":
        # Must actually contain Bengali Unicode script and zero Devanagari/Hindi characters
        return _has_bengali(clean) and not _has_devanagari(clean)
    if source_lang != target_lang and clean.lower() == source_text.strip().lower():
        if target_lang in {"bn", "hi", "ar", "ja"}:
            return False
    return True


def _offline_bengali_fallback(clean: str) -> str:
    norm = _normalize_phrase(clean)
    if norm in COMMON_EN_TO_BN:
        return COMMON_EN_TO_BN[norm]
    words = clean.split()
    bn_parts = []
    for raw_w in words:
        w = raw_w.lower().strip("?!.,\"'")
        if w in EN_TO_BN_WORDS:
            bn_parts.append(EN_TO_BN_WORDS[w])
        elif w in _STOPWORDS_EN:
            continue
        elif _has_bengali(raw_w):
            bn_parts.append(raw_w)
    if bn_parts:
        joined = " ".join(bn_parts)
        if "?" in clean and not joined.endswith("?"):
            joined += "?"
        return joined
    return "অনুগ্রহ করে স্পষ্ট ইংরেজি ভ্রমণ বাক্য লিখুন অথবা নিচের বাংলা বাক্যগুলো ব্যবহার করুন।"


def translate_text(text: str, source_lang: str = "en", target_lang: str = "bn"):
    clean = (text or "").strip()
    if not clean:
        return {"source_text": "", "translated_text": "", "phonetic": "", "provider": "phrasebook"}

    norm = _normalize_phrase(clean)

    # 1. Exact phrase match in curated phrasebook & verified EN->BN dictionary (punctuation-insensitive)
    for p in TRAVEL_PHRASES:
        src_val = _normalize_phrase(p.get(source_lang, p["en"]))
        if norm == src_val:
            return {
                "source_text": clean,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "translated_text": p.get(target_lang, p["bn"]),
                "phonetic": p["phonetic_bn"] if target_lang == "bn" else "",
                "provider": "CholoGhuri Verified Travel Phrasebook",
            }

    if source_lang == "en" and target_lang == "bn" and norm in COMMON_EN_TO_BN:
        return {
            "source_text": clean,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "translated_text": COMMON_EN_TO_BN[norm],
            "phonetic": "",
            "provider": "CholoGhuri Verified Bengali Dictionary",
        }

    # 2. Try Google Translate GTX API (produces pure standard Bangladeshi Bengali & 7 languages)
    translated = None
    provider = "CholoGhuri Built-in Travel Dictionary"
    if source_lang != target_lang:
        try:
            r = requests.get(
                "https://translate.googleapis.com/translate_a/single",
                params={"client": "gtx", "sl": source_lang, "tl": target_lang, "dt": "t", "q": clean},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=5,
            )
            if r.status_code == 200:
                segments = r.json()[0] or []
                candidate = "".join(seg[0] for seg in segments if seg and seg[0]).strip()
                if _is_valid_translation(candidate, clean, source_lang, target_lang):
                    translated = candidate
                    provider = "Google Translate Live Engine"
        except Exception:
            translated = None

    # 3. Backup: MyMemory Translation API (with strict Bengali script & quality checks)
    if not translated and source_lang != target_lang:
        try:
            r = requests.get(
                "https://api.mymemory.translated.net/get",
                params={"q": clean, "langpair": f"{source_lang}|{target_lang}", "de": "chologhuribd@gmail.com"},
                timeout=5,
            )
            if r.status_code == 200:
                resp_data = r.json().get("responseData", {})
                candidate = (resp_data.get("translatedText") or "").strip()
                try:
                    match_score = float(resp_data.get("match") or 0)
                except (TypeError, ValueError):
                    match_score = 0.0
                if match_score >= 0.45 and _is_valid_translation(candidate, clean, source_lang, target_lang):
                    translated = candidate
                    provider = "MyMemory Live Translation API"
        except Exception:
            translated = None

    # 4. Pure Bengali Script Offline Fallback (never returns Banglish inside translated_text)
    if not translated:
        if source_lang == target_lang:
            translated = clean
        elif target_lang == "bn":
            translated = _offline_bengali_fallback(clean)
        else:
            translated = clean

    phonetic = ""
    if target_lang == "bn":
        matched_hints = [
            f"{k} -> {v}" for k, v in PHONETIC_WORD_MAP.items() if k in norm
        ]
        phonetic = " | ".join(matched_hints[:4]) if matched_hints else "Tap speaker button to play Bengali voice audio."

    return {
        "source_text": clean,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "translated_text": translated,
        "phonetic": phonetic,
        "provider": provider,
    }
