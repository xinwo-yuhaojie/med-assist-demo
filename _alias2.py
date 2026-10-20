# -*- coding: utf-8 -*-
"""v44\uff1a\u7ed9 4 \u4e2a\u65b0\u6162\u75c5\u8865\u522b\u540d\uff08\u6309 key \u5b9a\u4f4d\uff09\uff0c\u7136\u540e\u8865 kb.js\u3002"""
import io
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site"
LOG = []

# ================= 1) \u6162\u75c5\u522b\u540d =================
P = BASE + r"\index.html"
raw = io.open(P, encoding="utf-8", newline="").read()
CRLF = "\r\n" in raw
t = raw.replace("\r\n", "\n")

ALIAS = {
    "osteoarthritis": "    alias: ['\u5173\u8282\u708e', '\u9aa8\u5173\u8282\u708e'],",
    "knee_osteoarthritis": "    alias: ['\u819d\u5173\u8282\u708e', '\u819d\u5173\u8282\u82af\u53d1\u708e'],",
    "chronic_bronchitis": "    alias: ['\u6162\u6027\u652f\u6c14\u7ba1\u708e', '\u8001\u6162\u54b3'],",
    "chronic_gastritis": "    alias: ['\u6162\u6027\u6d3b\u52a8\u6027\u80c3\u708e', '\u80c3\u708e'],",
}
for key, al in ALIAS.items():
    pat = re.compile(r"(key: '%s',[^\n]*\n)" % re.escape(key))
    m = pat.search(t)
    if not m:
        LOG.append("  FAIL key %s \u672a\u627e\u5230" % key)
        continue
    t = t[:m.end(1)] + al + "\n" + t[m.end(1):]
    LOG.append("  OK   alias + %s" % key)

out = t.replace("\n", "\r\n") if CRLF else t
io.open(P, "w", encoding="utf-8", newline="").write(out)

# ================= 2) kb.js \u8865\u5145 =================
exec(open(BASE + r"\_kb_new_drugs.py", encoding="utf-8").read())
