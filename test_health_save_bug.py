# -*- coding: utf-8 -*-
"""回归测试：血压保存后界面不更新（v45 修复）。

覆盖三件事：
  ① 后端 /api/health POST 必须返回**事务提交后**的数组（uh.health），不是事务外的旧快照；
  ② 前端 addHealth 必须做兜底：即使后端返回旧数组，S.health 也要含刚写入的记录，且不重复；
  ③ renderRiskTrend 的摘要必须按「近 14 天」窗口统计，而不是全量历史。
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
SERVER = os.path.join(ROOT, "backend", "fc-web", "server.js")
NODE = r"D:\hclaw\node\node.exe"
OK = [True]


def ck(desc, cond, extra=""):
    print(("  PASS  " if cond else "  FAIL  ") + desc + (("  ->  " + str(extra)) if extra != "" else ""))
    OK[0] = OK[0] and bool(cond)


html = io.open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
js = io.open(SERVER, encoding="utf-8").read()

print("=== ① 后端：POST /api/health 返回值 ===")
m = re.search(r"if \(p\.endsWith\('/api/health'\)\) \{(.*?)\n    \}\n", js, re.S)
ck("找到 /api/health 路由", m is not None)
if m:
    block = m.group(1)
    post = block[block.find("method === 'POST'"):]
    ck("POST 分支使用事务返回值 uh.health", "health: uh.health" in post)
    ck("POST 分支不再返回事务外的旧快照 user.health", "health: user.health" not in post)

print("\n=== ② 前端 addHealth 兜底 ===")
m_add = re.search(r"  async function addHealth\(rec\) \{.*?\n  \}\n", html, re.S)
ck("找到 addHealth 实现", m_add is not None)
if m_add:
    src = m_add.group(0)
    ck("addHealth 里有兜底写入（has 判定）", "if (!has) S.health = S.health.concat([rec]);" in src)
    ck("兜底按 日期+时间+类型+数值 匹配", "h.date === rec.date && h.time === rec.time" in src)

    # 真跑一遍：注入假的 store/S/Bus，跑真实 addHealth 代码
    JS = """
var S = { health: [] };
var E = { fmtDate: function (d) {
  var y = d.getFullYear(), m = d.getMonth() + 1, day = d.getDate();
  return y + '-' + (m < 10 ? '0' + m : m) + '-' + (day < 10 ? '0' + day : day);
} };
var Bus = { emit: function () {} };
var kbAnnounce = function () {};
var store = { addHealth: function (rec) { return Promise.resolve(STALE); } };
var STALE = [];
%s
(async function () {
  var rec = { type: 'bp', sys: 128, dia: 78, val: null, meal: null, note: '' };
  await addHealth(rec);
  var n1 = S.health.length;
  var hasNew = S.health.some(function (h) { return h.type === 'bp' && h.sys === 128; });
  // 第二次调用：后端这次返回含新记录的数组
  STALE = [{ type: 'bp', sys: 128, dia: 78, date: S.health[0].date, time: S.health[0].time }];
  await addHealth({ type: 'bp', sys: 130, dia: 80, val: null, meal: null, note: '' });
  var n2 = S.health.length;
  console.log(JSON.stringify({ n1: n1, hasNew: hasNew, n2: n2 }));
})();
""" % src
    p = os.path.join(SITE, "_health_save_test.js")
    io.open(p, "w", encoding="utf-8").write(JS)
    r = subprocess.run([NODE, p], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    try:
        os.remove(p)
    except Exception:
        pass
    if not (r.stdout or "").strip():
        ck("node 执行 addHealth", False, (r.stderr or "")[:300])
    else:
        d = json.loads(r.stdout.strip().splitlines()[-1])
        ck("后端返回旧数组时，S.health 仍含新记录（兜底生效）", d["hasNew"] is True, d)
        ck("后端返回正确数组时，不产生重复条目", d["n2"] == 2, "n2=%s（期望 2）" % d["n2"])

print("\n=== ③ renderRiskTrend 的 14 天窗口口径 ===")
m_cnt = re.search(r"(var from14 = .*?var glu14 = .*?;\n)", html, re.S)
ck("找到近 14 天窗口统计块", m_cnt is not None)
if m_cnt:
    ck("统计块里定义了 from14 窗口起点", "var from14 = E.fmtDate(" in m_cnt.group(1))
    ck("recs14 按窗口过滤", "recs14 = (S.records || []).filter" in m_cnt.group(1))
    ck("hsAll 按窗口过滤", "hsAll = (S.health || []).filter" in m_cnt.group(1))

    JS2 = """
function E_fmtDate(d) {
  var y = d.getFullYear(), m = d.getMonth() + 1, day = d.getDate();
  return y + '-' + (m < 10 ? '0' + m : m) + '-' + (day < 10 ? '0' + day : day);
}
var E = { fmtDate: E_fmtDate };
var today = new Date();
var old = E.fmtDate(new Date(today.getTime() - 20 * 86400000));
var recent = E.fmtDate(new Date(today.getTime() - 2 * 86400000));
var S = { records: [], health: [
  { type: 'bp', date: old, sys: 150, dia: 95 },
  { type: 'bp', date: recent, sys: 128, dia: 78 }
]};
%s
console.log(JSON.stringify({ hp14: hp14, glu14: glu14, total: S.health.length }));
""" % m_cnt.group(1)
    p2 = os.path.join(SITE, "_win_test.js")
    io.open(p2, "w", encoding="utf-8").write(JS2)
    r2 = subprocess.run([NODE, p2], capture_output=True, text=True,
                        encoding="utf-8", errors="replace", timeout=60)
    try:
        os.remove(p2)
    except Exception:
        pass
    if not (r2.stdout or "").strip():
        ck("node 执行窗口统计", False, (r2.stderr or "")[:300])
    else:
        d2 = json.loads(r2.stdout.strip().splitlines()[-1])
        ck("20 天前的那条血压被排除在「近14天」之外", d2["hp14"] == 1, d2)
        ck("2 天前的那条被计入", d2["hp14"] >= 1, d2)

print("\n" + ("全部通过 ✓" if OK[0] else "存在失败项 ✗"))
sys.exit(0 if OK[0] else 1)
