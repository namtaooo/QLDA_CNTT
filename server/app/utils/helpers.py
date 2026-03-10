import re

def clean_html(raw_html: str) -> str:
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def snippet_text(text: str, length: int = 200) -> str:
    if len(text) <= length:
        return text
    return text[:length] + "..."
