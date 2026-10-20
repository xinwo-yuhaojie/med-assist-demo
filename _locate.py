# -*- coding: utf-8 -*-
"""v44\uff1a\u7528\u4e0e check_inline_js.py \u4e00\u81f4\u7684\u5207\u6cd5\u5b9a\u4f4d\u9519\u8bef\u5757\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\index.html"
html = io.open(P, encoding="utf-8").read()
blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
print("blocks = %d" % len(blocks))
b = blocks[2]
L = b.split("\n")
print("block #3 lines = %d" % len(L))
for j in range(228, min(len(L), 246)):
    print("%4d| %s" % (j + 1, L[j][:116]))
print("--- } {  \u5947\u5f02\u76f8\u90bb ---")
for j, l in enumerate(L):
    if re.search(r"\}\s*\{", l):
        print("  >>> L%d: %r" % (j + 1, l[:110]))
