import json
import os
import time
import urllib.parse
import urllib.request

LANGUAGES = [
    "ar", "bg", "cs", "de", "el", "es", "en", "fa", "fr", "he",
    "in", "it", "iw", "ko", "lt", "my", "pt", "ro", "ru", "sq",
    "tr", "uk", "vi", "zh", "hu", "pl", "uz", "ja"
]

URL = "https://translate.googleapis.com/translate_a/single"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

VERSION = "2.4.0"


def translate(text, lang):
    params = {
        "client": "gtx",
        "sl": "ru",
        "tl": lang,
        "dt": "t",
        "q": text
    }

    request = urllib.request.Request(
        URL + "?" + urllib.parse.urlencode(params),
        headers=HEADERS
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    return "".join(item[0] for item in data[0])


with open("updates/update_ru.json", "r", encoding="utf-8") as f:
    original = json.load(f)

for lang in LANGUAGES:

    update = original.copy()
    update["lang"] = lang

    if lang == "ru":
        update["changes"] = original["changes"]
    else:
        print("Translate:", lang)
        update["changes"] = translate(original["changes"], lang)
        time.sleep(0.5)

    filename = "updates/update_" + lang + ".json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(update, f, ensure_ascii=False, indent=4)
        
if "GITHUB_OUTPUT" in os.environ:
    build = str(original["build"])
    short_build = build[2:8]
    
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        print("tag={}-{}".format(VERSION, short_build), file=f)
        print("base={}".format(original["name"]), file=f)
        print("body<<EOF", file=f)
        print(original["changes"], file=f)
        print("EOF", file=f)
        

print("Done.")