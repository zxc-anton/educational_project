import requests
from flask_babel import _

def translate(text, source_lang, dest_lang):
    url = f"https://api.mymemory.translated.net/get?q={text}&langpair={source_lang}|{dest_lang}"
    try:
        responce = requests.post(url=url)
        responce.raise_for_status()
        return responce.json()['responseData']['translatedText']
    except:
        return _("Error: the translation service failed.")

