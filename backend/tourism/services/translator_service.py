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
