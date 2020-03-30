import requests
import os
import urllib.parse


def chunkify(text, limit):
    chunks = []
    while len(text) > limit:
        idx = text.index("\n", limit)
        chunks.append(text[:idx])
        text = text[idx:]
    chunks.append(text)
    return chunks


def escape_md(text):
    return text.replace("_", "\_").replace("*", "\*").replace(">>>", "\>>>")


def create_corimd_notebook():
    base_url = "https://notes.status.im/"
    create_new_note_url = base_url + "new"
    res = requests.get(create_new_note_url)
    return res.url


def wolfram_simple_query(query):
    base_url = "https://api.wolframalpha.com/v2/result?i={0}&appid={1}"
    app_id = os.getenv("WOLFRAM_ALPHA_APP_ID")
    query_url = base_url.format(urllib.parse.quote(query), app_id)
    res = requests.get(query_url).text
    return res
