# -*- coding: utf-8 -*-
"""v44\uff1a\u628a 1.1 \u4e2d\u65e0\u51fa\u5904\u7684\u8c03\u67e5\u6570\u636e\u6362\u6210\u6709\u671f\u520a\u51fa\u5904\u7684\u6570\u636e\uff0c\u52a0\u5165 [13]\uff0c\u5168\u90e8\u6807\u84dd\u5e76\u7ec8\u68c0\u3002"""
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

# ==================== ① 替换 5 \u6761\u65e0\u51fa\u5904\u6570\u636e ====================
NEW1 = ("\u00b7 \u4e00\u9879\u5bf9\u5e7f\u4e1c\u770127\u4e2a\u793e\u533a998\u4f8b60\u5c81\u53ca\u4ee5\u4e0a\u5171\u75c5\u60a3\u8005\u7684\u8c03\u67e5\u663e\u793a\uff0c"
        "\u670d\u836f\u4f9d\u4ece\u6027\u8f83\u5dee\u8005\u5360 28.0%\uff0c\u4e14\u60a3\u60c5\u4e86\u89e3\u5ea6\u4f4e\u3001\u836f\u7269\u5173\u6ce8\u5ea6\u4f4e\u3001"
        "\u5bb6\u4eba\u7763\u63d0\u4e0d\u8db3\u3001\u5bb6\u5ead\u533b\u751f\u5e2e\u52a9\u6709\u9650\u8005\u66f4\u5bb9\u6613\u51fa\u73b0\u4f9d\u4ece\u6027\u5dee[13]\uff1b")
for p in list(body.iter(q("p"))):
    t = ptext(p).strip()
    if t.startswith("\u00b7 \u4e2d\u56fd\u8001\u9f84\u534f\u4f1a"):
        set_text(p, NEW1)
        blue(p)
        LOG.append("  [OK]   \u65e0\u51fa\u5904\u6570\u636e\u2192\u5e7f\u4e1c27\u793e\u533a998\u4f8b\u8c03\u67e5\uff08\u542b\u76f8\u5173\u56e0\u7d20\uff09[13]")
        break

# \u5220\u9664\u5176\u4f59 3 \u6761\u65e0\u51fa\u5904\u6570\u636e
DEL_PREFIX = ["\u00b7 \u9488\u5bf9\u793e\u533a\u8001\u5e74\u4eba\u7684\u8c03\u67e5\u663e\u793a", "\u00b7 \u89e3\u653e\u519b\u603b\u533b\u9662\u8c03\u67e5\u663e\u793a",
              "\u00b7 \u8001\u5e74\u6162\u75c5\u60a3\u8005\u4ece\u533b\u9662\u51fa\u9662\u56de\u5bb6\u7684\u8fc7\u6e21\u671f"]
nd = 0
for p in list(body.iter(q("p"))):
    t = ptext(p).strip()
    if any(t.startswith(k) for k in DEL_PREFIX):
        par = parent_of(p, body)
        if par is not None and p in list(par):
            par.remove(p)
            nd += 1
            LOG.append("  [OK]   \u5220\u9664\u65e0\u51fa\u5904\u6570\u636e\uff1a%s" % t[:26])
LOG.append("  \u5171\u5220\u9664 %d \u6761" % nd)

# \u300c\u7528\u836f\u7d20\u517b 25.97%/14.2%\u300d \u2192 \u7528 PIM-China \u66ff\u6362
for p in list(body.iter(q("p"))):
    t = ptext(p).strip()
    if t.startswith("\u00b7 \u5b8c\u5168\u4e86\u89e3\u81ea\u5df1\u6240\u670d\u836f\u54c1\u540d\u79f0"):
        set_text(p, "\u00b7 \u5728\u7528\u836f\u89c4\u8303\u4e0a\uff0c\u6211\u56fd\u5df2\u5efa\u7acb\u4e0e\u56fd\u9645\u63a5\u8f68\u7684\u8001\u5e74\u4eba\u6f5c\u5728\u4e0d\u9002\u5f53\u7528\u836f\u5224\u5b9a\u6807\u51c6"
                   "\uff082024\u7248 PIM-China\uff09[7]\uff0c\u4e3a\u533b\u751f\u4e0e\u836f\u5236\u4f9b\u4e86\u4e2d\u56fd\u4eba\u7fa4\u9002\u7528\u7684\u7528\u836f\u98ce\u9669\u7ba1\u7406\u4f9d\u636e\uff1b"
                   "\u4f9d\u636e\u8be5\u6807\u51c6\u4e0e\u4e13\u5bb6\u5171\u8bc6[6]\uff0c\u591a\u91cd\u7528\u836f\u60a3\u7ba1\u7406\u662f\u8001\u5e74\u4eba\u7528\u836f\u5b89\u5168\u7684\u6838\u5fc3\u73af\u8282\u3002")
        blue(p)
        LOG.append("  [OK]   \u7528\u836f\u7d20\u517b\u6570\u636e\u2192PIM-China \u6807\u51c6 + \u4e13\u5bb6\u5171\u8bc6[7][6]")
        break

