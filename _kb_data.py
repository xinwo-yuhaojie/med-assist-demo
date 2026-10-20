# -*- coding: utf-8 -*-
"""v44\uff1a\u4ece _kb_new_drugs.py \u91cc\u63d0\u53d6 NEW \u6570\u636e\uff08\u4e0d\u6267\u884c\u5176\u4ed6\u903b\u8f91\uff09\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SRC = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\_kb_new_drugs.py"
src = io.open(SRC, encoding="utf-8").read()
# \u53d6 NEW = [ ... ] \u8fd9\u4e00\u6bb5
m = re.search(r"NEW = \[(.*?)\n\]\n", src, re.S)
assert m, "NEW \u672a\u627e\u5230"
ns = {}
exec(compile("def D(n,c,u,x,a,t,d,f):\n    return {'n':n,'c':c,'u':u,'x':x,'a':a,'t':t,'d':d,'f':f}\n"
             "NEW = [" + m.group(1) + "\n]\n", "newdata", "exec"), ns)
NEW = ns["NEW"]
print("extracted %d drugs" % len(NEW))
for d in NEW:
    assert d["n"] and d["u"] and d["x"], d["n"]
    assert isinstance(d["a"], list) and isinstance(d["t"], list)
    assert isinstance(d["d"], list) and isinstance(d["f"], list)
print("all entries well-formed")
