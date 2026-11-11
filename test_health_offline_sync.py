# -*- coding: utf-8 -*-
"""v47 回归测试：云端写不可用时血压必须「立刻可见 + 刷新不丢 + 恢复后自动补传」。

真跑 index.html 中抽取的函数（node 执行），不是静态字符串匹配。
"""
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.abspath(__file__))
NODE = r"D:\hclaw\node\node.exe"
OK = [True]


def ck(d, c, e=""):
    print(("  PASS  " if c else "  FAIL  ") + d + (("  ->  " + str(e)) if e else ""))
    OK[0] = OK[0] and bool(c)


html = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()


def grab(pattern, name):
    m = re.search(pattern, html, re.S)
    if not m:
        ck("抽到函数 %s" % name, False)
        return ""
    return m.group(0)


f_key = grab(r"  function healthKey\(h\) \{.*?\n  \}\n", "healthKey")
f_pget = grab(r"  function pendingGet\(\) \{.*?\n  \}\n", "pendingGet")
f_pset = grab(r"  function pendingSet\(list\) \{.*?\n  \}\n", "pendingSet")
f_pbucket = grab(r"  function pendingBucket\(\) \{.*?\n  \}\n", "pendingBucket")
f_padd = grab(r"  function pendingAdd\(rec\) \{.*?\n  \}\n", "pendingAdd")
f_merge = grab(r"  function mergeHealth\(cloud, local\) \{.*?\n  \}\n", "mergeHealth")
f_add = grab(r"  async function addHealth\(rec\) \{.*?\n  \}\n", "addHealth")
f_sync = grab(r"  async function syncPendingHealth\(\) \{.*?\n  \}\n", "syncPendingHealth")
ck("抽取 8 个函数", all([f_key, f_pget, f_pset, f_pbucket, f_padd, f_merge, f_add, f_sync]))

JS = r"""
var _ls = {}, _events = [], _schedules = 0, _posts = 0, _announce = 0;
var localStorage = { getItem: function(k){ return _ls[k] === undefined ? null : _ls[k]; },
                     setItem: function(k,v){ _ls[k] = String(v); },
                     removeItem: function(k){ delete _ls[k]; } };
var EMCAuth = { getToken: function(){ return 'tok_abcdef123456'; }, isLoggedIn: function(){ return true; } };
var E = { fmtDate: function(){ return '2026-11-11'; } };
var S = { health: [] };
var store = {};
var Bus = { emit: function(){ _events.push(Array.prototype.slice.call(arguments)); } };
function kbAnnounce(){ _announce++; }
function scheduleHealthSync(){ _schedules++; }
var PENDING_KEY = 'emc_v47_health_pending';
__PBUCKET__
__PGET__
__PSET__
__KEY__
__PADD__
__MERGE__
var healthSyncing = false;
__SYNC__
__ADD__

var R = {};
function reset(){ _ls = {}; _events = []; _schedules = 0; _posts = 0; S.health = []; healthSyncing = false; }
function failStore(){ return function(){ var e = new Error('服务暂时开小差了，请稍后再试'); e._status = 500; return Promise.reject(e); }; }

(async function(){
  // 场景 1：云端写 500（线上现状）→ 必须落本地 + 立刻进 S.health + 重绘
  reset();
  var store = { addHealth: failStore(), getHealth: function(){ return Promise.resolve([]); } };
  var rec1 = { type:'bp', sys:126, dia:78, val:null, meal:null, note:'' };
  var e1 = null;
  try { await addHealth(rec1); } catch(e) { e1 = e; }
  R.s1 = { localSaved: !!(e1 && e1.localSaved), pending: (e1 && e1.pendingCount),
           health: S.health.length, events: _events.length, queue: pendingGet().length,
           value: S.health[0] && S.health[0].sys };

  // 场景 2：连续第二天再录一条（不同数值）→ 两条都在
  var rec2 = { type:'bp', sys:130, dia:82, val:null, meal:null, note:'' };
  try { await addHealth(rec2); } catch(e) {}
  R.s2 = { health: S.health.length, queue: pendingGet().length, events: _events.length };

  // 场景 3：同一条重复提交 → 不重复入队、不重复进 S.health
  try { await addHealth({ type:'bp', sys:126, dia:78, val:null, meal:null, note:'' }); } catch(e) {}
  R.s3 = { health: S.health.length, queue: pendingGet().length };

  // 场景 4：刷新（云端返回空数组）→ 合并本地队列后仍应有 2 条
  var cloud = [];
  S.health = mergeHealth(cloud, pendingGet());
  R.s4 = { health: S.health.length, sysList: S.health.map(function(h){return h.sys;}) };

  // 场景 5：云端已有同样的记录 → 补传应直接出队、不重复 POST
  var cloudHas = [{date:'2026-11-11', time:S.health[0].time, type:'bp', sys:126, dia:78, val:null, meal:null},
                  {date:'2026-11-11', time:S.health[1].time, type:'bp', sys:130, dia:82, val:null, meal:null}];
  store = { addHealth: function(){ _posts++; return Promise.resolve([]); },
            getHealth: function(){ return Promise.resolve(cloudHas); } };
  await syncPendingHealth();
  R.s5 = { posts: _posts, queue: pendingGet().length };

  // 场景 6：后端恢复（云端空）→ 自动补传 2 条、队列清空
  reset(); pendingAdd(rec1); pendingAdd(rec2);
  var posted = [];
  store = { addHealth: function(r){ _posts++; posted.push(r.sys); return Promise.resolve([r]); },
            getHealth: function(){ return Promise.resolve([]); } };
  await syncPendingHealth();
  R.s6 = { posts: _posts, posted: posted, queue: pendingGet().length };

  // 场景 7：写成功路径（后端已恢复）→ 用返回数组、触发补传调度
  reset();
  // 后端会用前端传来的 time 原样入库，mock 必须遵循同样行为
  store = { addHealth: function(r){ return Promise.resolve([{ date:r.date, time:r.time, type:r.type, sys:r.sys, dia:r.dia }]); },
            getHealth: function(){ return Promise.resolve([]); } };
  await addHealth({ type:'bp', sys:128, dia:80, val:null, meal:null });
  R.s7 = { health: S.health.length, sys: S.health[0] && S.health[0].sys,
           schedules: _schedules, events: _events.length, queue: pendingGet().length };

  // 场景 8：后端返回旧快照（写入成功但回传旧数组）→ 兜底补一条
  reset();
  store = { addHealth: function(){ return Promise.resolve([]); }, getHealth: function(){ return Promise.resolve([]); } };
  await addHealth(rec1);
  R.s8 = { health: S.health.length, sys: S.health[0] && S.health[0].sys };

  console.log(JSON.stringify(R));
})().catch(function(e){ console.log(JSON.stringify({ERROR: String(e && e.stack || e)})); });
"""
JS = JS.replace("var store = {", "store = {")
for k, v in [("__PBUCKET__", f_pbucket), ("__PGET__", f_pget), ("__PSET__", f_pset),
             ("__KEY__", f_key), ("__PADD__", f_padd), ("__MERGE__", f_merge),
             ("__SYNC__", f_sync), ("__ADD__", f_add)]:
    JS = JS.replace(k, v)

