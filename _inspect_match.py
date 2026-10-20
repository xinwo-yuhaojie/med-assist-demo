# -*- coding: utf-8 -*-
"""v44\uff1a\u67e5 EMC.DRUGS \u7684\u5339\u914d\u903b\u8f91\uff08\u662f\u5426\u5904\u7406\u201c\u7247\u201d\u201c\u80f6\u56ca\u201d\u201c\u9897\u7c92\u201d\u7b49\u5242\u578b\u540e\u7f00\uff09\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\index.html"
L = io.open(P, encoding="utf-8").read().split("\n")

print("### EMC.DRUGS \u7684\u67e5\u627e/\u5339\u914d\u51fd\u6570")
for i, l in enumerate(L, 1):
    s = l.strip()
    if ("DRUGS" in s) and any(k in s for k in ("function", "=", "find", "match", "search")) \
            and "EMC.DRUGS = [" not in s and len(s) < 130:
        print("%5d| %s" % (i, s[:126]))

print("\n### \u6d89\u53ca DRUGS \u7684\u5173\u952e\u884c")
for i, l in enumerate(L, 1):
    if "EMC.DRUGS" in l:
        print("%5d| %s" % (i, l.strip()[:126]))
