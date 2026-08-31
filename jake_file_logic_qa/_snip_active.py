from urllib.request import urlopen

raw = urlopen(
    "https://app.stage.velvetelves.com/assets/index-DVPQw4mY.js", timeout=60
).read().decode("utf-8", "replace")
for needle in (
    "Automation active",
    "Checking automation",
    "Checking the last hourly run",
    "Named letters",
):
    idx = raw.find(needle)
    print("====", needle, "idx", idx)
    if idx >= 0:
        print(raw[max(0, idx - 250) : idx + 350])
        print()
