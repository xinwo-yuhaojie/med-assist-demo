# -*- coding: utf-8 -*-
"""v44\uff1akb.js \u8865\u5145\u7f3a\u5931\u7684 14 \u6761\u836f\u7269\u624b\u518c\u3002

\u6ce8\u610f\uff1akb.js \u91cc\u6709\u5355\u5f15\u53f7\u5b57\u7b26\u4e32\uff0c**\u4e0d\u662f\u4e25\u683c JSON**\uff0c\u4e0d\u80fd\u7528 json.dumps \u6574\u4f53\u91cd\u5199\u3002
\u91c7\u7528\u6700\u5c0f\u6539\u52a8\uff1a
  1) drugs \u6570\u7ec4\u672b\u5c3e\u63d2\u5165\u65b0\u6761\u76ee\uff08json.dumps \u751f\u6210\uff0c\u53cc\u5f15\u53f7\u5b89\u5168\uff09
  2) idx \u5bf9\u8c61\u672b\u5c3e\u63d2\u5165\u300c\u836f\u540d\u5c0f\u5199\u300d -> \u4e0b\u6807 \u6620\u5c04
  3) n \u8ba1\u6570\u52a0\u4e0a\u65b0\u589e\u6570
kbFindDrug \u7684\u68c0\u7d22\u5b8c\u5168\u4f9d\u8d56 KB.idx\uff08\u6ca1\u6709 drugs \u904d\u5386\u515c\u5e95\uff09\uff0c\u6240\u4ee5\u4e24\u8fb9\u5fc5\u987b\u540c\u6b65\u3002
"""
import io
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KB = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\kb.js"
kb = io.open(KB, encoding="utf-8").read()

import importlib.util
_sp = importlib.util.spec_from_file_location("kbdata", r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\_kb_data.py")
_m = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(_m)
NEW = _m.NEW

have = set(re.findall(r'"n":"([^"]+)"', kb))
add = [d for d in NEW if d["n"] not in have]
print("  \u5f85\u8865\u5145 = %d \u6761" % len(add))
if not add:
    print("  SKIP")
    sys.exit(0)

# ---- 1) drugs \u6570\u7ec4\u8fb9\u754c ----
i = kb.find("drugs: [")
depth = 0
j = i + 7
while j < len(kb):
    if kb[j] == "[":
        depth += 1
    elif kb[j] == "]":
        depth -= 1
        if depth == 0:
            break
    j += 1
assert kb[j] == "]", "drugs \u6570\u7ec4\u672a\u7ed3\u675f"
base = len(re.findall(r'"n":"([^"]+)"', kb[:j]))
print("  drugs \u539f\u6709 %d \u6761" % base)

# ---- 2) idx \u5bf9\u8c61\u8fb9\u754c ----
mi = re.search(r"\bidx\s*:\s*\{", kb[j:])
assert mi, "idx \u672a\u627e\u5230"
ks = j + mi.start()
k2 = kb.find("{", ks)
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
assert kb[m2] == "}", "idx \u672a\u7ed3\u675f"
idx_pairs = re.findall(r'"([^"]+)":\s*(\d+)', kb[k2:m2 + 1])
zh = [p for p in idx_pairs if any('\u4e00' <= ch <= '\u9fff' for ch in p[0])]
print("  idx \u6761\u76ee\u6570 = %d\uff08\u5176\u4e2d\u4e2d\u6587\u952e %d\uff09" % (len(idx_pairs), len(zh)))

# ---- 3) \u751f\u6210\u8ffd\u52a0\u6587\u672c ----
new_drugs = "," + ",".join(json.dumps(d, ensure_ascii=False, separators=(",", ":")) for d in add)
new_idx = "".join(',"%s":%d' % (d["n"].lower(), base + k) for k, d in enumerate(add))

# ---- 4) \u62fc\u63a5\uff08\u4ece\u540e\u9762\u6539\uff0c\u907f\u514d\u504f\u79fb\uff09 ----
out = kb[:j] + new_drugs + kb[j:m2] + new_idx + kb[m2:]
out = re.sub(r"(EMC\.DRUGKB = \{ n: )(\d+)", lambda mo: mo.group(1) + str(int(mo.group(2)) + len(add)), out, count=1)
io.open(KB, "w", encoding="utf-8", newline="").write(out)

# ---- 5) \u9a8c\u8bc1 ----
chk = io.open(KB, encoding="utf-8").read()
names2 = re.findall(r'"n":"([^"]+)"', chk)
m3 = re.search(r"\bidx\s*:\s*\{", chk[j:])
k3 = chk.find("{", j + m3.start())
depth = 0
m4 = k3
while m4 < len(chk):
    if chk[m4] == "{":
        depth += 1
    elif chk[m4] == "}":
        depth -= 1
        if depth == 0:
            break
    m4 += 1
pairs2 = dict(re.findall(r'"([^"]+)":\s*(\d+)', chk[k3:m4 + 1]))
print("  \u9a8c\u8bc1: drugs \u6761\u76ee\u6570 = %d\uff08\u5e94\u4e3a %d\uff09" % (len(names2), base + len(add)))
ok = True
for d in add:
    key = d["n"].lower()
    hit = key in pairs2 and int(pairs2[key]) < len(names2)
    if not hit:
        ok = False
        print("  FAIL idx \u7f3a %s" % key)
print("  \u9a8c\u8bc1: \u65b0\u836f\u5728 idx \u4e2d\u53ef\u67e5 = %s" % ("\u2713" if ok else "\u2717"))
print("  \u65b0\u589e: %s" % ", ".join(d["n"] for d in add))
