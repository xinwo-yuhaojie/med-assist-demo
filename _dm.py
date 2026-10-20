# -*- coding: utf-8 -*-
"""v44\uff1a\u53ea\u5728 EMC.CHRONIC_DISEASES \u5757\u5185\u628a diabetes \u7684 name \u6539\u4e3a 2\u578b\u7cd6\u5c3f\u75c5\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\index.html"
raw = io.open(P, encoding="utf-8", newline="").read()
CRLF = "\r\n" in raw
t = raw.replace("\r\n", "\n")

m = re.search(r"EMC\.CHRONIC_DISEASES = \[.*?\n\];", t, re.S)
assert m, "CHRONIC_DISEASES \u672a\u627e\u5230"
blk = m.group(0)
old = "key: 'diabetes', name: '\u7cd6\u5c3f\u75c5'"
new = "key: 'diabetes', name: '2\u578b\u7cd6\u5c3f\u75c5'"
n = blk.count(old)
print("block \u5185\u5339\u914d = %d" % n)
if n == 1:
    nb = blk.replace(old, new)
    t = t[:m.start()] + nb + t[m.end():]
    out = t.replace("\n", "\r\n") if CRLF else t
    io.open(P, "w", encoding="utf-8", newline="").write(out)
    print("  OK   diabetes -> 2\u578b\u7cd6\u5c3f\u75c5")
    print("bytes = %d" % len(out.encode("utf-8")))
else:
    print("  FAIL \u672a\u5199\u6587\u4ef6")

# \u770b chronicKeyOf \u7684\u5b9e\u73b0\uff08\u786e\u8ba4\u65e7\u540d\u300c\u7cd6\u5c3f\u75c5\u300d\u4ecd\u80fd\u6620\u5c04\uff09
L = t.split("\n")
for i, l in enumerate(L, 1):
    if "EMC.chronicKeyOf = function" in l:
        print("\n### chronicKeyOf")
        for j in range(i - 1, min(len(L), i + 12)):
            print("%5d| %s" % (j + 1, L[j].rstrip()[:110]))
        break
