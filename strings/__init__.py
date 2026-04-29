from strings.en import STRINGS as EN_STRINGS
from strings.hi import STRINGS as HI_STRINGS

_LANGS = {
    "en": EN_STRINGS,
    "hi": HI_STRINGS,
}


def get_string(lang: str, key: str, **kwargs) -> str:
    strings = _LANGS.get(lang, EN_STRINGS)
    text = strings.get(key, EN_STRINGS.get(key, key))
    try:
        return text.format(**kwargs) if kwargs else text
    except Exception:
        return text
