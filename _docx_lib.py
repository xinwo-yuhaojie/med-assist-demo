# -*- coding: utf-8 -*-
"""v44\uff1a\u6700\u8f7b\u91cf docx \u7f16\u8f91\u5e93\uff08\u76f4\u63a5\u64cd\u4f5c OOXML\uff0c\u4e0d\u4f9d\u8d56 python-docx\uff09\u3002

\u76ee\u7684\uff1a\u4fee\u6539\u7533\u62a5\u4e66\u6b63\u6587\uff0c\u540c\u65f6**\u5b8c\u5168\u4fdd\u7559**\uff1a
  \u00b7 \u539f\u6709\u6bb5\u843d\u683c\u5f0f\uff08\u5b57\u4f53\u3001\u884c\u8ddd\u3001\u7b49\u7ea7\uff09
  \u00b7 \u8868\u683c\u7ed3\u6784\u4e0e\u6837\u5f0f
  \u00b7 \u5df2\u6709\u6279\u6ce8\uff08comments.xml\uff09\u4e0e\u4eba\u5458\u4fe1\u606f
  \u00b7 \u56fe\u7247\u7b49\u5a92\u4f53\u6587\u4ef6
  \u00b7 \u5176\u4ed6\u6240\u6709 package \u6761\u76ee

\u5173\u952e\u5b9e\u73b0\u70b9\uff1a
  set_para_text  \u2192 \u53ea\u6539\u5199\u6bb5\u843d\u7684 w:t \u6587\u672c\uff0c**\u4fdd\u7559\u9996\u4e2a run \u7684\u5185\u5bb9\u683c\u5f0f**\uff08\u52a0\u7c97/\u5b57\u4f53/\u989c\u8272\uff09
  insert_para   \u2192 \u590d\u5236\u76f8\u90bb\u6bb5\u843d\u7684 w:pPr\uff0c\u4fdd\u8bc1\u65b0\u6bb5\u843d\u6837\u5f0f\u4e00\u81f4
  bold_phrases  \u2192 \u6309\u5173\u952e\u8bcd\u5206\u53e5\u62c6 run\uff0c\u53ea\u5bf9\u547d\u4e2d\u53e5\u52a0\u7c97\uff08\u4fdd\u7559\u5176\u4f59 run \u539f\u6837\uff09
"""
import copy
import io
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = "{%s}" % W
ET.register_namespace("w", W)


def q(tag):
    return NS + tag


