from deep_translator import GoogleTranslator


def to_english(text, lang):
    if lang == "en":
        return text
    return GoogleTranslator(source=lang, target="en").translate(text)


def from_english(text, lang):
    if lang == "en":
        return text
    return GoogleTranslator(source="en", target=lang).translate(text)