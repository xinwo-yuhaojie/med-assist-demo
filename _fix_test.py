# -*- coding: utf-8 -*-
"""v44\uff1a\u4fee\u6d4b\u8bd5\u7684 set \u53bb\u91cd\u9519\u8bef + \u9ad8\u8102\u8840\u75c7\u663e\u793a\u540d\u6539\u4e3a\u9ad8\u8840\u8102\uff08\u4fdd\u7559\u533b\u5b66\u6b63\u5f0f\u540d\u4f5c\u522b\u540d\uff09\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site"
LOG = []

# ---- 1) \u6d4b\u8bd5\u811a\u672c\uff1a\u53bb\u91cd\u4f1a\u628a\u540c\u540d\u6761\u76ee\u5408\u5e76\u6389 ----
P = BASE + r"\test_add_drugs.py"
t = io.open(P, encoding="utf-8").read()
old = 'kbn = set(re.findall(r\'"n":"([^"]+)"\', kb))'
new = 'kbn = re.findall(r\'"n":"([^"]+)"\', kb)'
if t.count(old) == 1:
    t = t.replace(old, new)
    LOG.append("  OK   \u6d4b\u8bd5\u53bb\u91cd\u4fee\u6b63")
else:
    LOG.append("  FAIL \u6d4b\u8bd5\u53bb\u91cd (%d)" % t.count(old))
old2 = 'ck("kb.js \u6761\u76ee\u6570 = 1605", len(kbn) == 1605, len(kbn))'
new2 = 'ck("kb.js \u6761\u76ee\u6570 = 1605", len(kbn) == 1605, len(kbn))'
# \u9ad8\u8840\u8102\u7684\u540d\u79f0\u65ad\u8a00\uff1a\u540d\u79f0\u6216\u522b\u540d\u547d\u4e2d\u5373\u53ef
old3 = """for n in USER_CHRONIC:
    ck("\u6162\u75c5 %s" % n, n in cnames, cnames)"""
new3 = """aliases = re.findall(r"alias:\\s*\\[([^\\]]*)\\]", chronic_src)
alias_all = [x for g in aliases for x in re.findall(r"'([^']*)'", g)]
for n in USER_CHRONIC:
    ck("\u6162\u75c5 %s" % n, (n in cnames) or (n in alias_all), cnames)"""
if t.count(old3) == 1:
    t = t.replace(old3, new3)
    LOG.append("  OK   \u6162\u75c5\u65ad\u8a00\u542b\u522b\u540d")
io.open(P, "w", encoding="utf-8", newline="").write(t)

# ---- 2) lipid \u663e\u793a\u540d\uff1a\u9ad8\u8102\u8840\u75c7 \u2192 \u9ad8\u8840\u8102\uff08\u522b\u540d\u4fdd\u7559\u9ad8\u8102\u8840\u75c7\uff09 ----
P2 = BASE + r"\index.html"
raw = io.open(P2, encoding="utf-8", newline="").read()
CRLF = "\r\n" in raw
t2 = raw.replace("\r\n", "\n")
old4 = "key: 'lipid', name: '\u9ad8\u8102\u8840\u75c7'"
new4 = "key: 'lipid', name: '\u9ad8\u8840\u8102'"
if t2.count(old4) == 1:
    t2 = t2.replace(old4, new4)
    out = t2.replace("\n", "\r\n") if CRLF else t2
    io.open(P2, "w", encoding="utf-8", newline="").write(out)
    LOG.append("  OK   lipid \u663e\u793a\u540d \u2192 \u9ad8\u8840\u8102")
else:
    LOG.append("  FAIL lipid name (%d)" % t2.count(old4))

print("\n".join(LOG))
