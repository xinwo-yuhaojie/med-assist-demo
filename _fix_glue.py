# -*- coding: utf-8 -*-
"""v44\uff1a\u4fee EMC.DRUGS \u6570\u7ec4\u5c3e\u90e8\u7684 }  { \u7c98\u8fde\uff08\u5207\u7247\u8d8a\u754c\u9020\u6210\uff09\u3002"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\index.html"
raw = io.open(P, encoding="utf-8", newline="").read()
CRLF = "\r\n" in raw
t = raw.replace("\r\n", "\n")
LOG = []

# 1) }  {  ->  },\n  {
bad = "  }  {\n    id: 'gliclazide'"
good = "  },\n  {\n    id: 'gliclazide'"
n = t.count(bad)
if n == 1:
    t = t.replace(bad, good)
    LOG.append("  OK   }  {  ->  },  (n=%d)" % n)
else:
    LOG.append("  FAIL(%d) }  {" % n)

# 2) \u6570\u7ec4\u5c3e\u5c3e\u7684\u5c3e\u8ddf\u9017\u53f7\uff1a} ,\n\n];  ->  }\n];
bad2 = "  },\n\n];\n\n/* ---------- 3."
good2 = "  }\n];\n\n/* ---------- 3."
n2 = t.count(bad2)
if n2 == 1:
    t = t.replace(bad2, good2)
    LOG.append("  OK   \u53bb\u9664\u5c3e\u8ddf\u9017\u53f7")
else:
    LOG.append("  FAIL(%d) \u5c3e\u8ddf\u9017\u53f7" % n2)

# 3) \u6821\u9a8c\u4e2d\u6587\u662f\u5426\u6b63\u786e\uff08\u7528 \u8f6c\u4e49\u6bd4\u5bf9\uff0c\u4e0d\u770b\u63a7\u5236\u53f0\u663e\u793a\uff09
CHECKS = [
    ("id: 'irbesartan', name: '\u4f26\u8d1d\u6c99\u6a3f\u7247'", "irbesartan \u540d\u5b57"),
    ("id: 'gliclazide', name: '\u683c\u5217\u9f50\u7279\u7f13\u91ca\u7247'", "gliclazide \u540d\u5b57"),
    ("id: 'telmisartan', name: '\u66ff\u7c73\u6c99\u6a3f\u7247'", "telmisartan \u540d\u5b57"),
    ("id: 'simvastatin', name: '\u8f9b\u4f8b\u4ed6\u6ed9\u7247'", "simvastatin \u540d\u5b57"),
    ("id: 'doxofylline', name: '\u591a\u7d22\u8336\u78b1\u7247'", "doxofylline \u540d\u5b57"),
    ("id: 'etoricoxib', name: '\u4f9d\u6258\u8003\u661e\u7247'", "etoricoxib \u540d\u5b57"),
    ("id: 'diclofenac', name: '\u53cc\u6c2f\u82ac\u9178\u94a0\u7f13\u91ca\u7247'", "diclofenac \u540d\u5b57"),
    ("id: 'ureaclear', name: '\u5c3f\u6bd2\u6e05\u9887\u7c92'", "ureaclear \u540d\u5b57"),
    ("id: 'ketoacid', name: '\u590d\u65b9\u03b1-\u916e\u9178\u7247'", "ketoacid \u540d\u5b57"),
    ("\u78fa\u80c0\u7c7b\u5bb9\u6613\u5bfc\u81f4\u4f4e\u8840\u7cd6", "\u78fa\u80c0\u7c7b\u6b63\u5b57"),
    ("\u7f8e\u54cb\u54b4", "\u7f8e\u54cb\u54b4\u522b\u540d"),
    ("\u6c22\u6c2f\u5586\u5648\u7247", "\u6c22\u6c2f\u5586\u5648\u522b\u540d"),
    ("\u5e03\u6d1b\u82ac\u7f13\u91ca\u80f6\u56ca", "\u5e03\u6d1b\u82ac\u522b\u540d"),
]
for key, label in CHECKS:
    LOG.append(("  OK   " if key in t else "  FAIL ") + label)

out = t.replace("\n", "\r\n") if CRLF else t
io.open(P, "w", encoding="utf-8", newline="").write(out)
print("\n".join(LOG))
print("bytes = %d" % len(out.encode("utf-8")))
