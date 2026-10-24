# -*- coding: utf-8 -*-
"""v44\uff1a\u9a8c\u8bc1\u4fee\u8ba2\u7248 docx \u7684\u5b8c\u6574\u6027\u3002"""
import io
import os
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SRC = r"C:\Users\d1513\Desktop\申报书_AI 风险筛查与提醒、用药管理与人文关怀 —— 老年人慢病用药辅助智能体（系统）初定版-吴改-余改.docx"
OUT = r"C:\Users\d1513\Desktop\申报书_AI 风险筛查与提醒、用药管理与人文关怀 —— 老年人慢病用药辅助智能体（系统）初定版-吴改-余改_修订版.docx"
OK = [True]


def ck(d, c, e=""):
    print(("  PASS  " if c else "  FAIL  ") + d + (("  -> " + str(e)) if e else ""))
    OK[0] = OK[0] and bool(c)


def ptext(p):
    out = []
    for n in p.iter():
        if n.tag == W + "t":
            out.append(n.text or "")
    return "".join(out)


zs = zipfile.ZipFile(SRC)
zo = zipfile.ZipFile(OUT)
sn, on = set(zs.namelist()), set(zo.namelist())

ck("zip \u53ef\u6b63\u5e38\u6253\u5f00", zo.testzip() is None)
ck("\u6ca1\u4e22\u5931\u4efb\u4f55 package \u6761\u76ee", not (sn - on), sorted(sn - on)[:5])
ck("document.xml \u5b58\u5728", "word/document.xml" in on)

src_media = sorted(x for x in sn if x.startswith("word/media/"))
out_media = sorted(x for x in on if x.startswith("word/media/"))
ck("\u56fe\u7247\u5168\u90e8\u4fdd\u7559", src_media == out_media,
   "%d -> %d" % (len(src_media), len(out_media)))

for part in ("word/comments.xml", "word/people.xml", "word/styles.xml", "word/_rels/document.xml.rels"):
    if part in sn:
        ck("\u4fdd\u7559 %s" % part.split("/")[-1], part in on)

# XML \u53ef\u89e3\u6790
try:
    droot = ET.fromstring(zo.read("word/document.xml"))
    ck("document.xml \u53ef\u89e3\u6790", True)
except Exception as e:
    ck("document.xml \u53ef\u89e3\u6790", False, e)
    droot = None

if droot is not None:
    body = droot.find(W + "body")
    ps = list(body.iter(W + "p"))
    ck("\u6bb5\u843d\u6570\u5408\u7406", 300 < len(ps) < 1200, len(ps))
    tbls = list(body.iter(W + "tbl"))
    ck("\u8868\u683c\u4fdd\u7559", len(tbls) >= 5, len(tbls))
    texts = [ptext(p) for p in ps]
    full = "\n".join(texts)
    ck("\u65b0\u589e\u53c2\u8003\u6587\u732e", "\u53c2\u8003\u6587\u732e\uff08GB/T 7714\uff09" in full)
    ck("\u65b0\u589e\u4f50\u8bc1\u6750\u6599\u76ee\u5f55", "\u4f50\u8bc1\u6750\u6599\u76ee\u5f55" in full)
    ck("\u5360\u4f4d\u00b7\u7cfb\u7edf\u754c\u9762\u622a\u56fe", "\u5360\u4f4d\u00b7\u7cfb\u7edf\u754c\u9762\u622a\u56fe" in full)
    ck("\u5360\u4f4d\u00b7\u793e\u533a\u8c03\u7814\u7167\u7247", "\u5360\u4f4d\u00b7\u793e\u533a\u8c03\u7814\u73b0\u573a\u7167\u7247" in full)
    ck("\u5360\u4f4d\u00b7\u8c03\u7814\u771f\u5b9e\u6570\u636e", "\u5360\u4f4d\u00b7\u793e\u533a\u8c03\u7814\u771f\u5b9e\u6570\u636e" in full)
    ck("UTAUT + HBM \u7406\u8bba\u6846\u67b6", "UTAUT" in full and "HBM" in full)
    ck("\u8bd5\u70b9\u5bf9\u7167\u8bbe\u8ba1 + \u6837\u672c\u91cf + PDC \u7ec8\u70b9",
       "\u8bd5\u70b9\u524d\u540e\u5bf9\u7167\u8bbe\u8ba1" in full and "PDC" in full)
    ck("\u6570\u636e\u4fee\u6b63 33.4%", "33.4%" in full and "34.5%" not in full)
    ck("\u6570\u636e\u4fee\u6b63 58% / 82%", "\u7ea658%" in full)
    ck("\u77e5\u8bc6\u5e93 1605 \u6761", "1605" in full)
    ck("\u7ade\u4e89\u8d5b\u4e8b\u66f4\u540d", "\u4e2d\u56fd\u56fd\u9645\u5927\u5b66\u751f\u521b\u65b0\u521b\u4e1a\u5927\u8d5b" in full)
    ck("\u8f6f\u4ef6\u8457\u767b\u8bb0\u8d39\u505c\u5f81\u8bf4\u660e", "\u505c\u5f81\u767b\u8bb0\u8d39" in full)
    ck("\u7814\u7a76\u57fa\u7840\u786c\u4ef6/\u8f6f\u4ef6\u5206\u5199", "\u786c\u4ef6" in full and "\u8f6f\u4ef6" in full)
    ck("\u793e\u533a\u770b\u677f\u8840\u538b\u8840\u7cd6\u4e0e\u8131\u654f", "\u8840\u538b\u8840\u7cd6" in full and "\u8131\u654f" in full)
    ck("\u5e76\u53d1\u4fdd\u62a4\uff08If-Match\uff09", "If-Match" in full)
    ck("\u65b9\u8a00\u652f\u6301\u5230\u6d59\u5c3e\u8bdd", "\u6d59\u5c3e\u8bdd" in full)
    ck("\u91c7\u7528\u6d88\u654f\u805a\u5408\u6307\u6807\u7684\u770b\u677f\u8bf4\u660e", "\u805a\u5408\u6307\u6807" in full)
    ck("\u82f1\u6587\u534a\u89d2\u5f15\u53f7\u5df2\u6e05\u9664", '"' not in full.replace('\\"', ''),
       full.count('"'))
    # 项目名/系统名保留「慢病」（与封面一致），描述性表述用「慢性疾病」
    left = [x.strip() for x in full.split("\n") if "\u6162\u75c5" in x]
    ck("「慢病」仅出现在项目名/系统名中", len(left) <= 6 and all(
        ("\u6162\u75c5\u7528\u836f" in x) for x in left), len(left))
    ck("描述性表述已用「慢性疾病」", full.count("\u6162\u6027\u75be\u75c5") >= 8,
       full.count("\u6162\u6027\u75be\u75c5"))

print("\n" + ("\u5168\u90e8\u901a\u8fc7" if OK[0] else "\u6709\u5931\u8d25"))
sys.exit(0 if OK[0] else 1)