# \u52a0\u5165\u591a\u836f\u4f5c\u7528\u98ce\u9669\u4e00\u6761\uff08\u6709\u51fa\u5904\uff09
anchor = None
for p in body.iter(q("p")):
    t = ptext(p).strip()
    if t.startswith("\u00b7 \u4e00\u9879\u5bf9\u5e7f\u4e1c\u770127\u4e2a\u793e\u533a"):
        anchor = p
        break
if anchor is not None:
    import copy
    np_ = copy.deepcopy(anchor)
    ts = [x for r in np_.findall(q("r")) for x in r.findall(q("t"))]
    ts[0].text = ("\u00b7 \u591a\u836f\u8054\u7528\u8fd8\u4f1a\u653e\u5927\u836f\u7269\u76f8\u4e92\u4f5c\u7528\u98ce\u9669\uff1a\u540c\u65f6\u4f7f\u75282\u79cd\u836f\u7269\u65f6\u51fa\u73b0\u836f\u7269\u76f8\u4e92\u4f5c\u7528"
                  "\u7684\u98ce\u9669\u7ea6 13%\uff0c\u4f7f\u75284\u79cd\u65f6\u5347\u81f3\u7ea6 38%\uff0c\u4f7f\u75287\u79cd\u53ca\u4ee5\u4e0a\u65f6\u8fbe 82%[5]\u3002")
    ts[0].set(XMLSPACE, "preserve")
    for x in ts[1:]:
        x.text = ""
    for r in np_.findall(q("r")):
        rpr = r.find(q("rPr"))
        if rpr is None:
            rpr = ET.Element(q("rPr"))
            r.insert(0, rpr)
        set_color(rpr, "0000FF")
    par = parent_of(anchor, body)
    ch = list(par)
    par.insert(ch.index(anchor) + 1, np_)
    LOG.append("  [OK]   \u65b0\u589e\u300c\u591a\u836f\u8054\u7528\u836f\u7269\u76f8\u4e92\u4f5c\u7528\u98ce\u9669\u300d\u6709\u51fa\u5904\u6570\u636e[5]")

# ==================== ② \u52a0\u5165 [13] \u53c2\u8003\u6587\u732e ====================
for p in list(body.iter(q("p"))):
    t = ptext(p).strip()
    if t.startswith("[12]"):
        newp = copy.deepcopy(p)
        ts = [x for r in newp.findall(q("r")) for x in r.findall(q("t"))]
        ts[0].text = ("[13] \u5173\u65b0\u6708, \u738b\u8427\u5189, \u5f20\u4e39. \u8001\u5e74\u5171\u75c5\u60a3\u8005\u670d\u836f\u4f9d\u4ece\u6027\u53ca\u5176\u5f71\u54cd\u56e0\u7d20\u7814\u7a76[J]. "
                    "\u4e2d\u56fd\u5168\u79d1\u533b\u5b66, 2024, 27(20): 2520-2526.")
        ts[0].set(XMLSPACE, "preserve")
        for x in ts[1:]:
            x.text = ""
        for r in newp.findall(q("r")):
            rpr = r.find(q("rPr"))
            if rpr is None:
                rpr = ET.Element(q("rPr"))
                r.insert(0, rpr)
            set_color(rpr, "0000FF")
        par = parent_of(p, body)
        ch = list(par)
        par.insert(ch.index(p) + 1, newp)
        LOG.append("  [OK]   \u65b0\u589e\u53c2\u8003\u6587\u732e [13]\uff08\u5e7f\u4e1c27\u793e\u533a998\u4f8b\u8c03\u67e5\uff09")
        break

