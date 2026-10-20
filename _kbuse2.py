# -*- coding: utf-8 -*-
"""v44\uff1a\u67e5 EMC.DRUGKB \u7684\u68c0\u7d22\u903b\u8f91\uff08\u786e\u8ba4\u65b0\u589e\u4e2d\u6587\u836f\u540d\u80fd\u88ab\u67e5\u5230\uff09\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\index.html"
L = io.open(P, encoding="utf-8").read().split("\n")
hits = [i for i, l in enumerate(L) if "EMC.DRUGKB" in l]
print("DRUGKB \u5f15\u7528\u884c = %s" % [h + 1 for h in hits])
for h in hits:
    print("\n--- L%d ---" % (h + 1))
    for j in range(max(0, h - 2), min(len(L), h + 26)):
        print("%5d| %s" % (j + 1, L[j].rstrip()[:112]))
