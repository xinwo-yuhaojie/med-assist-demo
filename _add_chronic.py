# -*- coding: utf-8 -*-
"""v44\uff1a\u65b0\u589e 4 \u79cd\u6162\u75c5\uff08\u9aa8\u5173\u8282\u82ef / \u819d\u9aa8\u5173\u8282\u82ef / \u6162\u6027\u652f\u6c14\u7ba1\u708e / \u6162\u6027\u80c3\u708e\uff09\uff0c
\u5e76\u628a\u65b0\u836f\u6302\u5230\u5bf9\u5e94\u6162\u75c5\u7684\u63a8\u8350\u7528\u836f\u91cc\u3002"""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site\index.html"
raw = io.open(P, encoding="utf-8", newline="").read()
CRLF = "\r\n" in raw
t = raw.replace("\r\n", "\n")
LOG = []
FAILED = []

# ---------- 1) \u65b0\u589e 4 \u79cd\u6162\u75c5 ----------
NEW = """  {
    key: 'osteoarthritis', name: '\u9aa8\u5173\u8282\u82ef', icon: '\U0001f9e0',
    cls: ['nsaid', 'cox2', 'analgesic'],
    monitor: '\u53d8\u5316\u524d\u540e\u5173\u8282\u75db\u3001\u6d3b\u52a8\u5ea6\u3001\u662f\u5426\u6709\u5c3a\u810a\u4f53\u3001\u5173\u8282\u80a0\u6d6e\u80ed',
    tips: '\u975e\u861a\u4f53\u6297\u708e\u836f\u80fd\u7f13\u89e3\u75db\u4f46\u4f1a\u4f24\u80a0\uff0c\u5e94\u4f18\u5148\u9009\u62e9\u5c3e\u90e8\u4f11\u606f\u3001\u51cf\u91cd\u3001\u6e2f\u5c3e\u7b49\u975e\u836f\u7269\u6d4b\u7a0b\uff1b\u82e5\u540c\u65f6\u7528\u963f\u53f8\u6797\u679c\u548c\u7d20\u98df\u8d28\u62bd\u6837\uff0c\u5fc5\u987b\u544a\u77e5\u533b\u751f\u3002',
    drugs: ['ibuprofen', 'diclofenac', 'etoricoxib', 'paracetamol']
  },
  {
    key: 'knee_osteoarthritis', name: '\u819d\u9aa8\u5173\u8282\u82ef', icon: '\U0001f97f',
    cls: ['nsaid', 'cox2', 'analgesic'],
    monitor: '\u4e0a\u697c\u4e0b\u697c\u65f6\u819d\u75db\u3001\u4e0b\u697c\u9700\u4e0d\u9700\u8981\u505c\u4e0b\u89c9\u4f11\u3001\u5173\u8282\u662f\u5426\u7ea2\u80bf\u70ed',
    tips: '\u819d\u5173\u8282\u82ef\u591a\u8d85\u91cd\uff0c\u964d\u91cd\u3001\u589e\u52a0\u808c\u529b\u3001\u6c34\u6ee9\u6c60\u5f88\u91cd\u8981\uff1b\u4e0a\u697c\u53ef\u7528\u5fae\u659c\u68af\u6216\u5750\u4f4d\u7f13\u51b2\u907f\u514d\u819d\u4f53\u53d7\u529b\uff1b\u4e00\u65e6\u5173\u8282\u7ea2\u80fd\u5feb\u3001\u81ea\u53d1\u70ed\u6216\u6d3b\u52a8\u9700\u9650\u5230\u5c3d\u5feb\u5c31\u533b\u3002',
    drugs: ['ibuprofen', 'diclofenac', 'etoricoxib', 'paracetamol']
  },
  {
    key: 'chronic_bronchitis', name: '\u6162\u6027\u652f\u6c14\u7ba1\u708e', icon: '\U0001fa81',
    cls: ['bronchodilator'],
    monitor: '\u75db\u6027\u54b3\u55fd\u3001\u75f4\u5916\u6392\u51fa\u3001\u547c\u5438\u56f0\u97f3\u4e0e\u52a8\u4f5c\u540e\u6c14\u77ed\uff1b\u6709\u65e0\u53d1\u70e7\u3001\u75f4\u4e2d\u5e26\u8840',
    tips: '\u5e73\u65f6\u51fa\u4e0a\u80a4\u529b\u6d3b\u52a8\u3001\u505a\u64fa\u547c\u7ec3\u4e60\u3001\u591a\u559d\u6e29\u6c34\uff1b\u5c4f\u6bcf\u3001\u70df\u96fe\u3001\u51b7\u98ce\u662f\u5178\u578b\u8bf1\u53d1\u56e0\u7d20\uff1b\u5e38\u7528\u4f53\u6d3b\u529b\u5242\u5e94\u5728\u75c5\u51b2\u52a0\u91cd\u65f6\u6309\u533b\u907f\u4f7f\u7528\uff0c\u4e0d\u8981\u81ea\u884c\u52a0\u91cf\u3002',
    drugs: ['doxofylline']
  },
  {
    key: 'chronic_gastritis', name: '\u6162\u6027\u80c3\u708e', icon: '\U0001f964',
    cls: ['ppi', 'antacid'],
    monitor: '\u4e0a\u80c3\u95f8\u75db\u3001\u80c3\u9178\u3001\u9ed1\u5c31\u3001\u996e\u540e\u4e0d\u9002\uff1b\u5927\u4fbf\u662f\u5426\u5e26\u8840\u3001\u662f\u5426\u4f53\u91cd\u4e0b\u964d',
    tips: '\u6297\u9178\u836f\uff08PPI\uff09\u901a\u5e38\u5728\u65e9\u9910\u524d\u534a\u5c0f\u65f6\u670d\u7528\uff0c\u4e00\u6b21\u7528\u4e8b\u524d\u670d\u7528\u4e00\u6b21\uff0c\u4e0d\u8981\u968f\u610f\u505c\u6b62\uff1b\u907f\u514d\u975e\u6614\u98df\u7528\u54ac\u3001\u6fc0\u6fc0\u8336\u3001\u9152\u7cbe\u548c\u8fc7\u70ed\u98df\u7269\uff1b\u5176\u5b9e\u4e3a\u4e0d\u53ef\u64a4\u9500\u7684\u4e0d\u826f\u4e60\u60ef\uff0c\u4e0d\u8981\u81ea\u5df1\u957f\u671f\u5403\u6297\u9178\u836f\u3002',
    drugs: ['omeprazole']
  },
"""
anchor = "  {\n    key: 'other', name: '\u5176\u4ed6\u57fa\u7840\u75c5'"
i = t.find(anchor)
if i < 0:
    FAILED.append("other \u6162\u75c5\u672a\u627e\u5230")