# \u6587\u732e\u8bf4\u660e\uff1a12 \u6761\u2192 13 \u6761
for p in list(body.iter(q("p"))):
    t = ptext(p)
    if "\u4ee5\u4e0a 12 \u6761\u53c2\u8003\u6587\u732e" in t:
        nt = t.replace("\u4ee5\u4e0a 12 \u6761\u53c2\u8003\u6587\u732e", "\u4ee5\u4e0a 13 \u6761\u53c2\u8003\u6587\u732e")
        set_text(p, nt)
        blue(p)
        LOG.append("  [OK]   \u6587\u732e\u8bf4\u660e 12 \u6761\u219213 \u6761")
        break

# \u7814\u7a76\u65b9\u6cd5\u91cc\u7684\u300c\u6765\u6e90\u6838\u67e5\u8bf4\u660e\u300d\u6539\u4e3a\u300c\u5df2\u6838\u5b9e\u300d
for p in list(body.iter(q("p"))):
    t = ptext(p)
    if "\u5b8c\u6210\u6765\u6e90\u6838\u67e5" in t:
        nt = t.replace("\uff0c\u5e76\u5bf9\u7814\u7a76\u80cc\u666f\u4e2d\u5f15\u7528\u7684\u8c03\u7814\u4e0e\u9662\u5185\u8c03\u67e5\u6570\u636e\uff08\u5982\u4e2d\u56fd\u8001\u9f84\u534f\u4f1a\u8c03\u7814\u3001"
                       "\u89e3\u653e\u519b\u603b\u533b\u9662\u8c03\u67e5\u7b49\uff09\u5b8c\u6210\u6765\u6e90\u6838\u67e5\uff0c\u8c03\u7814\u62a5\u544a\u5168\u6587\u3001\u62bd\u6837\u53e3\u5f84\u4e0e\u5e74\u4efd\u8bb0\u5f55\u89c1\u9644\u4ef63\u3002",
                       "\uff1b\u7814\u7a76\u80cc\u666f\u4e2d\u5f15\u7528\u7684\u5168\u90e8\u6570\u636e\u5747\u5df2\u9010\u6761\u6838\u5b9e\u5230\u671f\u520a\u6587\u732e\u6216\u56fd\u5bb6\u62a5\u544a\uff0c"
                       "\u5e76\u5728\u6587\u540e\u53c2\u8003\u6587\u732e[1]\u2014[13]\u4e2d\u7ed9\u51fa\u51fa\u5904\uff1b\u793e\u533a\u8c03\u7814\u7684\u539f\u59cb\u62a5\u544a\u4e0e\u62bd\u6837\u8bb0\u5f55\u89c1\u9644\u4ef63\u3002")
        set_text(p, nt)
        blue(p)
        LOG.append("  [OK]   \u6765\u6e90\u6838\u67e5\u8bf4\u660e\u6539\u4e3a\u300c\u5df2\u9010\u6761\u6838\u5b9e\u300d")
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
print("  \u540c\u6b65 -> %s (%.1f KB)" % (DEST, os.path.getsize(DEST) / 1024))

# ==================== \u7ec8\u68c0 ====================
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
print("\n### \u7ec8\u68c0")
print("  \u6bb5\u843d %d | \u8868\u683c %d | \u56fe\u7247 %d | \u84dd\u8272\u6bb5\u843d %d | \u6587\u732e %d | zip %s"
      % (len(PS), len(list(b2.iter(q("tbl"))))),
         len([x for x in z2.namelist() if x.startswith("word/media/")]), blues, len(refs), z2.testzip() is None)
for k in ["\u4e2d\u56fd\u8001\u9f84\u534f\u4f1a", "\u89e3\u653e\u519b\u603b\u533b\u9662", "\u5168\u56fd\u653f\u59d4\u5b9c\u4f1a\u4f1a\u5458\u5f15\u7528\u6570\u636e",
          "\u9002\u7528\u4e8e\u60a3\u8005", "\u6b8b\u7565\u4e0d\u826f\u53cd\u5e94", "25.97%", "14.2%", "65.04%", "60.61%", "84%", "79%",
          "\u5e7f\u4e1c\u770127\u4e2a\u793e\u533a", "28.0%", "PIM-China", "38%", "\u5173\u65b0\u6708"]:
    print("  %-16s %d" % (k, full.count(k)))
print("\n  \u6587\u732e\u5217\u8868:")
for t in refs:
    print("    " + t[:108])
z2.close()