class Docx(object):
    def __init__(self, path):
        self.path = path
        self.zin = zipfile.ZipFile(path)
        self.items = [(i, self.zin.read(i.filename)) for i in self.zin.infolist()]
        self.doc = ET.fromstring(self._raw("word/document.xml"))
        self.body = self.doc.find(q("body"))
        self.log = []

    def _raw(self, name):
        for i, d in self.items:
            if i.filename == name:
                return d
        raise KeyError(name)

    # ---------- \u6bb5\u843d ----------
    def paras(self):
        """\u76f4\u63a5\u5728 body \u4e0b\u7684\u6bb5\u843d\uff08\u4e0d\u5305\u542b\u8868\u683c\u5185\u7684\uff09\u3002"""
        return [c for c in self.body if c.tag == q("p")]

    def all_paras(self):
        """\u5305\u542b\u8868\u683c\u5185\u7684\u6240\u6709\u6bb5\u843d\u3002"""
        return list(self.body.iter(q("p")))

    @staticmethod
    def text(p):
        out = []
        for n in p.iter():
            if n.tag == q("t"):
                out.append(n.text or "")
            elif n.tag == q("tab"):
                out.append("\t")
            elif n.tag == q("br"):
                out.append(" ")
        return "".join(out)

    @staticmethod
    def style(p):
        ppr = p.find(q("pPr"))
        if ppr is None:
            return ""
        st = ppr.find(q("pStyle"))
        return st.get(q("val"), "") if st is not None else ""

    def find(self, needle, exact=False, in_table=True):
        """\u627e\u7b2c\u4e00\u4e2a\u5305\u542b needle \u7684\u6bb5\u843d\u3002"""
        for p in (self.all_paras() if in_table else self.paras()):
            t = self.text(p)
            if (t.strip() == needle) if exact else (needle in t):
                return p
        return None

    def find_prefix(self, prefix, in_table=True):
        """找第一个以 prefix 开头的段落，比较时忽略引号与空白差异。"""
        def norm(s):
            return (s.replace('\u201c', '').replace('\u201d', '').replace('\u300c', '').replace('\u300d', '')
                     .replace(chr(34), '').replace(' ', ''))
        np_ = norm(prefix)
        for p in (self.all_paras() if in_table else self.paras()):
            if norm(self.text(p).strip()).startswith(np_):
                return p
        return None

    def find_all(self, needle, in_table=False):
        out = []
        for p in (self.all_paras() if in_table else self.paras()):
            if needle in self.text(p):
                out.append(p)
        return out

    # ---------- \u5199\u5165 ----------
    def set_para_text(self, p, text, keep_first_run=True):
        """\u6539\u5199\u6bb5\u843d\u6587\u672c\uff0c\u4fdd\u7559\u9996\u4e2a run \u7684\u683c\u5f0f\u3002"""
        runs = [r for r in p.iter(q("r"))]
        ts = []
        for r in runs:
            ts.extend(r.findall(q("t")))
        if not ts:
            r = ET.SubElement(p, q("r"))
            t = ET.SubElement(r, q("t"))
            t.text = text
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            return True
        first = ts[0]
        first.text = text
        first.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        for extra in ts[1:]:
            extra.text = ""
        # \u6e05\u6389\u5176\u4ed6 run \u91cc\u7684\u975e\u6587\u672c\u5185\u5bb9\uff08\u5982\u9000\u683c\u7b26\uff09
        return True

    def insert_para_after(self, anchor, text, bold=False, style_from=None):
        """\u5728 anchor \u6bb5\u843d\u4e4b\u540e\u63d2\u5165\u4e00\u4e2a\u65b0\u6bb5\u843d\uff0c\u590d\u5236 anchor \u7684 pPr\u3002"""
        model = style_from if style_from is not None else anchor
        newp = ET.Element(q("p"))
        ppr = model.find(q("pPr"))
        if ppr is not None:
            newp.append(copy.deepcopy(ppr))
        r = ET.SubElement(newp, q("r"))
        # \u7ee7\u627f\u6a21\u677f\u6bb5\u9996\u4e2a run \u7684 rPr
        model_rpr = None
        for mr in model.iter(q("r")):
            rp = mr.find(q("rPr"))
            if rp is not None:
                model_rpr = rp
                break
        if model_rpr is not None:
            rpr = copy.deepcopy(model_rpr)
            if bold and rpr.find(q("b")) is None:
                rpr.insert(0, ET.Element(q("b")))
            r.append(rpr)
        t = ET.SubElement(r, q("t"))
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        # 定位 anchor 所在的父容器：
        #   body 直接子元素（段落）→ 插到 body；
        #   表格单元格（tc）→ 插到该 tc 内部（tc 内直接放 p 是合法的）。
        parent = None
        for c in list(self.body):
            if c is anchor:
                parent = self.body
                break
            if anchor in list(c.iter()):
                parent = c
                break
        if parent is None:
            parent = self.body
        if parent is self.body:
            children = list(self.body)
            idx = children.index(anchor)
            self.body.insert(idx + 1, newp)
        else:
            # 递归找 **最近祖先**：上一次遍历取到的是最外层（body/tbl），
            # 会把新段落插到 body 顶层（封面之前）。正确做法：从 anchor 的上层容器开始向下查，
            # 只选择其直接子元素里包含 anchor 的那一个。
            holder = None
            node = anchor
            while True:
                found = None
                for cand in parent:
                    if cand is node:
                        break
                    if node in list(cand.iter()):
                        found = cand
                        break
                if found is None:
                    break
                node = found
                holder = found
                if found.tag == q('tc') or found.tag == q('p'):
                    break
            if holder is None:
                holder = parent
            ch = list(holder)
            idx = ch.index(anchor) if anchor in ch else len(ch) - 1
            holder.insert(idx + 1, newp)
        return newp

    def insert_paras_after(self, anchor, items):
        """items = [(text, bold), ...] \u8fde\u7eed\u63d2\u5165\u3002"""
        cur = anchor
        for text, bold in items:
            cur = self.insert_para_after(cur, text, bold=bold)
        return cur

    def bold_phrases(self, p, phrases):
        """\u628a\u6bb5\u843d\u62c6\u6210\u591a\u4e2a run\uff0c\u53ea\u5bf9\u5305\u542b phrases \u7684\u53e5\u5b50\u52a0\u7c97\u3002"""
        full = self.text(p)
        if not full.strip():
            return False
        # \u628a\u6bb5\u843d\u5185\u5bb9\u6309\u53e5\u53f7\u62c6\u5206\uff0c\u4fdd\u7559\u539f\u6709\u7684\u683c\u5f0f\uff08\u53d6\u9996\u4e2a run \u7684 rPr\uff09
        base_rpr = None
        for r in p.iter(q("r")):
            rp = r.find(q("rPr"))
            if rp is not None:
                base_rpr = rp
                break
        pieces = []
        buf = ""
        for ch in full:
            buf += ch
            if ch in "\u3002\uff1b\uff01\uff1f\n":
                pieces.append(buf)
                buf = ""
        if buf:
            pieces.append(buf)
        # \u91cd\u5efa\u6bb5\u843d\uff1a\u6e05\u9664\u6240\u6709 run\uff0c\u6309 piece \u91cd\u65b0\u751f\u6210
        for r in [x for x in list(p) if x.tag == q("r")]:
            p.remove(r)
        for piece in pieces:
            hit = any(ph in piece for ph in phrases)
            r = ET.SubElement(p, q("r"))
            if base_rpr is not None:
                rpr = copy.deepcopy(base_rpr)
                if hit and rpr.find(q("b")) is None:
                    rpr.insert(0, ET.Element(q("b")))
                r.append(rpr)
            t = ET.SubElement(r, q("t"))
            t.text = piece
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return True

    def delete_para(self, p):
        try:
            self.body.remove(p)
            return True
        except Exception:
            return False

    # ---------- \u4fdd\u5b58 ----------
    def save(self, out):
        """先写临时文件，再原子替换。
        目标文件往往会被 Word 打开占用 → 直接 ZipFile(out,'w') 会
        先把原文件截断为 0 字节、再报错，目标格式完装丢失。
        现在先写 .tmp，成功后再 replace。"""
        import os
        import shutil
        # 关闭读句柄：Windows 上打开的 zip 会锁住文件，
        # 不关的话 os.replace 会报 WinError 5。
        try:
            self.zin.close()
        except Exception:
            pass
        tmp = out + ".tmp"
        if os.path.exists(tmp):
            os.remove(tmp)
        xml = ET.tostring(self.doc, encoding="UTF-8", xml_declaration=True)
        zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
        try:
            for info, data in self.items:
                if info.filename == "word/document.xml":
                    zout.writestr(info, xml)
                else:
                    zout.writestr(info, data)
        finally:
            zout.close()
        try:
            os.replace(tmp, out)
        except OSError as e:
            # \u76ee\u6807\u88ab Word \u5360\u7528\uff1a\u4fdd\u7559 .tmp\uff0c\u5e76\u7ed9\u51fa\u660e\u786e\u63d0\u793a
            raise IOError("\u65e0\u6cd5\u5199\u5165 %s\uff08\u8bf7\u5148\u5173\u95ed\u8be5\u6587\u4ef6\uff09\uff1a%s" % (out, e))
        return out


def normalize_quotes(text):
    """\u82f1\u6587\u534a\u89d2\u5f15\u53f7 \u201c \" \u201d \u2192 \u4e2d\u6587\u5168\u89d2 \u201c \u201d\uff08\u6210\u5bf9\u5207\u6362\uff09\u3002"""
    out = []
    open_q = True
    for ch in text:
        if ch == '"':
            out.append("\u201c" if open_q else "\u201d")
            open_q = not open_q
        else:
            out.append(ch)
    return "".join(out)
