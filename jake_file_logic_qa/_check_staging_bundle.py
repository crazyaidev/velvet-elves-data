from urllib.request import urlopen
import re

html = urlopen("https://app.stage.velvetelves.com/", timeout=30).read().decode()
print("--- html snippets ---")
for m in re.findall(r'(?:src|href)="(/assets/[^"]+)"', html):
    print("ref", m)
# also modulepreload
for m in re.findall(r'/assets/[A-Za-z0-9._-]+\.js', html):
    print("js", m)

needles = [
    "Checking automation",
    "Automation has stopped",
    "Automation active",
    "seller's agent closing information",
]
# download main + any other js referenced
urls = sorted(set(re.findall(r'/assets/[A-Za-z0-9._-]+\.js', html)))
print("urls", urls)
blob = ""
for u in urls:
    raw = urlopen("https://app.stage.velvetelves.com" + u, timeout=60).read().decode("utf-8", "replace")
    print("file", u, "len", len(raw))
    blob += raw
print("--- needles in fetched js ---")
for s in needles:
    print(s, s in blob)
