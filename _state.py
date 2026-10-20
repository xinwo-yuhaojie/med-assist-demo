# -*- coding: utf-8 -*-
"""v44\uff1a\u76d8\u70b9 index.html / kb.js \u5f53\u524d\u7684\u6539\u52a8\u843d\u5730\u60c5\u51b5\u3002"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site"
t = io.open(ROOT + r"\index.html", encoding="utf-8").read()

m = re.search(r"EMC\.DRUGS = \[(.*?)\n\];", t, re.S)
ids = re.findall(r"id: '([^']+)'", m.group(1))
print("EMC.DRUGS = %d \u6761" % len(ids))
print("  \u65b0\u589e 9 \u6761\u662f\u5426\u5728: %s" % all(x in ids for x in
      ["gliclazide", "irbesartan", "diclofenac", "simvastatin", "doxofylline",
       "etoricoxib", "ureaclear", "ketoacid", "telmisartan"]))

m2 = re.search(r"EMC\.CHRONIC_DISEASES = \[(.*?)\n\];", t, re.S)
cks = re.findall(r"key: '([^']+)'", m2.group(1))
print("\nEMC.CHRONIC_DISEASES = %d \u6761: %s" % (len(cks), cks))
print("  \u65b0\u589e 4 \u6761\u662f\u5426\u5728: %s" % all(x in cks for x in
      ["osteoarthritis", "knee_osteoarthritis", "chronic_bronchitis", "chronic_gastritis"]))

print("\n\u836f\u540d\u5b9e\u9645\u5199\u6cd5\uff08\u65b0\u589e 9 \u6761\uff09:")
for mm in re.finditer(r"id: '([^']+)', name: '([^']+)'", m.group(1)):
    if mm.group(1) in ("gliclazide", "irbesartan", "diclofenac", "simvastatin", "doxofylline",
                       "etoricoxib", "ureaclear", "ketoacid", "telmisartan"):
        print("  %-14s %s" % (mm.group(1), mm.group(2)))

print("\nalias \u662f\u5426\u5df2\u8865\uff08\u73b0\u6709 12 \u6761\uff09:")
for mm in re.finditer(r"id: '([^']+)', name: '([^']+)', alias: \[([^\]]*)\]", m.group(1)):
    if mm.group(1) in ("nifedipine", "metformin", "metoprolol", "isosorbide", "omeprazole",
                       "ibuprofen", "hydrochlorothiazide", "acarbose", "benazepril", "aspirin",
                       "valsartan", "amlodipine"):
        al = re.findall(r"'([^']*)'", mm.group(3))
        print("  %-18s %s" % (mm.group(1), al))

print("\n\u5339\u914d\u52a0\u56fa\u5316\uff1anormDrugForm = %s" % ("function normDrugForm" in t))
print("\u6162\u75c5 alias \u652f\u6301 = %s" % ("(EMC.CHRONIC_DISEASES[i].alias || [])" in t))

kb = io.open(ROOT + r"\kb.js", encoding="utf-8").read()
kbn = re.findall(r'"n":"([^"]+)"', kb)
print("\nkb.js = %d \u6761" % len(kbn))
print("  \u542b\u300c\u6c99\u300d\u7684\u65b0\u6761\u76ee: %s" % [n for n in kbn if "\u6c99" in n][-4:])
