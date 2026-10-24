# -*- coding: utf-8 -*-
"""v44\uff1a\u6e05\u7406\u5269\u4f59\u65e0\u51fa\u5904\u6570\u636e\uff08\u771f\u5b9e\u4e2d\u6587\uff09\u3002"""
import io
import os
import re
import shutil
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = "{%s}" % W
ET.register_namespace("w", W)
XMLSPACE = "{http://www.w3.org/XML/1998/namespace}space"
RPR_ORDER = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike",
             "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish",
             "webHidden", "color", "spacing", "w", "kern", "position", "sz", "szCs", "highlight",
             "u", "effect", "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang",
             "eastAsianLayout", "specVanish", "oMath"]
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "_rev_v2.docx")
DEST = os.path.join(r"C:\Users\d1513\Desktop\大创申报6", "申报书终稿_蓝标版.docx")


def q(t):
    return NS + t


def ptext(p):
    return "".join((n.text or "") for n in p.iter(q("t")))


def set_color(rpr, val):
    c = rpr.find(q("color"))
    if c is None:
        c = ET.Element(q("color"))
        idx = RPR_ORDER.index("color")
        pos = len(list(rpr))
        for k, ch in enumerate(list(rpr)):
            tag = ch.tag.replace(NS, "")
            if tag in RPR_ORDER and RPR_ORDER.index(tag) > idx:
                pos = k
                break
        rpr.insert(pos, c)
    c.set(q("val"), val)


def blue(p):
    for r in p.findall(q("r")):
        rpr = r.find(q("rPr"))
        if rpr is None:
            rpr = ET.Element(q("rPr"))
            r.insert(0, rpr)
        set_color(rpr, "0000FF")


def set_text(p, text):
    ts = [x for r in p.findall(q("r")) for x in r.findall(q("t"))]
    if not ts:
        r = ET.SubElement(p, q("r"))
        ts = [ET.SubElement(r, q("t"))]
    ts[0].text = text
    ts[0].set(XMLSPACE, "preserve")
    for x in ts[1:]:
        x.text = ""


def parent_of(node, root):
    for c in list(root):
        if c is node:
            return root
        if node in list(c.iter()):
            return parent_of(node, c)
    return None


z = zipfile.ZipFile(WORK)
doc = ET.fromstring(z.read("word/document.xml"))
body = doc.find(q("body"))
LOG = []

# ① 删掉「出院过渡期 60.61%」那条
for p in list(body.iter(q("p"))):
    t = ptext(p).strip()
    if t.startswith("· 老年慢性疾病患者从医院出院回家的过渡期"):
        par = parent_of(p, body)
        if par is not None and p in list(par):
            par.remove(p)
            LOG.append("  [OK]   删除「出院过渡期服药偏差 60.61%」（无出处）")
        break

# ② 方法里的来源核查说明改为「已逐条核实」
for p in list(body.iter(q("p"))):
    t = ptext(p)
    if "中国老龄协会调研" in t:
        head = t.split("；并对研究背景中引用的调研与院内调查数据")[0]
        nt = (head + "；研究背景中引用的全部现状数据均已逐条核实到期刊文献或国家报告，出处见文后参考文献[1]—[13]；"
               "社区调研的原始报告全文、抽样口径与年份记录见附件3。")
        set_text(p, nt)
        blue(p)
        LOG.append("  [OK]   来源说明改为「已逐条核实到文献/国家报告」")
        break

xml = ET.tostring(doc, encoding="UTF-8", xml_declaration=True)
tmp = WORK + ".tmp"
zo = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
try:
    for info, data in [(i, z.read(i.filename)) for i in z.infolist()]:
        zo.writestr(info, xml if info.filename == "word/document.xml" else data)
finally:
    zo.close()
z.close()
os.replace(tmp, WORK)
print("\n".join(LOG))
shutil.copyfile(WORK, DEST)
print("  同步 -> %s (%.1f KB)" % (DEST, os.path.getsize(DEST) / 1024))

# ==================== 终检 ====================
z2 = zipfile.ZipFile(DEST)
d2 = ET.fromstring(z2.read("word/document.xml"))
b2 = d2.find(q("body"))
PS = list(b2.iter(q("p")))
seq = [ptext(p).strip() for p in PS if ptext(p).strip()]
full = "\n".join(seq)
refs = [t for t in seq if re.match(r"^\[\d+\]", t)]
blues = 0
for p in PS:
    for r in p.findall(q("r")):
        rpr = r.find(q("rPr"))
        if rpr is not None:
            c = rpr.find(q("color"))
            if c is not None and c.get(q("val")) == "0000FF":
                blues += 1
                break
nimg = len([x for x in z2.namelist() if x.startswith("word/media/")])
ntbl = len(list(b2.iter(q("tbl"))))
print("\n### 终检")
print("  段落 %d | 表格 %d | 图片 %d | 蓝色段落 %d | 文献 %d | zip %s"
      % (len(PS), ntbl, nimg, blues, len(refs), z2.testzip() is None))
print("  --- 残留无源数据检查（应全 0）---")
for k in ["中国老龄协会", "解放军总医院", "孙蓉", "60.61", "65.04", "25.97", "14.2", "出院回家", "84%"]:
    print("    %-14s %d" % (k, full.count(k)))
print("  --- 新数据检查（应 >0）---")
for k in ["广东", "27个社区", "998例", "28.0%", "PIM-China", "38%", "82%", "13%"]:
    print("    %-14s %d" % (k, full.count(k)))
print("  --- 文献列表 ---")
for t in refs:
    print("    " + t[:110])
z2.close()
