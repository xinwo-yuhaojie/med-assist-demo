# -*- coding: utf-8 -*-
"""v44\uff1a\u8bca\u65ad kb.js \u6761\u76ee\u6570\u4e0d\u5bf9 + \u4e2d\u6587\u66ff\u6362\u672a\u751f\u6548\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KB = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\kb.js"
kb = io.open(KB, encoding="utf-8").read()

print("len = %d" % len(kb))
print('"n":" \u603b\u6570 = %d' % kb.count('"n":"'))
# \u65b0\u589e\u7684 15 \u6761\u662f\u5426\u5728
NEWS = ["氨氯地平", "缬沙坦", "厄贝沙坦", "替米沙坦", "硝苯地平", "阿司匹林肠溶片",
        "辛伐他汀", "单硝酸异山梨酯", "多索茶碱", "依托考昔", "双氯芬酸钠缓释片",
        "氢氯噻嗪", "尿毒清颗粒", "复方α-酮酸片", "奥美拉唑肠溶胶囊"]
for nm in NEWS:
    print("  %-18s %s" % (nm, ('"n":"%s"' % nm) in kb))

print("\n### \u9519\u8bef\u5199\u6cd5\u662f\u5426\u4ecd\u5728")
for bad in ["伦贝沙樿", "辛例他滙", "依托考昞", "尿毒清颇粒", "硕芬地平", "阿司林肠溶片",
            "氢氯喆噈", "缬沙沟", "单工酸异山梠酯", "奥美拉唡", "氯莉地平"]:
    print("  %-14s %d" % (bad, kb.count(bad)))

print("\n### \u5c3e\u90e8 300 \u5b57\u7b26")
print(repr(kb[-300:]))
