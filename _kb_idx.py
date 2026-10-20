# -*- coding: utf-8 -*-
"""v44\uff1a\u67e5 kb.js \u7684 index \u6620\u5c04\u7ed3\u6784\u3002"""
import io
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KB = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\kb.js"
kb = io.open(KB, encoding="utf-8").read()
i = kb.find("drugs: [")
# \u62ff\u5934\u5b9a\u4f4d\u6570\u7ec4\u8fb9\u754c\uff08\u62ec\u53f7\u8ba1\u6570\uff09
depth = 0
j = i + 7
while j < len(kb):
    c = kb[j]
    if c == "[":
        depth += 1
    elif c == "]":
        depth -= 1
        if depth == 0:
            break
    j += 1
print("drugs \u6570\u7ec4\u8fb9\u754c: %d .. %d" % (i, j))
arr = kb[i + 8:j]
data = json.loads(arr)
print("\u6761\u76ee\u6570 = %d" % len(data))
print("\u7b2c\u4e00\u6761\u5b57\u6bb5 = %s" % list(data[0].keys()))
tail = kb[j + 1:j + 200]
print("\u6570\u7ec4\u540e\u7684\u5185\u5bb9: %r" % tail[:150])

# index \u7684\u952e
mi = re.search(r'"?index"?\s*:\s*\{', tail)
if mi:
    k2 = tail.find("{", mi.start())
    depth = 0
    m = k2
    while m < len(tail):
        if tail[m] == "{":
            depth += 1
        elif tail[m] == "}":
            depth -= 1
            if depth == 0:
                break
        m += 1
    idx = json.loads(tail[k2:m + 1])
    ks = list(idx.keys())[:6]
    print("\nindex \u6761\u76ee\u6570 = %d" % len(idx))
    print("index \u524d\u51e0\u4e2a\u952e = %s" % ks)
    # \u952e\u662f\u4e0d\u662f\u836f\u540d\u7684\u62fc\u97f3/\u82f1\u6587 id
    nm = data[0]["n"]
    print("\u7b2c\u4e00\u6761 n = %r" % nm)
    # \u627e index \u91cc\u5bf9\u5e94\u7b2c\u4e00\u6761\u7684\u952e
    hit = [k for k in idx if nm in k or k in nm][:3]
    print("index \u4e2d\u4e0e n \u76f8\u5173\u7684\u952e = %s" % hit)
    # index \u7684\u6700\u5927\u503c
    print("index \u6700\u5927\u503c = %d" % max(idx.values()))
