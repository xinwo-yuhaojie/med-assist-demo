# -*- coding: utf-8 -*-
"""提取 docx 正文（段落 + 样式 + 是否含图），用于判断现有结构与薄弱处。"""
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

p = sys.argv[1]
z = zipfile.ZipFile(p)
xml = z.read("word/document.xml").decode("utf-8")

print("document.xml =", len(xml), "chars")
print("段落数 <w:p>  =", xml.count("<w:p ") + xml.count("<w:p>"))
print("表格数 <w:tbl> =", xml.count("<w:tbl>"))
print("图片 <w:drawing> =", xml.count("<w:drawing>"))
print("media 文件:", [n for n in z.namelist() if n.startswith("word/media")])
print("")
print("=" * 70)

paras = re.findall(r"<w:p[ >].*?</w:p>", xml, re.S)
# 只匹配 <w:t> 与 <w:t xml:space="preserve">。
# 写成 <w:t[^>]*> 会把 <w:tbl>/<w:tc>/<w:tr> 一并吞进来，
# 正文里就会混进成片的 <w:autoSpaceDE/> 之类的原始 XML 碎片。
T = re.compile(r"<w:t(?: [^>]*)?>(.*?)</w:t>", re.S)
for i, para in enumerate(paras):
    st = re.search(r'<w:pStyle w:val="([^"]+)"', para)
    style = st.group(1) if st else ""
    txt = "".join(T.findall(para))
    txt = re.sub(r"\s+", " ", txt).strip()
    img = " [图]" if "<w:drawing>" in para else ""
    if txt or img:
        print("%3d %-12s %s%s" % (i, style[:12], txt[:92], img))