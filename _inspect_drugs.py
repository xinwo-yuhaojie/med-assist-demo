# -*- coding: utf-8 -*-
"""\u5217\u51fa EMC.DRUGS \u73b0\u6709\u6761\u76ee\u4e0e cls \u53d6\u503c\uff08\u4e0d\u7ecf PowerShell \u4e2d\u8f6c\uff09\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\index.html"
t = io.open(P, encoding="utf-8").read()

m = re.search(r"EMC\.DRUGS = \[(.*?)\n\];", t, re.S)
assert m, "DRUGS \u672a\u627e\u5230"
body = m.group(1)
recs = re.findall(r"id:\s*'([^']+)',\s*name:\s*'([^']+)',\s*alias:\s*\[([^\]]*)\],\s*"
                   r"cls:\s*'([^']*)',\s*cat:\s*'([^']*)',\s*dose:\s*'([^']*)',\s*best:\s*\[([^\]]*)\]", body)
print("\u73b0\u6709 EMC.DRUGS = %d \u6761" % len(recs))
for r in recs:
    al = re.findall(r"'([^']*)'", r[2])
    print("  %-16s %-16s cls=%-14s cat=%-10s best=%s" % (r[0], r[1], r[3], r[4], r[6]))

cls = sorted(set(r[3] for r in recs))
print("\n\u73b0\u6709 cls \u53d6\u503c: %s" % ", ".join(cls))
cats = sorted(set(r[4] for r in recs))
print("\u73b0\u6709 cat \u53d6\u503c: %s" % ", ".join(cats))

# \u5168\u5c40\u51fa\u73b0\u7684 cls \u5b57\u9762\u91cf\uff08\u542b\u6162\u75c5\u91cc\u5f15\u7528\u7684\uff09
allcls = sorted(set(re.findall(r"cls:\s*\[([^\]]*)\]", t) and
                     [x.strip().strip("'") for g in re.findall(r"cls:\s*\[([^\]]*)\]", t) for x in g.split(",")]))
print("\u9875\u9762\u4e2d\u7528\u5230\u7684 cls: %s" % ", ".join(allcls))
