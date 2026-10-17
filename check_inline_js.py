# -*- coding: utf-8 -*-
"""从 index.html 里抽出所有内联 <script> 体，逐段用真实 JS 解析器校验。

为什么必须真解析：`jscheck.py` 只查括号配对，
而本轮修的两个笔误（`if (old; old.parentNode)`、丢弃 closest() 返回值）
括号全是配对的，只有真正的解析器才报得出来。
这里用 Chrome 之外零依赖的办法：node --check 逐段过一遍。
"""
import os
import re
import subprocess
import sys
import tempfile

NODE = r"C:\Users\d1513\.workbuddy\binaries\node\versions\22.22.2-3\node.exe"
HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')

if not os.path.exists(NODE):
    print('!! node not found:', NODE)
    sys.exit(2)

html = open(HTML, encoding='utf-8').read()
blocks = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S)
print('inline script blocks =', len(blocks))

bad = 0
tmpdir = tempfile.mkdtemp(prefix='kbjs-')
for i, b in enumerate(blocks):
    p = os.path.join(tmpdir, 'b%03d.js' % i)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(b)
    r = subprocess.run([NODE, '--check', p], capture_output=True, text=True)
    if r.returncode != 0:
        bad += 1
        print('\n--- block #%d FAILED ---' % i)
        print(r.stderr.strip()[:900])
        # 打印出错行在原文件里的行号，方便定位
        for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>', html):
            pass
print('\n%s  blocks ok: %d / %d' % ('ALL PASS' if not bad else 'HAS FAILURES',
                                     len(blocks) - bad, len(blocks)))
sys.exit(1 if bad else 0)