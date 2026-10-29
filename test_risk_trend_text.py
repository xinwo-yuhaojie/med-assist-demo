# -*- coding: utf-8 -*-
"""验证 renderRiskTrend 真实输出：用户看到的摘要与提示文案是否正确。

场景：近 14 天录了 2 条血压（均正常）、打了卡但无漏服 → 风险分恒为 0，
      预期文案要说明「已录 N 条、指标正常、曲线持平属正常」，
      而不是让老人以为「没保存」。
"""
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SITE = r"D:\网站专用\网站式老人慢性病用药辅助智能体\my-first-site"
NODE = r"D:\hclaw\node\node.exe"
OK = [True]


def ck(desc, cond, extra=""):
    print(("  PASS  " if cond else "  FAIL  ") + desc + (("  ->  " + str(extra)) if extra != "" else ""))
    OK[0] = OK[0] and bool(cond)


html = io.open(os.path.join(SITE, "index.html"), encoding="utf-8").read()

m_rt = re.search(r"  function renderRiskTrend\(\) \{.*?\n  \}\n", html, re.S)
m_series = re.search(r"  function riskSeries\(records, health, days\) \{.*?\n  \}\n", html, re.S)
m_fmt = re.search(r"  function fmtDate\(d\) \{.*?\n  \}", html, re.S)
m_bp = re.search(r"  function bpStatus\(sys, dia\) \{.*?\n  \}", html, re.S)
m_glu = re.search(r"  function gluStatus\(val, meal\) \{.*?\n  \}", html, re.S)
m_health = re.search(r"EMC\.HEALTH = \{[^;]*\}", html, re.S)
ck("抽到 renderRiskTrend / riskSeries / fmtDate / bpStatus / gluStatus / EMC.HEALTH",
   all([m_rt, m_series, m_fmt, m_bp, m_glu, m_health]))

JS = """
function esc(s){return String(s==null?'':s);}
var EMC = { Chart: { lines: function (labels, series, opt) { return '<svg class="fake"></svg>'; } } };
__HEALTH__
var box = { innerHTML: '' };
function $id(id) { return (id === 'riskTrend') ? box : null; }
__FMT__
__BP__
__GLU__
__SERIES__
var E = { fmtDate: fmtDate, bpStatus: bpStatus, gluStatus: gluStatus, riskSeries: riskSeries };
var S = { records: [], health: [] };
var today = fmtDate(new Date());
var yesterday = fmtDate(new Date(Date.now() - 86400000));
S.health = [
  { type: 'bp', date: today, sys: 128, dia: 78 },
  { type: 'bp', date: yesterday, sys: 132, dia: 82 }
];
S.records = [
  { date: today, mid: 'm1', slot: 'morning', status: 'taken' },
  { date: yesterday, mid: 'm1', slot: 'morning', status: 'taken' }
];
__RT__
renderRiskTrend();
console.log(JSON.stringify({ html: box.innerHTML }));
"""
for _k, _v in [("__FMT__", m_fmt.group(0)), ("__BP__", m_bp.group(0)),
                ("__GLU__", m_glu.group(0)), ("__SERIES__", m_series.group(0)),
                ("__HEALTH__", m_health.group(0)), ("__RT__", m_rt.group(0))]:
    JS = JS.replace(_k, _v)

p = os.path.join(SITE, "_rt_text_test.js")
io.open(p, "w", encoding="utf-8").write(JS)
r = subprocess.run([NODE, p], capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=60)
try:
    os.remove(p)
except Exception:
    pass
if not (r.stdout or "").strip():
    ck("node 执行 renderRiskTrend", False, (r.stderr or "")[:400])
    sys.exit(1)
d = json.loads(r.stdout.strip().splitlines()[-1])
out = d["html"]
plain = re.sub(r"<[^>]+>", "", out)

ck("摘要显示血压 2 条", "血压" in plain and "2" in plain, plain[:120])
ck("提示说明「曲线持平属正常」", "曲线持平属正常" in plain, plain[:200])
ck("提示说明「指标均在正常范围」", "正常范围" in plain)
ck("不再出现旧的笼统文案「这是好事」单独一句",
   "这是好事" not in plain or "已录入血压" in plain)
ck("评分口径提示仍在（0无/1轻/2中/3+重）", "0 无 / 1 轻" in plain or "0无/1轻" in plain)
print("\n--- 实际渲染文本 ---")
print(plain.strip()[:400])
print("\n" + ("全部通过 ✓" if OK[0] else "存在失败项 ✗"))
sys.exit(0 if OK[0] else 1)