else:
    t = t[:i] + NEW + t[i:]
    LOG.append("  OK   \u65b0\u589e 4 \u79cd\u6162\u75c5")

# ---------- 2) \u628a\u65b0\u836f\u6302\u5230\u73b0\u6709\u6162\u75c5 ----------
ADD = {
    "hypertension": "    drugs: ['amlodipine', 'valsartan', 'benazepril', 'metoprolol', 'hydrochlorothiazide', 'irbesartan', 'telmisartan']",
    "diabetes": "    drugs: ['metformin', 'acarbose', 'glimepiride', 'gliclazide']",
    "lipid": "    drugs: ['atorvastatin', 'simvastatin']",
    "ckd": None,   # ckd \u7684 drugs \u5b57\u7b26\u4e32\u9700\u5355\u72ec\u627e
}
OLD = {
    "hypertension": "    drugs: ['amlodipine', 'valsartan', 'benazepril', 'metoprolol', 'hydrochlorothiazide']",
    "diabetes": "    drugs: ['metformin', 'acarbose', 'glimepiride']",
    "lipid": "    drugs: ['atorvastatin']",
}
for k, old in OLD.items():
    if t.count(old) == 1:
        t = t.replace(old, ADD[k])
        LOG.append("  OK   %s drugs += " % k)
    else:
        FAILED.append("%s drugs \u672a\u5339\u914d (%d)" % (k, t.count(old)))

# ckd\uff1a\u5728\u5b83\u7684 drugs \u884c\u91cc\u8865
import re
m = re.search(r"(key: 'ckd'.*?\n    drugs: \[)([^\]]*)(\])", t, re.S)
if m:
    cur = m.group(2)
    add = "', 'ureaclear', 'ketoacid"
    if "'ureaclear'" not in cur:
        t = t[:m.start(2)] + cur.rstrip() + add + t[m.end(2):]
        LOG.append("  OK   ckd drugs += ureaclear/ketoacid")
    else:
        LOG.append("  SKIP ckd drugs \u5df2\u6709")
else:
    FAILED.append("ckd drugs \u672a\u627e\u5230")

# ---------- 3) \u7cd6\u5c3f\u75c5\u540d\u79f0\uff1a\u7cd6\u5c3f\u75c5 -> 2\u578b\u7cd6\u5c3f\u75c5 ----------
old_dm = "key: 'diabetes', name: '\u7cd6\u5c3f\u75c5'"
new_dm = "key: 'diabetes', name: '2\u578b\u7cd6\u5c3f\u75c5'"
if t.count(old_dm) == 1:
    t = t.replace(old_dm, new_dm)
    LOG.append("  OK   \u7cd6\u5c3f\u75c5 \u2192 2\u578b\u7cd6\u5c3f\u75c5")
else:
    FAILED.append("diabetes name \u672a\u5339\u914d (%d)" % t.count(old_dm))

if FAILED:
    print("\n".join(LOG))
    print("\u5931\u8d25\uff08\u672a\u5199\u6587\u4ef6\uff09: " + "; ".join(FAILED))
    sys.exit(1)

out = t.replace("\n", "\r\n") if CRLF else t
io.open(P, "w", encoding="utf-8", newline="").write(out)
print("\n".join(LOG))
print("bytes = %d" % len(out.encode("utf-8")))