tmp = os.path.join(ROOT, "_v47_run.js")
io.open(tmp, "w", encoding="utf-8").write(JS)
r = subprocess.run([NODE, tmp], capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=90)
try:
    os.remove(tmp)
except Exception:
    pass
if not (r.stdout or "").strip():
    ck("node 执行", False, (r.stderr or "")[:400])
    sys.exit(1)
d = json.loads(r.stdout.strip().splitlines()[-1])
if "ERROR" in d:
    ck("node 执行无异常", False, d["ERROR"][:400])
    sys.exit(1)

print("\n=== 场景验证 ===")
ck("① 写 500 时标记 localSaved 且 pendingCount=1", d["s1"]["localSaved"] is True and d["s1"]["pending"] == 1, d["s1"])
ck("① S.health 立刻有这条血压（126）", d["s1"]["health"] == 1 and d["s1"]["value"] == 126, d["s1"])
ck("① 触发 Bus.emit → 风险趋势图会重绘", d["s1"]["events"] >= 1, d["s1"])
ck("① 队列落盘", d["s1"]["queue"] == 1, d["s1"])
ck("② 连续两条：S.health=2、队列=2、两次重绘", d["s2"]["health"] == 2 and d["s2"]["queue"] == 2 and d["s2"]["events"] >= 2, d["s2"])
ck("③ 重复提交不产生重复记录", d["s3"]["health"] == 2 and d["s3"]["queue"] == 2, d["s3"])
ck("④ 刷新时云端空数组不冲掉本地记录", d["s4"]["health"] == 2, d["s4"])
ck("⑤ 云端已有 → 补传不重复 POST 且队列清空", d["s5"]["posts"] == 0 and d["s5"]["queue"] == 0, d["s5"])
ck("⑥ 后端恢复 → 自动补传 2 条并清空队列", d["s6"]["posts"] == 2 and d["s6"]["queue"] == 0, d["s6"])
ck("⑦ 写成功用返回数组并触发补传调度", d["s7"]["health"] == 1 and d["s7"]["sys"] == 128 and d["s7"]["schedules"] >= 1, d["s7"])
ck("⑧ 后端回传旧数组时兜底补一条", d["s8"]["health"] == 1 and d["s8"]["sys"] == 126, d["s8"])

print("\n=== 静态检查（保存流程 / 加载合并 / 版本号）===")
ck("saveHealth 区分 localSaved 分支", "if (e && e.localSaved)" in html)
ck("提示语为「已保存到本机」", "已保存到本机" in html)
ck("抽出了 clearHealthInputs 复用（成功/离线两处调用）",
   "function clearHealthInputs()" in html and html.count("clearHealthInputs();") == 2)
ck("loadAllInner 合并本地队列", "S.health = mergeHealth(arr(pick(4, [])), pendingGet());" in html)
ck("loadAll 结束后触发补传", "scheduleHealthSync(); } catch (e) {}" in html)
ck("60 秒自动重试已注册", "setInterval(function () { syncPendingHealth(); }, 60000)" in html)
ck("KB_BUILD 已升到 2026111101", "window.KB_BUILD=2026111101;" in html)
sw = io.open(os.path.join(ROOT, "sw.js"), encoding="utf-8").read()
ck("sw.js 已升到 v70", "const VER = 'v70'" in sw)

print("\n" + ("全部通过 ✓" if OK[0] else "存在失败项 ✗"))
sys.exit(0 if OK[0] else 1)
