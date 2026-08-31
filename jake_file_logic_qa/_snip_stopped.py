from urllib.request import urlopen

raw = urlopen(
    "https://app.stage.velvetelves.com/assets/index-DVPQw4mY.js", timeout=60
).read().decode("utf-8", "replace")
idx = raw.find("Automation has stopped")
print("idx", idx)
print(raw[max(0, idx - 400) : idx + 400])
print("--- chunks ---")
# vite lazy import hashes
import re
chunks = sorted(set(re.findall(r"assets/[A-Za-z0-9_-]+\.js", raw)))
print("n chunks", len(chunks))
for c in chunks[:40]:
    print(c)
