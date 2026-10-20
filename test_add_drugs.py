# -*- coding: utf-8 -*-
"""v44\uff1a\u52a0\u836f/\u52a0\u6162\u75c5\u7684\u529f\u80fd\u9a8c\u8bc1\uff08\u5168\u90e8\u7528\u771f\u5b9e\u4e2d\u6587\u65ad\u8a00\uff0c\u4e0d\u7528\u7801\u4f4d\u8f6c\u4e49\uff09\u3002"""
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site"
OK = [True]


def ck(d, c, e=""):
    print(("  PASS  " if c else "  FAIL  ") + d + (("  -> " + str(e)) if e else ""))
    OK[0] = OK[0] and bool(c)


# \u7528\u6237\u7ed9\u7684 22 \u4e2a\u836f\u540d\uff08\u542b\u5242\u578b\uff09
USER_DRUGS = [
    "苯磺酸氨氯地平片", "缬沙坦片", "二甲双胍缓释片", "格列齐特缓释片", "厄贝沙坦片",
    "硝苯地平缓释片", "双氯芬酸钠缓释片", "阿司匹林肠溶片", "辛伐他汀片", "单硝酸异山梨酯片",
    "美托洛尔缓释片", "多索茶碱片", "二甲双胍片", "阿卡波糖片", "依托考昔片",
    "贝那普利片", "氢氯噻嗪片", "尿毒清颗粒", "复方α-酮酸片", "布洛芬缓释胶囊",
    "替米沙坦片", "奥美拉唑肠溶胶囊",
]
USER_CHRONIC = ["高血压", "2型糖尿病", "骨关节炎", "冠心病", "高血脂",
                "慢性支气管炎", "膝骨关节炎", "慢性胃炎"]
NEW_DRUG_IDS = ["gliclazide", "irbesartan", "diclofenac", "simvastatin", "doxofylline",
                "etoricoxib", "ureaclear", "ketoacid", "telmisartan"]
NEW_CHRONIC_KEYS = ["osteoarthritis", "knee_osteoarthritis", "chronic_bronchitis", "chronic_gastritis"]
KB_NEW = ["氨氯地平", "缬沙坦", "厄贝沙坦", "替米沙坦", "硝苯地平", "阿司匹林肠溶片",
          "辛伐他汀", "单硝酸异山梨酯", "多索茶碱", "依托考昔", "双氯芬酸钠缓释片",
          "氢氯噻嗪", "尿毒清颗粒", "复方α-酮酸片", "奥美拉唑肠溶胶囊"]

html = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
m = re.search(r"EMC\.DRUGS = \[(.*?)\n\];", html, re.S)
assert m, "DRUGS 未找到"
drugs_src = m.group(1)
m2 = re.search(r"EMC\.CHRONIC_DISEASES = \[(.*?)\n\];", html, re.S)
assert m2, "CHRONIC_DISEASES 未找到"
chronic_src = m2.group(1)
mf = re.search(r"function normDrugForm\(s\) \{.*?\n  \}", html, re.S)
mm = re.search(r"function matchDrugByName\(name\) \{.*?\n  \}\n", html, re.S)
assert mf and mm, "匹配函数未找到"

JS = """
var EMC = { DRUGS: [] };
var DRUGS = %s;
var CHRONIC = %s;
%s
%s
EMC.DRUGS = DRUGS;
var out = { hits: [], chronic: [], drugIds: [] };
var T = %s;
T.forEach(function(nm){ var h = matchDrugByName(nm); out.hits.push([nm, h ? h.id : null]); });
out.chronic = CHRONIC.map(function(c){ return [c.key, c.name]; });
out.drugIds = DRUGS.map(function(d){ return d.id; });
console.log(JSON.stringify(out));
""" % ("[" + drugs_src + "]", "[" + chronic_src + "]", mf.group(0), mm.group(0),
       json.dumps(USER_DRUGS, ensure_ascii=False))

p = os.path.join(ROOT, "_adddrugs_test.js")
io.open(p, "w", encoding="utf-8").write(JS)
r = subprocess.run([r"D:\hclaw\node\node.exe", p], capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=60)
try:
    os.remove(p)
except Exception:
    pass
if not (r.stdout or "").strip():
    print("node 无输出: %s" % (r.stderr or "")[:400])
    sys.exit(1)
d = json.loads(r.stdout.strip().splitlines()[-1])

print("=== ① 用户给的 22 个药名（含剂型）能命中 ===")
miss = [nm for nm, hid in d["hits"] if not hid]
ck("全部 22 个命中", not miss, "未命中: %s" % miss)
for nm, hid in d["hits"]:
    print("       %-16s -> %s" % (nm, hid))

print("\n=== ② 新增 9 种药在 EMC.DRUGS 里 ===")
ids = d["drugIds"]
for i in NEW_DRUG_IDS:
    ck("id %s 存在" % i, i in ids)
ck("DRUGS 总数 = 34（25+9）", len(ids) == 34, len(ids))
names_by_id = dict(re.findall(r"id: '([^']+)', name: '([^']+)'", drugs_src))
EXPECT = {"gliclazide": "格列齐特缓释片", "irbesartan": "厄贝沙坦片",
          "diclofenac": "双氯芬酸钠缓释片", "simvastatin": "辛伐他汀片",
          "doxofylline": "多索茶碱片", "etoricoxib": "依托考昔片",
          "ureaclear": "尿毒清颗粒", "ketoacid": "复方α-酮酸片",
          "telmisartan": "替米沙坦片"}
for k, v in EXPECT.items():
    ck("%s 的中文名正确" % k, names_by_id.get(k) == v, names_by_id.get(k))

print("\n=== ③ 用户给的 8 种慢病都在 ===")
cnames = [n for k, n in d["chronic"]]
aliases = re.findall(r"alias:\s*\[([^\]]*)\]", chronic_src)
alias_all = [x for g in aliases for x in re.findall(r"'([^']*)'", g)]
for n in USER_CHRONIC:
    ck("慢病 %s" % n, (n in cnames) or (n in alias_all), cnames)

print("\n=== ④ 慢病 key 齐全 ===")
ckeys = [k for k, n in d["chronic"]]
for k in NEW_CHRONIC_KEYS:
    ck("key %s" % k, k in ckeys)

print("\n=== ⑤ 慢病的推荐药 id 都存在 ===")
bad = []
for mm2 in re.finditer(r"drugs:\s*\[([^\]]*)\]", chronic_src):
    for did in re.findall(r"'([^']+)'", mm2.group(1)):
        if did not in ids:
            bad.append(did)
ck("无悬空的药 id", not bad, bad)

print("\n=== ⑥ kb.js 新增 15 条手册条目 ===")
kb = io.open(os.path.join(ROOT, "kb.js"), encoding="utf-8").read()
kbn = re.findall(r'"n":"([^"]+)"', kb)
ck("kb.js 条目数 = 1605", len(kbn) == 1605, len(kbn))
for nm in KB_NEW:
    ck("kb 含 %s" % nm, nm in kbn)
idx = dict(re.findall(r'"([^"]+)":\s*(\d+)', kb[kb.find("idx"):]))
for nm in ["氨氯地平", "厄贝沙坦", "多索茶碱", "尿毒清颗粒", "复方α-酮酸片"]:
    ck("kb idx 含 %s" % nm, nm.lower() in idx)

print("\n" + ("全部通过" if OK[0] else "有失败"))
sys.exit(0 if OK[0] else 1)
