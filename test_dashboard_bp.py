# -*- coding: utf-8 -*-
"""\u9a8c\u8bc1\u770b\u677f\u65b0\u589e\u7684\u8840\u538b/\u8840\u7cd6\u4e24\u5217\u80fd\u6b63\u786e\u6e32\u67d3\u3002

\u7528\u7ebf\u4e0a\u771f\u5b9e\u8fd4\u56de\u7684 perUser \u6570\u636e\u9a71\u52a8\uff0c\u628a dashboard.html \u91cc\u90a3\u6bb5\u6e32\u67d3\u4ee3\u7801
\u62c6\u51fa\u6765\u5728 node \u91cc\u8dd1\uff0c\u68c0\u67e5\u8f93\u51fa HTML \u91cc\u662f\u5426\u542b\u6709\u538b\u503c\u3001\u504f\u9ad8\u6807\u8bb0\u3001\u65e0\u6570\u636e\u65f6\u7684\u2014\u3002
\u7ebf\u4e0a\u4e0d\u53ef\u7528\u65f6\u56de\u9000\u5230\u5185\u7f6e\u7684\u771f\u5b9e\u6837\u672c\u6570\u636e\u3002"""
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site"
OK = [True]


def ck(d, c, e=""):
    print(("  PASS  " if c else "  FAIL  ") + d + (("  -> " + str(e)) if e else ""))
    OK[0] = OK[0] and bool(c)


# \u5185\u7f6e\u7684\u771f\u5b9e\u6837\u672c\uff08\u4ece\u7ebf\u4e0a\u6293\u5230\u7684 perUser \u771f\u5b9e\u6570\u636e\uff09
SAMPLE = [
    {"id": "19835955957", "name": "\u5f20\u4e00", "gender": "\u5973", "meds": 3, "rate7": 90,
     "missedToday": 0, "low": 0, "adrMild": 0, "adrSevere": 0,
     "bpCount": 1, "bpSys7": 135, "bpDia7": 88, "bpHigh": False,
     "bpLast": {"date": "2026-10-15", "time": "22:10", "sys": 135, "dia": 88},
     "gluCount": 1, "glu7": 7, "gluHigh": False},
    {"id": "18900823923", "name": "\u674e\u4e8c", "gender": "\u7537", "meds": 5, "rate7": 72,
     "missedToday": 1, "low": 1, "adrMild": 1, "adrSevere": 0,
     "bpCount": 3, "bpSys7": 150, "bpDia7": 95, "bpHigh": True,
     "bpLast": {"date": "2026-10-14", "time": "08:40", "sys": 135, "dia": 88},
     "gluCount": 1, "glu7": 12.5, "gluHigh": True},
    {"id": "\u543c\u543c\u543c", "name": "\u543c\u543c\u543c", "gender": "\u5973", "meds": 1, "rate7": 100,
     "missedToday": 0, "low": 0, "adrMild": 0, "adrSevere": 0,
     "bpCount": 1, "bpSys7": 75, "bpDia7": 40, "bpHigh": False,
     "bpLast": {"date": "2026-10-15", "time": "22:36", "sys": 75, "dia": 40},
     "gluCount": 0, "glu7": None, "gluHigh": False},
    {"id": "nobody", "name": "\u6ca1\u6570\u636e", "gender": "\u7537", "meds": 0, "rate7": None,
     "missedToday": 0, "low": 0, "adrMild": 0, "adrSevere": 0,
     "bpCount": 0, "bpSys7": None, "bpDia7": None, "bpHigh": False,
     "bpLast": None, "gluCount": 0, "glu7": None, "gluHigh": False},
]

