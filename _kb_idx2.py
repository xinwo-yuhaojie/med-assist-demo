# -*- coding: utf-8 -*-
"""v44\uff1a\u5224\u65ad kb.js \u7684 index \u6620\u5c04\u952e\u4e0e drugs[].n \u7684\u5bf9\u5e94\u5173\u7cfb\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KB = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\kb.js"
kb = io.open(KB, encoding="utf-8").read()

names = re.findall(r'"n":"([^"]+)"', kb)
print("drugs n \u6570\u91cf = %d" % len(names))
print("\u524d 5 \u4e2a n: %s" % names[:5])
print("\u540e 5 \u4e2a n: %s" % names[-5:])

# index \u5bf9\u8c61
mi = re.search(r',?\s*"?index"?\s*:\s*\{', kb[kb.find("drugs: ["):])
print("\nindex \u4f4d\u7f6e = %s" % (bool(mi)))
if mi:
    s = kb.find("drugs: [") + mi.start()
    k2 = kb.find("{", s)
    depth = 0
    m = k2
    while m < len(kb):
        if kb[m] == "{":
            depth += 1
        elif kb[m] == "}":
            depth -= 1
            if depth == 0:
                break
        m += 1
    seg = kb[k2:m + 1]
    pairs = re.findall(r'"([^"]+)":\s*(\d+)', seg)
    print("index \u6761\u76ee\u6570 = %d" % len(pairs))
    print("index \u524d 8 \u4e2a: %s" % pairs[:8])
    print("index \u540e 4 \u4e2a: %s" % pairs[-4:])
    # \u952e\u662f\u5426\u4e3a\u4e2d\u6587\u836f\u540d
    zh = [p for p in pairs if any('\u4e00' <= ch <= '\u9fff' for ch in p[0])]
    print("\u952e\u4e2d\u542b\u4e2d\u6587\u7684\u6570\u91cf = %d" % len(zh))
    if zh:
        print("\u793a\u4f8b: %s" % zh[:5])
    # \u6bd4\u5bf9\uff1aindex \u7684\u952e\u662f\u5426\u80fd\u5728 n \u91cc\u627e\u5230
    hit = 0
    for k, v in pairs[:50]:
        if k in names:
            hit += 1
    print("index \u524d 50 \u4e2a\u952e\u4e2d\u80fd\u5728 n \u91cc\u627e\u5230\u7684 = %d" % hit)
    # \u6570\u503c\u8303\u56f4
    vals = [int(v) for k, v in pairs]
    print("index \u6570\u503c\u8303\u56f4 = %d..%d" % (min(vals), max(vals)))
