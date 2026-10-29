# -*- coding: utf-8 -*-
"""看板血压/血糖列回归测试（v46）。

要验三件事：
  ① 近 7 天有测量的账户 → 显示均值 + 次数（+偏高标记）；
  ② 3 年内测过但近 7 天没测的账户 → 显示**最近一次**的值与日期（不再 null/null）；
  ③ 从未测过的账户 → 显示 —；
  ④ 后端 perUser 必须给出看板显示所需的全部字段（含 3 年历史与最近一次）。
"""
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"D:\网站专用\网站式老人慢性病用药辅助智能体"
SITE = os.path.join(ROOT, "my-first-site")
NODE = r"D:\hclaw\node\node.exe"
OK = [True]


def ck(desc, cond, extra=""):
    print(("  PASS  " if cond else "  FAIL  ") + desc + (("  ->  " + str(extra)) if extra != "" else ""))
    OK[0] = OK[0] and bool(cond)


html = io.open(os.path.join(SITE, "dashboard.html"), encoding="utf-8").read()
js = io.open(os.path.join(ROOT, "backend", "fc-web", "server.js"), encoding="utf-8").read()

print("=== ① 后端 perUser 字段完整性 ===")
for f in ["bpCount", "bpCount7", "bpSys7", "bpDia7", "bpLast", "bpHigh", "bpHighAll", "bpAnomaly7",
          "gluCount", "gluCount7", "glu7", "gluLast", "gluHigh", "gluHighAll", "gluAnomaly7"]:
    ck("perUser 含字段 %s" % f, ("%s:" % f) in js)

print("\n=== ② 后端取值容错（历史字符串型血压不被丢弃）===")
ck("使用 numOf 做数值归一", "const numOf = function (v)" in js)
# 只看代码行（排除注释里的说明文字）
code_only = "\n".join(l for l in js.splitlines() if not l.strip().startswith("*") and not l.strip().startswith("/*"))
ck("血压过滤已改为 numOf 判定",
   "numOf(h.sys) != null" in code_only and "typeof h.sys === 'number'" not in code_only)

print("\n=== ③ 前端显示逻辑（真跑 dashboard 的 fmtBpCell/fmtGluCell）===")
m_bp = re.search(r"    function fmtBpCell\(p\) \{.*?\n    \}\n", html, re.S)
m_glu = re.search(r"    function fmtGluCell\(p\) \{.*?\n    \}\n", html, re.S)
ck("抽到 fmtBpCell / fmtGluCell", bool(m_bp and m_glu))
if m_bp and m_glu:
    JS = """
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
%s
%s
// 三种账户
var recent = { bpSys7: 128.5, bpDia7: 78, bpCount7: 3, bpCount: 12, bpHigh: true, bpLast: {date:'2026-10-29', sys:130, dia:80} };
var stale  = { bpSys7: null, bpDia7: null, bpCount7: 0, bpCount: 12, bpHigh: false, bpHighAll: true,
               bpLast: {date:'2026-09-12', sys:150, dia:95} };
var none   = { bpSys7: null, bpDia7: null, bpCount: 0, bpLast: null };
var gRecent = { glu7: 6.2, gluCount7: 2, gluCount: 9, gluHigh: false, gluLast: {date:'2026-10-29', val:6.4} };
var gStale  = { glu7: null, gluCount7: 0, gluCount: 9, gluHigh: false, gluHighAll: false,
                gluLast: {date:'2026-08-03', val:7.1} };
var gNone   = { glu7: null, gluCount: 0, gluLast: null };
console.log(JSON.stringify({
  bp_recent: fmtBpCell(recent), bp_stale: fmtBpCell(stale), bp_none: fmtBpCell(none),
  glu_recent: fmtGluCell(gRecent), glu_stale: fmtGluCell(gStale), glu_none: fmtGluCell(gNone)
}));
""" % (m_bp.group(0), m_glu.group(0))
    p = os.path.join(SITE, "_dash_bp_test.js")
    io.open(p, "w", encoding="utf-8").write(JS)
    r = subprocess.run([NODE, p], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    try:
        os.remove(p)
    except Exception:
        pass
    if not (r.stdout or "").strip():
        ck("node 执行看板渲染", False, (r.stderr or "")[:300])
    else:
        d = json.loads(r.stdout.strip().splitlines()[-1])
        print("   近7天有值 :", d["bp_recent"])
        print("   仅历史   :", d["bp_stale"])
        print("   从未测过 :", d["bp_none"])
        ck("近7天账户显示均值与次数", "128.5/78" in d["bp_recent"] and "3次" in d["bp_recent"], d["bp_recent"])
        ck("近7天账户偏高有标记", "偏高" in d["bp_recent"])
        ck("仅历史账户显示最近一次的值", "150/95" in d["bp_stale"], d["bp_stale"])
        ck("仅历史账户显示日期", "09-12" in d["bp_stale"], d["bp_stale"])
        ck("仅历史账户标记曾偏高", "曾偏高" in d["bp_stale"])
        ck("从未测过显示 —", d["bp_none"].strip().startswith("—") or "—" in d["bp_none"])
        ck("**任何情况都不出现 null**",
           "null" not in d["bp_recent"] and "null" not in d["bp_stale"] and "null" not in d["bp_none"])
        ck("血糖近7天显示均值与次数", "6.2" in d["glu_recent"] and "2次" in d["glu_recent"], d["glu_recent"])
        ck("血糖仅历史显示最近一次", "7.1" in d["glu_stale"] and "08-03" in d["glu_stale"], d["glu_stale"])
        ck("血糖从未测过显示 —", "—" in d["glu_none"])

print("\n=== ④ 旧实现已移除（null/null 的写法不能再出现）===")
# 旧实现特征：在 map 渲染块里直接按 p.bpCount 判断并拼接（不做 null 判断）
ck("旧的直拼写法已不在渲染块",
   "esc(String(p.bpSys7) + '/' + String(p.bpDia7))\n" not in html
   and html.count("esc(String(p.bpSys7) + '/' + String(p.bpDia7))") == 1)

print("\n" + ("全部通过 ✓" if OK[0] else "存在失败项 ✗"))
sys.exit(0 if OK[0] else 1)