per = None
B = "https://kangban-ai-cfcnpojddz.cn-beijing.fcapp.run"
for attempt in range(3):
    try:
        req = urllib.request.Request(B + "/api/admin/stats",
                                     data=json.dumps({"password": "123123123",
                                                      "communityPw": "123456789"}).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
        d = json.loads(urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace"))
        per = (d.get("stats") or {}).get("perUser") or []
        if per:
            break
    except Exception as e:
        print("  (\u7ebf\u4e0a\u62c9\u53d6\u5931\u8d25\uff0c\u5c1d\u8bd5 %d/3: %s)" % (attempt + 1, str(e)[:60]))
        time.sleep(3)
if not per:
    per = SAMPLE
    print("  (\u7ebf\u4e0a\u4e0d\u53ef\u7528\uff0c\u4f7f\u7528\u5185\u7f6e\u771f\u5b9e\u6837\u672c\u6570\u636e)")
else:
    print("\u7ebf\u4e0a perUser = %d \u4e2a\u8d26\u53f7" % len(per))

html = io.open(ROOT + r"\dashboard.html", encoding="utf-8").read()
m = re.search(r"var rate = p\.rate7.*?return '<tr>.*?</tr>';", html, re.S)
ck("\u627e\u5230\u770b\u677f\u6e32\u67d3\u4ee3\u7801\u6bb5", m is not None)
if not m:
    sys.exit(1)
code = m.group(0)

js = ("function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;')\n"
      ".replace(/>/g,'&gt;').replace(/\"/g,'&quot;').replace(/'/g,'&#39;');}\n"
      "var per = " + json.dumps(per, ensure_ascii=False) + ";\n"
      "function render(p, isMgr) {\n" + code + "\n}\n"
      "console.log(JSON.stringify(per.map(function(p){ return render(p,false); })));\n")

p = ROOT + r"\_dash_test.js"
io.open(p, "w", encoding="utf-8").write(js)
r = subprocess.run([r"D:\hclaw\node\node.exe", p], capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=60)
try:
    os.remove(p)
except Exception:
    pass
if not (r.stdout or "").strip():
    print("node \u65e0\u8f93\u51fa: %s" % (r.stderr or "")[:300])
    sys.exit(1)
rows = json.loads(r.stdout.strip().splitlines()[-1])

print("\n=== \u8868\u5934 ===")
th = re.findall(r"<th[^>]*>(.*?)</th>", html, re.S)
ck("\u8868\u5934\u6709\u8840\u538b\u5217", any("\u8840\u538b" in x for x in th), th)
ck("\u8868\u5934\u6709\u8840\u7cd6\u5217", any("\u8840\u7cd6" in x for x in th), th)

print("\n=== \u884c\u5185\u5bb9 ===")
ck("\u6bcf\u884c 9 \u4e2a\u5355\u5143\u683c", all(x.count("</td>") == 9 for x in rows),
   [x.count("</td>") for x in rows[:5]])
bp_rows = [x for x in rows if "\u00b7" in x and "/" in x]
ck("\u6709\u8840\u538b\u7684\u8d26\u53f7\u663e\u793a\u4e86\u5747\u503c", len(bp_rows) >= 1, len(bp_rows))
if bp_rows:
    print("     \u793a\u4f8b: " + bp_rows[0][:120])
    ck("\u6709\u300c\u6b21\u300d\u8ba1\u6570", "\u6b21" in bp_rows[0], bp_rows[0][:70])
ck("\u504f\u9ad8\u6807\u8bb0\u51fa\u73b0", any("\u504f\u9ad8" in x for x in rows),
   sum(1 for x in rows if "\u504f\u9ad8" in x))
ck("\u65e0\u6570\u636e\u7684\u8d26\u53f7\u663e\u793a \u2014", any("\u2014" in x for x in rows))
ck("\u65e0 XSS\uff1a\u884c\u5185\u65e0 script \u6807\u7b7e", all("<script" not in x.lower() for x in rows))

print("\n" + ("\u5168\u90e8\u901a\u8fc7" if OK[0] else "\u6709\u5931\u8d25"))
sys.exit(0 if OK[0] else 1)
