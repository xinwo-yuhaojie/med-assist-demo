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
f_owner = grab(r"  function pendingOwner\(\) \{.*?\n  \}\n", "pendingOwner")
f_valid = grab(r"  function validHealthRec\(h\) \{.*?\n  \}\n", "validHealthRec")
f_migrate = grab(r"  function migratePendingBuckets\(\) \{.*?\n  \}\n", "migratePendingBuckets")
ck("抽取 11 个函数", all([f_key, f_pget, f_pset, f_pbucket, f_padd, f_merge, f_add, f_sync,
                        f_owner, f_valid, f_migrate]))

JS = r"""
var _ls = {}, _events = [], _schedules = 0, _posts = 0, _announce = 0;
var localStorage = { getItem: function(k){ return _ls[k] === undefined ? null : _ls[k]; },
                     setItem: function(k,v){ _ls[k] = String(v); },
                     removeItem: function(k){ delete _ls[k]; } };
var EMCAuth = { getToken: function(){ return 'tok_abcdef123456'; }, isLoggedIn: function(){ return true; } };
var E = { fmtDate: function(){ return '2026-11-11'; } };
var S = { health: [], profile: { username: 'testuser' } };
var store = {};
var Bus = { emit: function(){ _events.push(Array.prototype.slice.call(arguments)); } };
function kbAnnounce(){ _announce++; }
function scheduleHealthSync(){ _schedules++; }
var PENDING_KEY = 'emc_v47_health_pending';
var PENDING_MAX = 500;
__POWNER__
__PBUCKET__
__VALID__
__PGET__
__PSET__
__KEY__
__PADD__
__MERGE__
var pendingMigrated = false;
__MIGRATE__
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

  // v48-①：4xx 永久拒绝 → 不入队、不标 localSaved（否则会无限重试并谎称待同步）
  reset();
  store = { addHealth: function(){ var e = new Error('测量数值不在合理范围'); e._status = 400; return Promise.reject(e); },
            getHealth: function(){ return Promise.resolve([]); } };
  var e4 = null;
  try { await addHealth({type:'bp', sys:126, dia:78, val:null, meal:null}); } catch(e){ e4 = e; }
  R.s9 = { localSaved: !!(e4 && e4.localSaved), queue: pendingGet().length,
           health: S.health.length, status: e4 && e4._status };

  // v48-②：localStorage 写满 → 必须标记 storageFull，绝不能宣称已保存
  reset();
  var origSet = localStorage.setItem;
  localStorage.setItem = function(){ throw new Error('QuotaExceeded'); };
  store = { addHealth: failStore(), getHealth: function(){ return Promise.resolve([]); } };
  var e5 = null;
  try { await addHealth({type:'bp', sys:128, dia:80, val:null, meal:null}); } catch(e){ e5 = e; }
  localStorage.setItem = origSet;
  R.s10 = { storageFull: !!(e5 && e5.storageFull), localSaved: !!(e5 && e5.localSaved) };

  // v48-③：云端记录不含 meal，去重键仍须匹配 → 不重复 POST
  reset();
  pendingAdd({date:'2026-11-11', time:'08:00', type:'glu', val:6.2, meal:'post'});
  var cloudNoMeal = [{date:'2026-11-11', time:'08:00', type:'glu', val:6.2}];
  store = { addHealth: function(){ _posts++; return Promise.resolve([]); },
            getHealth: function(){ return Promise.resolve(cloudNoMeal); } };
  await syncPendingHealth();
  R.s11 = { posts: _posts, queue: pendingGet().length };

  // v48-④：稳定账号分桶——换 token 后队列必须还在（初版按 token 会丢）
  reset();
  pendingAdd({date:'2026-11-11', time:'09:00', type:'bp', sys:120, dia:75});
  var origTok = EMCAuth.getToken;
  EMCAuth.getToken = function(){ return 'brand_new_token_zzzz'; };
  R.s12 = { queue: pendingGet().length, bucket: pendingBucket() };
  EMCAuth.getToken = origTok;

  // v48-⑤：非法队列条目被过滤（畸形 date / 非数值 / 正常记录）
  reset();
  _ls[pendingBucket()] = JSON.stringify([
    {date:'<img src=x onerror=1>', time:'08:00', type:'bp', sys:120, dia:80},
    {date:'2026-11-11', time:'08:00', type:'bp', sys:'abc', dia:80},
    {date:'2026-11-11', time:'08:00', type:'bp', sys:120, dia:80}
  ]);
  R.s13 = { queue: pendingGet().length, first: pendingGet()[0] && pendingGet()[0].sys };

  console.log(JSON.stringify(R));
})().catch(function(e){ console.log(JSON.stringify({ERROR: String(e && e.stack || e)})); });
"""
JS = JS.replace("var store = {", "store = {")
for k, v in [("__POWNER__", f_owner), ("__PBUCKET__", f_pbucket), ("__VALID__", f_valid),
             ("__PGET__", f_pget), ("__PSET__", f_pset), ("__MIGRATE__", f_migrate),
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

print("\n=== v48 漏洞回归场景 ===")
ck("⑨ 4xx 永久拒绝不入队、不谎称待同步",
   d["s9"]["status"] == 400 and d["s9"]["localSaved"] is False
   and d["s9"]["queue"] == 0 and d["s9"]["health"] == 0, d["s9"])
ck("⑩ 存储写满时标记 storageFull、不标 localSaved",
   d["s10"]["storageFull"] is True and d["s10"]["localSaved"] is False, d["s10"])
ck("⑪ 云端无 meal 仍能去重（不重复 POST）",
   d["s11"]["posts"] == 0 and d["s11"]["queue"] == 0, d["s11"])
ck("⑫ 换 token 后离线队列仍在（稳定账号分桶）",
   d["s12"]["queue"] == 1 and "testuser" in d["s12"]["bucket"], d["s12"])
ck("⑬ 非法队列条目被过滤，仅保留合法一条",
   d["s13"]["queue"] == 1 and d["s13"]["first"] == 120, d["s13"])

print("\n=== 静态检查（保存流程 / 加载合并 / 后端 / 版本号）===")
ck("saveHealth 区分 localSaved 分支", "if (e && e.localSaved)" in html)
ck("提示语为「已保存到本机」", "已保存到本机" in html)
ck("存储失败有专门提示", "if (e && e.storageFull)" in html and "本机存储空间不足" in html)
ck("4xx 短路不入队", "e._status >= 400 && e._status < 500" in html)
ck("渲染异常不冒泡出 catch", "console.warn('[EMC] renderHealth 失败'" in html)
ck("抽出了 clearHealthInputs 复用（成功/离线两处调用）",
   "function clearHealthInputs()" in html and html.count("clearHealthInputs();") == 2)
ck("loadAllInner 合并本地队列", "S.health = mergeHealth(arr(pick(4, [])), pendingGet());" in html)
ck("kbLiveTick 回填也合并队列", "var mergedH = mergeHealth(health, pendingGet());" in html)
ck("loadAll 结束后触发补传", "scheduleHealthSync(); } catch (e) {}" in html)
ck("后台标签页不轮询", "if (document.hidden) return;" in html)
ck("Bus.emit 异常留痕", "console.warn('[Bus] handler error: '" in html)
ck("Bus.emit 传对象而非 null", "Bus.emit('health', { remote: true })" in html)
ck("renderHealth 字段已转义", "esc(h.date) + ' ' + esc(h.time || '')" in html
   and "'血压 ' + esc(h.sys)" in html)
ck("游客迁移去重键已修", "var hk = healthKey(h);" in html and "h.value || ''" not in html)
ck("60 秒自动重试已注册", "syncPendingHealth();\n    }, 60000)" in html)
ck("KB_BUILD 已升到 2026111102", "window.KB_BUILD=2026111102;" in html)
sw = io.open(os.path.join(ROOT, "sw.js"), encoding="utf-8").read()
ck("sw.js 已升到 v71", "const VER = 'v71'" in sw)

server = io.open(os.path.join(ROOT, "..", "backend", "fc-web", "server.js"), encoding="utf-8").read()
ck("后端跳过 null 空值（P0：Number(null)=0 误判越界）",
   "b[k] === undefined || b[k] === null || b[k] === ''" in server)
ck("后端 HP_RANGE 补 hr", "hr: [30, 250]" in server)
ck("后端白名单补 hr / meal", "'pulse', 'hr', 'meal', 'note'" in server)

print("\n" + ("全部通过 ✓" if OK[0] else "存在失败项 ✗"))
sys.exit(0 if OK[0] else 1)
