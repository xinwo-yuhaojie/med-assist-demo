# -*- coding: utf-8 -*-
"""v44\uff1a\u68c0\u67e5 kb.js \u91cc\u662f\u5426\u5df2\u6709\u76ee\u6807\u836f\u7269\u6761\u76ee\uff08\u7528\u57fa\u7840\u540d\u641c\uff09\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\kb.js"
kb = io.open(P, encoding="utf-8").read()

names = set(re.findall(r'"n":"([^"]+)"', kb))
print("kb.js \u836f\u540d\u6761\u76ee\u6570 = %d" % len(names))

TARGETS = [
    ("\u6c2f\u8389\u5730\u5e73", "\u82ef\u786b\u9178\u6c28\u6c34\u5730\u5e73\u7247"),
    ("\u7f2c\u6c99\u6c9f", "\u7f2c\u6c99\u6c9f\u7247"),
    ("\u4e8c\u7532\u53cc\u80cd", "\u4e8c\u7532\u53cc\u80cd\u7f13\u91ca\u7247"),
    ("\u683c\u5217\u9f50\u7279", "\u683c\u5217\u9f50\u7279\u7f13\u91ca\u7247"),
    ("\u4f26\u8d1d\u6c99\u6c9f", "\u4f26\u8d1d\u6c99\u6c9f\u7247"),
    ("\u7855\u82ac\u5730\u5e73", "\u7855\u82ac\u5730\u5e73\u7f13\u91ca\u7247"),
    ("\u53cc\u6c2f\u82ac\u9178\u94a0", "\u53cc\u6c2f\u82ac\u9178\u94a0\u7f13\u91ca\u7247"),
    ("\u963f\u53f8\u6797\u80a0\u6eb6\u7247", "\u963f\u53f8\u6797\u80a0\u6eb6\u7247"),
    ("\u8f9b\u4f8b\u4ed6\u6ed9", "\u8f9b\u4f8b\u4ed6\u6ed9\u7247"),
    ("\u5355\u5de5\u9178\u5f02\u5c71\u68a0\u916f", "\u5355\u5de5\u9178\u5f02\u5c71\u68a0\u916f\u7247"),
    ("\u7f8e\u6258\u6d1b\u5c14", "\u7f8e\u6258\u6d1b\u5c14\u7f13\u91ca\u7247"),
    ("\u591a\u7d22\u8336\u78b1", "\u591a\u7d22\u8336\u78b1\u7247"),
    ("\u963f\u5361\u6ce2\u7cd6", "\u963f\u5361\u6ce2\u7cd6\u7247"),
    ("\u4f9d\u6258\u8003\u661e", "\u4f9d\u6258\u8003\u661e\u7247"),
    ("\u8d1d\u90a3\u666e\u5229", "\u8d1d\u90a3\u666e\u5229\u7247"),
    ("\u6c22\u6c2f\u5586\u5648", "\u6c22\u6c2f\u5586\u5648\u7247"),
    ("\u5c3f\u6bd2\u6e05", "\u5c3f\u6bd2\u6e05\u9887\u7c92"),
    ("\u916e\u9178", "\u590d\u65b9\u03b1-\u916e\u9178\u7247"),
    ("\u5e03\u6d1b\u82ac", "\u5e03\u6d1b\u82ac\u7f13\u91ca\u80f6\u56ca"),
    ("\u66ff\u7c73\u6c99\u6a3f", "\u66ff\u7c73\u6c99\u6a3f\u7247"),
    ("\u5965\u7f8e\u62c9\u5521", "\u5965\u7f8e\u62c9\u5521\u80a0\u6eb6\u80f6\u56ca"),
]
need = []
for base, full in TARGETS:
    if base in names:
        print("  [v] %-14s \u5df2\u6709" % full)
    else:
        part = sorted([n for n in names if base in n or (len(n) >= 3 and n in base)])[:3]
        if part:
            print("  [~] %-14s \u90e8\u5206\u5339\u914d: %s" % (full, part))
        else:
            print("  [x] %-14s \u7f3a\u5c11" % full)
            need.append((base, full))
print("\n\u9700\u8981\u5411 kb.js \u8865\u5145: %d \u6761" % len(need))
for b, f in need:
    print("   %s" % f)
