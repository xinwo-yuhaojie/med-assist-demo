# -*- coding: utf-8 -*-
"""v44\uff1a\u4fee kb.js \u7684 idx \u95ed\u5408\u62ec\u53f7\u88ab\u8bef\u5220\u7684\u95ee\u9898\uff0c\u5e76\u6821\u9a8c\u6574\u4e2a\u6587\u4ef6\u8bed\u6cd5\u3002"""
import io
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KB = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\kb.js"
kb = io.open(KB, encoding="utf-8").read()

# \u53d1\u73b0\u7f3a\u5931\u7684\u95ed\u5408\u62ec\u53f7\uff1a\u7528 node --check \u76f4\u63a5\u8bca\u65ad
p = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\_kbcheck.js"
io.open(p, "w", encoding="utf-8").write(kb)
r = subprocess.run([r"D:\hclaw\node\node.exe", "--check", p], capture_output=True, text=True)
print("node --check: rc=%d" % r.returncode)
if r.returncode != 0:
    print((r.stderr or "")[:600])

# \u627e idx \u7684\u7ed3\u675f\u62ec\u53f7\uff1a\u4ece\u5f00\u5934\u62ec\u53f7\u914d\u5bf9
m = re.search(r"\bidx\s*:\s*\{", kb)
assert m, "idx \u672a\u627e\u5230"
k2 = kb.find("{", m.start())
depth = 0
m2 = k2
while m2 < len(kb):
    if kb[m2] == "{":
        depth += 1
    elif kb[m2] == "}":
        depth -= 1
        if depth == 0:
            break
    m2 += 1
print("idx \u5bf9\u8c61\u7ed3\u675f\u4f4d\u7f6e = %d, \u5b57\u7b26 = %r" % (m2, kb[m2 - 3:m2 + 3]))
# \u82e5\u7ed3\u675f\u62ec\u53f7\u540e\u9762\u4e0d\u662f "};" \u6216 " }" \u7b49\uff0c\u8bf4\u660e\u88ab\u5220\u4e86
tail = kb[m2:m2 + 12]
print("idx \u4e4b\u540e = %r" % tail)
if not re.match(r"\s*\}", tail):
    # \u8865\u56de\u95ed\u5408\u62ec\u53f7
    kb = kb[:m2] + "}" + kb[m2:]
    io.open(KB, "w", encoding="utf-8", newline="").write(kb)
    print("  OK   \u5df2\u8865\u56de idx \u95ed\u5408\u62ec\u53f7")
else:
    print("  --   \u65e0\u9700\u4fee\u590d")

# \u518d\u6b21\u6821\u9a8c
kb2 = io.open(KB, encoding="utf-8").read()
io.open(p, "w", encoding="utf-8").write(kb2)
r2 = subprocess.run([r"D:\hclaw\node\node.exe", "--check", p], capture_output=True, text=True)
print("node --check (2): rc=%d" % r2.returncode)
if r2.returncode != 0:
    print((r2.stderr or "")[:600])
try:
    import os
    os.remove(p)
except Exception:
    pass
names = set(re.findall(r'"n":"([^"]+)"', kb2))
print("kb.js \u6761\u76ee\u6570 = %d" % len(names))
for nm in ["\u6c28\u6c2f\u5730\u5e73", "\u4f26\u8d1d\u6c99\u6a3f", "\u591a\u7d22\u8336\u78b1", "\u5c3f\u6bd2\u6e05\u9887\u7c92"]:
    print("  %s: %s" % (nm, nm in names))
