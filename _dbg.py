# -*- coding: utf-8 -*-
"""v44\uff1a\u5b9a\u4f4d\u300c\u4f26\u8d1d\u6c99\u6a3f\u300d\u5728\u6587\u4ef6\u91cc\u7684\u5b9e\u9645\u5199\u6cd5\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site"

t = io.open(ROOT + r"\index.html", encoding="utf-8").read()
print("### index.html \u4e2d irbesartan \u9644\u8fd1")
i = t.find("id: 'irbesartan'")
print(repr(t[i:i + 120]) if i > 0 else "  NOT FOUND")

print("\n### index.html \u4e2d\u6240\u6709 id + name\uff08\u65b0\u589e\u90e8\u5206\uff09")
m = re.search(r"EMC\.DRUGS = \[(.*?)\n\];", t, re.S)
for mm in re.finditer(r"id: '([^']+)', name: '([^']+)'", m.group(1)):
    if mm.group(1) in ("gliclazide", "irbesartan", "diclofenac", "simvastatin", "doxofylline",
                       "etoricoxib", "ureaclear", "ketoacid", "telmisartan"):
        print("  %-14s name=%r" % (mm.group(1), mm.group(2)))

print("\n### kb.js \u4e2d\u542b\u300c\u6c99\u6a3f\u300d\u7684\u6761\u76ee")
kb = io.open(ROOT + r"\kb.js", encoding="utf-8").read()
for nm in re.findall(r'"n":"([^"]+)"', kb):
    if "\u6c99\u6a3f" in nm or "\u4f26" in nm:
        print("  %r" % nm)
print("  (kb \u91cc\u542b\u300c\u4f26\u300d\u7684\u6761\u76ee\u6570 = %d)"
      % len([n for n in re.findall(r'"n":"([^"]+)"', kb) if "\u4f26" in n]))

print("\n### \u6bd4\u5bf9\uff1aNEW \u6570\u636e\u91cc\u7684\u540d\u5b57")
src = io.open(ROOT + r"\_kb_new_drugs.py", encoding="utf-8").read()
for mm in re.finditer(r"D\(\"([^\"]+)\",", src):
    print("  %r" % mm.group(1))
