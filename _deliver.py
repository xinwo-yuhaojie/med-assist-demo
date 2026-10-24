# -*- coding: utf-8 -*-
"""v44\uff1a\u6700\u7ec8\u4ea4\u4ed8\u2014\u2014\u4fee\u6b63 Goldberg \u6570\u636e\u8bed\u4e49 + \u4ee5\u65b0\u6587\u4ef6\u540d\u4ea4\u4ed8\u3002"""
import io
import os
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
DESKDIR = r"C:\Users\d1513\Desktop\大创申报6"
FINAL = os.path.join(DESKDIR, "申报书终稿_蓝标版.docx")
FINAL2 = os.path.join(r"C:\Users\d1513\Desktop", "附件2 安全审计报告摘要.docx")


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


z = zipfile.ZipFile(WORK)
doc = ET.fromstring(z.read("word/document.xml"))
body = doc.find(q("body"))

OLD = "研究显示（Goldberg et al., 1996）同时服用2种药物时不良反应发生率约13%，服用4种约38%，服用7种及以上达82%。"
NEW = ("研究显示（Goldberg et al., 1996）同时使用2种药物时出现药物相互作用的风险约13%，"
       "使用4种时升至约38%，使用7种及以上时达82%。")
hit = False
for p in list(body.iter(q("p"))):
    t = ptext(p)
    if OLD in t:
        set_text(p, t.replace(OLD, NEW))
        blue(p)
        hit = True
        break
print("  %s  Goldberg 语义修正为「药物相互作用风险」" % ("[OK]" if hit else "[MISS]"))

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

shutil.copyfile(WORK, FINAL)
print("  申报书终稿 -> %s (%.1f KB)" % (FINAL, os.path.getsize(FINAL) / 1024))
if os.path.exists(FINAL2):
    print("  附件2     -> %s (%.1f KB)" % (FINAL2, os.path.getsize(FINAL2) / 1024))

# \u6700\u7ec8\u6838\u9a8c
z2 = zipfile.ZipFile(FINAL)
d2 = ET.fromstring(z2.read("word/document.xml"))
b2 = d2.find(q("body"))
seq = [ptext(p).strip() for p in b2.iter(q("p")) if ptext(p).strip()]
full = "\n".join(seq)
PROB = []


def ck(c, tag, e=""):
    print(("  PASS  " if c else "  FAIL  ") + tag + (("  -> " + str(e)) if e else ""))
    if not c:
        PROB.append(tag)


print("\n### \u6700\u7ec8\u6838\u9a8c")
ck("American Journal of Emergency Medicine" in full, "[5] \u771f\u5b9e\u671f\u520a\u4e0e\u5377\u671f\u9875\u7801")
ck("Journal of the American Geriatrics Society" not in full, "[5] \u65e7\u8457\u5f55\u5df2\u6e05")
ck("\u51fa\u73b0\u836f\u7269\u76f8\u4e92\u4f5c\u7528\u7684\u98ce\u9669\u7ea613%" in full, "\u6b63\u6587\u8bed\u4e49=\u836f\u7269\u76f8\u4e92\u4f5c\u7528\u98ce\u9669")
ck("\u4f7f\u75284\u79cd\u65f6\u5347\u81f3\u7ea638%" in full, "\u6b63\u6587 38% \u8868\u8ff0")
ck("\u4f7f\u75287\u79cd\u53ca\u4ee5\u4e0a\u65f6\u8fbe82%" in full, "\u6b63\u6587 82% \u8868\u8ff0")
ck("\u67cf\u4e01\u516e" in full and "\u6d59\u5c3e\u8bdd" in full and "\u6f6e\u6c7d\u8bdd" in full, "\u4f5c\u8005\u4e0e\u65b9\u8a00\u540d\u6b63\u786e")
ck("\u8840\u538b\u8840\u7cd6" in full and "\u8131\u654f" in full, "\u770b\u677f\u8840\u538b\u8840\u7cd6\u4e0e\u8131\u654f")
ck("\u98ce\u9669\u9884\u6d4b\u4e0e\u5e94\u5bf9" in full, "\u98ce\u9669\u9884\u6d4b\u4e0e\u5e94\u5bf9\u6bb5")
ck("\u3010\u5360\u4f4d" in full, "\u4e09\u4e2a\u5360\u4f4d")
ck("\u4f26\u7406\u4e0e\u5408\u89c4" in full, "\u4f26\u7406\u5408\u89c4\u6bb5")
ck(len([t for t in seq if t.startswith("[") and len(t) > 20 and t[1:3].isdigit()]) == 12, "\u53c2\u8003\u6587\u732e 12 \u6761")
PS = list(b2.iter(q("p")))
blues = 0
for p in PS:
    for r in p.findall(q("r")):
        rpr = r.find(q("rPr"))
        if rpr is not None:
            c = rpr.find(q("color"))
            if c is not None and c.get(q("val")) == "0000FF":
                blues += 1
                break
print("  \u6bb5\u843d %d | \u8868\u683c %d | \u56fe\u7247 %d | \u84dd\u8272\u6bb5\u843d %d | zip \u6b63\u5e38=%s"
      % (len(PS), len(list(b2.iter(q("tbl"))))),
         len([x for x in z2.namelist() if x.startswith("word/media/")]), blues, z2.testzip() is None)
z2.close()
print("\n" + ("\u5168\u90e8\u901a\u8fc7\uff0c\u53ef\u4ee5\u63d0\u4ea4" if not PROB else "\u4ecd\u6709\u95ee\u9898\uff1a%s" % PROB))
