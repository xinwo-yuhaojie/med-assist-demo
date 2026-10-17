# -*- coding: utf-8 -*-
"""
转义函数防回归测试（v35）
================================
背景：esc() 原本只转义 & < >，**不转义引号**，导致全站 20 多处
     'data-xxx="' + esc(v) + '"' 形式的属性可被一个双引号截断 —— 完整 XSS。
     而药名/剂量常来自用户**粘贴的处方文本**，是最现实的注入源。

做法：从 index.html 中静态提取 esc / telHref 的实现，
     ① 断言 5 个字符全部被转义（防回退）
     ② 用 Python 等价实现跑一遍注入载荷，确认"转义后不含裸引号/尖括号"
     ③ 断言源码里已无裸的 href="tel:" + esc(...) 写法

用法：python test_escape.py
"""
import sys, os, re, io
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 由本文件位置推导，不写死盘符 —— 项目整体移动后仍然有效
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
src = io.open(SRC, encoding="utf-8").read()
lines = src.split("\n")

def grab_fn(name):
    start = None
    for i, l in enumerate(lines):
        if l.strip().startswith("function " + name + "("):
            start = i; break
    if start is None:
        return None
    depth = 0
    for j in range(start, len(lines)):
        depth += lines[j].count("{") - lines[j].count("}")
        if j > start and depth == 0:
            return "\n".join(lines[start:j+1])
    return None

esc_js  = grab_fn("esc")
tel_js  = grab_fn("telHref")
if not esc_js or not tel_js:
    print("!! 未能定位 esc/telHref（若函数被改名，请同步更新本测试）")
    sys.exit(2)

def norm(js):
    """压掉空白与注释，便于做包含判断"""
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    js = re.sub(r"//[^\n]*", "", js)
    return re.sub(r"\s+", "", js)

esc_n  = norm(esc_js)
tel_n  = norm(tel_js)

OK = True
def ck(d, c):
    global OK
    print(("  PASS  " if c else "  FAIL  ") + d); OK = OK and c

# --- Python 等价实现，用于跑载荷 ---
def esc_py(s):
    s = "" if s is None else str(s)
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&#39;"))
def tel_py(phone):
    p = "" if phone is None else str(phone)
    return "tel:" + re.sub(r"[^0-9+*#]", "", p)

print("\n=== 1. esc 必须转义这 5 类字符（v35 修复的根因）===")
for ch, ent in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"),
                ('"', "&quot;"), ("'", "&#39;")):
    ck("esc 包含 %s 的转义" % ("双引号" if ch == '"' else "单引号" if ch == "'" else ch),
       ch.replace("&", "&").replace("'", "'") in esc_n and ent.replace("&", "&") in esc_n)

print("\n=== 2. 提取到的实现片段（供人工核对）===")
print("  esc    : " + esc_n[:110] + ("..." if len(esc_n) > 110 else ""))
print("  telHref: " + tel_n[:110] + ("..." if len(tel_n) > 110 else ""))

print("\n=== 3. 注入载荷经转义后不含裸引号/尖括号 ===")
for p in ['药" onmouseover="alert(1)', "药' onfocus='alert(1)",
          '"><img src=x onerror=alert(1)>', '</div><script>alert(1)</script>',
          'javascript:alert(1)', 'a"b\'c<d>e&f', '药\"><script>x</script>']:
    out = esc_py(p)
    bad = ('"' in out) or ("'" in out) or ("<" in out) or (">" in out)
    ck("载荷被中和: " + p[:36], not bad)

print("\n=== 4. telHref 只保留电话合法字符 ===")
ck("手机号原样", tel_py("13800000000") == "tel:13800000000")
ck("座机横杠清除", tel_py("010-12345678") == "tel:01012345678")
ck("分机号 # 保留", tel_py("13800000000#123") == "tel:13800000000#123")
ck("引号彻底清除", '"' not in tel_py('138" onx="y') and "'" not in tel_py("138' onx='y"))
ck("尖括号清除", "<" not in tel_py("<script>") and ">" not in tel_py("<script>"))
ck("空格清除", " " not in tel_py("138 0000 0000"))
ck("telHref 实现确实做了字符白名单", "[^0-9+*#]" in tel_n)

print("\n=== 5. 源码不再有裸的 href=tel: + esc( ===")
bad_hits = re.findall(r"href=[\"']tel:[\"']\s*\+\s*esc\(", src)
ck("已无 tel:+esc() 拼接", len(bad_hits) == 0)
ck("telHref 已在源码中定义", "function telHref(" in src)

print("\n" + "=" * 52)
print("全部通过" if OK else "存在失败项")
print("=" * 52)
sys.exit(0 if OK else 1)