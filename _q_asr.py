# -*- coding: utf-8 -*-
"""v44\uff1a\u67e5\u4e24\u4e2a\u95ee\u9898\uff1a\u2460 \u65b9\u8a00\u652f\u6301\u8303\u56f4\uff08\u542b\u6d59\u5c3e\u8bdd\uff09\u2461 ASR/TTS \u6bcf\u65e5\u9650\u9891\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
F = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\index.html"
B = r"D:\网站专用\网站式老人慢性病用药辅助智能体\backend\fc-web\server.js"
FL = io.open(F, encoding="utf-8").read().split("\n")
BL = io.open(B, encoding="utf-8").read().split("\n")

print("### \u2460 \u524d\u7aef\u65b9\u8a00\u767d\u540d\u5355")
for i, l in enumerate(FL, 1):
    s = l.strip()
    if re.search(r"DIALECT|currentDialect|dialectList|\u65b9\u8a00", s) and len(s) < 200:
        print("%5d| %s" % (i, s[:150]))

print("\n### \u2460b \u540e\u7aef\u65b9\u8a00\u5904\u7406")
for i, l in enumerate(BL, 1):
    s = l.strip()
    if re.search(r"DIALECT|dialect|diaVoice", s) and len(s) < 200:
        print("%5d| %s" % (i, s[:150]))

print("\n### \u2461 \u6bcf\u65e5\u9650\u9891\uff08\u524d\u7aef\uff09")
for i, l in enumerate(FL, 1):
    s = l.strip()
    if re.search(r"todayCount|dailyCount|perDay|dailyLimit|\u6bcf\u5929|quota|usedToday|todayUsed|limitOk|checkDaily", s) and len(s) < 200:
        print("%5d| %s" % (i, s[:150]))

print("\n### \u2461b \u6bcf\u65e5\u9650\u9891\uff08\u540e\u7aef\uff09")
for i, l in enumerate(BL, 1):
    s = l.strip()
    if re.search(r"dailyLimit|perDay|quota|\u6bcf\u65e5\u4e0a\u9650|DAILY_", s) and len(s) < 200:
        print("%5d| %s" % (i, s[:150]))

print("\n### \u2461c allowCall \u5b9e\u73b0\uff08\u9650\u6d41\u8868\uff09")
for i, l in enumerate(BL, 1):
    if "function allowCall" in l:
        for j in range(i - 1, min(len(BL), i + 26)):
            print("%5d| %s" % (j + 1, BL[j].rstrip()[:112]))
        break
