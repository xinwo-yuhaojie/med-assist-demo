# -*- coding: utf-8 -*-
"""版本号一致性检查（v35 加固）
背景：v35 修掉「点任意处都弹看板密码」后，用户仍看到该现象 ——
因为 KB_BUILD 自 v32 起没升过，Service Worker 与"发现新版本"全靠它判断，
号不动，用户就一直用带 bug 的旧缓存。修好代码 != 用户拿到新代码。
检查：两处 KB_BUILD 一致 / 比 git 上次提交更大 / sw.js 版本非初始值。"""
import io, re, sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"D:\网站专用\my-first-site"
OK = True
def ck(d, c):
    global OK
    print(("  PASS  " if c else "  FAIL  ") + d); OK = OK and c

idx = io.open(ROOT + r"\index.html", encoding="utf-8", newline="").read()
sw = io.open(ROOT + r"\sw.js", encoding="utf-8", newline="").read()

print("=== 1. index.html 两处 KB_BUILD 一致 ===")
a = re.findall(r"window\.KB_BUILD=(\d+);", idx)
b = re.findall(r"var KB_BUILD = (\d+);", idx)
print("   head 内: %s   体内: %s" % (a or "无", b or "无"))
ck("两处存在且一致", bool(a) and bool(b) and a[0] == b[0])
cur = int(a[0]) if a else 0

print("\n=== 2. 必须比 git 上次提交更大（防忘记升版）===")
try:
    out = subprocess.run(["git","show","HEAD:index.html"], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    old = re.findall(r"window\.KB_BUILD=(\d+);", out)
    oldv = int(old[0]) if old else 0
    print("   上次: %s   本次: %s" % (oldv, cur))
    ck("已递增 (%d > %d)" % (cur, oldv), cur > oldv)
except Exception as e:
    print("   (跳过: %s)" % e)

print("\n=== 3. sw.js 缓存版本 ===")
m = re.search(r"const VER = '([^']+)'", sw)
ver = m.group(1) if m else "无"
print("   VER = %s" % ver)
ck("有版本号", ver != "无")
ck("非初始值（否则旧缓存永不失效）", ver not in ("v1","v0",""))

print("\n=== 4. 字符编码声明必须在前 1024 字节内 ===")
# 浏览器只认前 1024 字节里的 charset 声明。原来的声明在第 1162 行（<body> 中段），
# 会被忽略 -> 服务端不带 charset 时退回系统区域设置 -> 简体中文 Windows 上一片乱码。
head = idx.encode("utf-8")[:1024]
ck("前 1024 字节内有 <meta charset=utf-8>",
   re.search(rb'<meta\s+charset=["\']?utf-8', head, re.I) is not None)
allm = [(mm.start(), idx.count("\n", 0, mm.start()) + 1)
        for mm in re.finditer(r'<meta\s+charset=["\']?utf-8', idx, re.I)]
print("   全部 charset 声明(字节偏移,行号) = %s" % allm)
ck("声明位置在 <head> 内（行号 < 100）", bool(allm) and allm[0][1] < 100)

print("\n" + "="*50)
print("全部通过" if OK else "有问题：代码改了但版本号没升，用户仍拿旧版！")
print("="*50)
sys.exit(0 if OK else 1)
