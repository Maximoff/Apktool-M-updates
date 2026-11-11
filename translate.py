import json
import os
import time
import random
import urllib.error
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

# Задержка между успешными переводами
REQUEST_DELAY = 2.5

# Максимальное количество попыток одного перевода
MAX_RETRIES = 6


def translate(text, lang):
    params = {
        "client": "gtx",
        "sl": "ru",
        "tl": lang,
        "dt": "t",
        "q": text
    }

    url = URL + "?" + urllib.parse.urlencode(params)

    for attempt in range(MAX_RETRIES):
        request = urllib.request.Request(url, headers=HEADERS)

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

            result = "".join(item[0] for item in data[0])

            if not result and text:
                raise ValueError("Google returned an empty translation")

            return result

        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise

            retry_after = e.headers.get("Retry-After")
            try:
                retry_after = float(retry_after) if retry_after else 0
            except ValueError:
                retry_after = 0

            if attempt == MAX_RETRIES - 1:
                raise

            delay = max(retry_after, min(60, 3 * (2 ** attempt)))
            delay += random.uniform(0, 1)

            print(
                "Google error {} for {}. Retry {}/{} in {:.1f}s".format(
                    e.code, lang, attempt + 1, MAX_RETRIES, delay
                )
            )

            time.sleep(delay)

        except urllib.error.URLError as e:
            if attempt == MAX_RETRIES - 1:
                raise

            delay = min(60, 3 * (2 ** attempt)) + random.uniform(0, 1)

            print(
                "Connection error for {}. Retry {}/{} in {:.1f}s: {}".format(
                    lang, attempt + 1, MAX_RETRIES, delay, e
                )
            )

            time.sleep(delay)


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

        time.sleep(REQUEST_DELAY)

    filename = "updates/update_" + lang + ".json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(update, f, ensure_ascii=False, indent=4)


if "GITHUB_OUTPUT" in os.environ:
    build = str(original["build"])
    short_build = build[2:8]

    base_tag = "{}-{}".format(VERSION, short_build)
    tag = base_tag

    github_token = os.environ["GITHUB_TOKEN"]
    repository = os.environ["GITHUB_REPOSITORY"]

    api_url = "https://api.github.com/repos/{}/releases/tags/{}"

    request_headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + github_token,
        "X-GitHub-Api-Version": "2022-11-28"
    }

    number = 1

    while True:
        if number == 1:
            tag = base_tag
        else:
            tag = "{}({})".format(base_tag, number)

        url = api_url.format(
            repository,
            urllib.parse.quote(tag, safe="")
        )

        request = urllib.request.Request(
            url,
            headers=request_headers
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                print("Release already exists:", tag)
                number += 1

        except urllib.error.HTTPError as e:
            if e.code == 404:
                break

            raise

    print("Release tag:", tag)

    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        print("tag={}".format(tag), file=f)
        print("base={}".format(original["name"]), file=f)
        print("body<<EOF", file=f)
        print(original["changes"], file=f)
        print("EOF", file=f)


print("Done.")
