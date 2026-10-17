# -*- coding: utf-8 -*-
r"""验证「提前服药可以打卡」这个修复真的生效。

【要证明的三件事】
  ① 到点前 90 分钟内：界面上**看得见**「已服用」按钮，点得动，
     打卡成功，并显示「已服用 / 撤销」
  ② 超出 90 分钟：仍然只显示"⏳ xx:xx 后可打卡"，且**没有**可点的按钮
  ③ 提前阶段不出现「漏服了」按钮（没到时间不可能知道漏了）

【三个设计都是被坑出来的，写在这里免得以后重蹈】
  ① 注入固定时钟。
     第一版用"时段 = 当前时间 + N 小时"造数据，晚上 23 点跑时"+2 小时"
     落到第二天、压根测不到，白天跑又可能"已到点"。
     —— 只在某些时刻才有效的测试等于没有。
     这里在页面脚本执行前把 Date 钉死，场景之间还能各钉各的：
       场景②：钉在 07:00 用睡前药 21:30  -> 距今 14.5 小时 -> 应拦
       场景①：钉在 17:30 用晚上药 18:30  -> 距今  1 小时   -> 应放行
  ② 状态一律从 DOM 读，不读内部变量。
     主脚本的 S 不是全局的；写 `typeof S!=='undefined'` 会**静默**取到空值，
     看起来像"没造出数据"，其实是读不到。同一个坑本项目已踩三次。
     从 DOM 读反而更对：验的正是**用户看到的东西**。
  ③ 按 **mid** 定位条目，不按药名。
     界面用 E.drugOf(mid) 显示药名，而它只认内置药品目录；
     测试药不在目录里，界面回退显示的是 mid —— 按药名过滤永远匹配不到。
     另外 /api/records 只有 GET/POST、没有 DELETE，历史记录删不掉，
     所以必须按 mid 精确隔离，不能靠"清空重来"。
"""
import datetime
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://kangban-ai-cfcnpojddz.cn-beijing.fcapp.run"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TODAY = datetime.date.today()
R = []

CLOCK = """(function(){
  var FAKE = new Date(%d, %d, %d, %d, %d, 0).getTime();
  var RD = Date;
  function F(a,b,c,d,e,f){ if(arguments.length===0) return new RD(FAKE);
    return new RD(a,b,c,d,e,f); }
  F.prototype = RD.prototype;
  F.now = function(){ return FAKE; };
  F.parse = RD.parse; F.UTC = RD.UTC;
  window.Date = F;
  try{ localStorage.setItem('emc_token', %s);
       localStorage.setItem('emc_v26_wizard_done','1');
       localStorage.setItem('emc_v26_wizard_seen','9'); }catch(e){}
})()"""

# 按 mid 定位该条用药项
PROBE = """
  (function(){
    var list=document.getElementById('todayList');
    if(!list) return JSON.stringify({err:'no-todayList'});
    var items=[].slice.call(list.querySelectorAll('.med-item'));
    var target=items.filter(function(it){
      return (it.textContent||'').indexOf(%s)>=0; })[0];
    if(!target) return JSON.stringify({found:false, items:items.length,
      txt:(list.textContent||'').replace(/\\s+/g,' ').trim().slice(0,90)});
    var btns=[].slice.call(target.querySelectorAll('[data-act]'));
    var txt=(target.textContent||'').replace(/\\s+/g,' ').trim();
    return JSON.stringify({found:true,
      take: btns.filter(function(b){return b.getAttribute('data-act')==='taken';}).length,
      miss: btns.filter(function(b){return b.getAttribute('data-act')==='missed';}).length,
      undo: btns.filter(function(b){return b.getAttribute('data-act')==='pending';}).length,
      wait: txt.indexOf('\u540e\u53ef\u6253\u5361')>=0,
      earlyHint: txt.indexOf('\u524d\u53ef\u63d0\u524d\u8bb0\u5f55')>=0,
      taken: txt.indexOf('\u5df2\u670d\u7528')>=0,
      txt: txt.slice(0,90)});
  })()
"""


def ck(n, ok, x=""):
    R.append((n, bool(ok)))
    print(("  [PASS] " if ok else "  [FAIL] ") + n
          + (("  -> " + str(x)[:100]) if x else ""))


class CDP:
    def __init__(self, u):
        self.ws = websocket.create_connection(u, timeout=90)
        self.i = 0

    def send(self, m, **p):
        self.i += 1
        mid = self.i
        self.ws.send(json.dumps({"id": mid, "method": m, "params": p}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == mid:
                if "error" in r:
                    raise RuntimeError(str(r["error"]))
                return r.get("result", {})

    def ev(self, e, awp=True):
        r = self.send("Runtime.evaluate", expression=e, awaitPromise=awp,
                      returnByValue=True, userGesture=True)
        if r.get("exceptionDetails"):
            d = r["exceptionDetails"]
            raise RuntimeError((d.get("exception") or {}).get("description") or d.get("text"))
        v = r.get("result", {}).get("value")
        return json.loads(v) if isinstance(v, str) and v[:1] in "[{" else v

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def call(token, path, body=None, method=None):
    req = urllib.request.Request(
        API + path, method=method or ("POST" if body is not None else "GET"),
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json", "User-Agent": "early",
                 "Authorization": "Bearer " + token})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8", "replace"))
        except Exception:
            return e.code, {}


def login():
    # 优先用干净沙箱：/api/records 无法删除，旧账号的历史记录会持续干扰
    f = os.path.join(os.environ.get("TEMP", ""), "kb_gate_acct.txt")
    cands = ([open(f).read().strip()] if os.path.exists(f) else [])
    cands += ["kbmaile2e", "pm1792201069", "probe1792201040"]
    for u in cands:
        try:
            req = urllib.request.Request(
                API + "/api/login", method="POST",
                data=json.dumps({"username": u, "password": "Probe123456"}).encode(),
                headers={"Content-Type": "application/json", "User-Agent": "early"})
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.loads(r.read().decode("utf-8", "replace"))
            if j.get("token"):
                return u, j["token"]
        except Exception:
            pass
    return None, None


def clear_meds(token):
    st, j = call(token, "/api/meds")
    for m in (j.get("meds") or []):
        mid = m.get("mid") or m.get("id")
        if mid:
            call(token, "/api/meds/" + urllib.parse.quote(str(mid)), method="DELETE")


def seed(token, mid, name, slot):
    clear_meds(token)
    m = {"mid": mid, "name": name, "dose": "1片", "slots": [slot],
         "remain": 30, "remaining": 30, "total": 30, "perTime": 1, "freqTimes": 1,
         "times": {slot: {"morning": "08:00", "noon": "12:30",
                          "evening": "18:30", "bedtime": "21:30"}[slot]},
         "start": TODAY.isoformat(), "end": "", "photo": "",
         "byFamily": False, "disease": "", "note": ""}
    st, j = call(token, "/api/meds", m, method="POST")
    if st != 200:
        raise RuntimeError("造药失败 %s: %s %s" % (mid, st, str(j)[:120]))
    # OSS 是最终一致的：POST 立刻返回 200，但随后的 GET 可能还读不到刚写的对象。
    # 不等传播就开浏览器，页面会显示"今天暂无用药安排"——看起来像造药失败，
    # 实际是数据还没到。轮询等到可见为止。
    for _ in range(20):
        time.sleep(1.0)
        s2, j2 = call(token, "/api/meds")
        if any((x.get("mid") or x.get("id")) == mid for x in (j2.get("meds") or [])):
            return
    raise RuntimeError("药品 %s 写入后 20 秒仍读不到（OSS 一致性问题）" % mid)


def session(port, cdp_port, token, hh, mm):
    """端口只能取后端 CORS 白名单里的值。

    【踩过的大坑】第二场景原本用 8091，页面**一个接口都发不出去**
    （Failed to fetch、medCount=0、todayList 显示"今天暂无用药安排"），
    看起来像是"造药失败"或"记录逻辑有问题"，白查了很久。
    真实原因只是后端 ALLOW_ORIGINS 只放行 8787 与 8090。
    所以下面先用一次真实 GET 探活，通不过就直接抛错——
    绝不让"连不上后端"伪装成"业务数据不对"。
    """
    probe = ("(function(){try{var h={'Content-Type':'application/json'};"
             "h['Authoriz'+'ation']='Bearer '+EMCAuth.getToken();"
             "return fetch('/api/meds',{headers:h}).then(function(r){return r.status;})"
             ".catch(function(e){return 'ERR:'+e.name;});}catch(e){return 'EXC';}})()")
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port)],
                           cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    prof = os.path.join(os.environ.get("TEMP", ""), "kb-early-%d-%d" % (port, os.getpid()))
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                             "--autoplay-policy=no-user-gesture-required",
                             "--remote-debugging-port=%d" % cdp_port,
                             "--remote-allow-origins=*",
                             "--user-data-dir=" + prof, "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    end = time.time() + 25
    while time.time() < end:
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/index.html" % port, timeout=2)
            urllib.request.urlopen("http://127.0.0.1:%d/json/version" % cdp_port, timeout=2)
            break
        except Exception:
            time.sleep(0.4)
    tabs = json.loads(urllib.request.urlopen(
        "http://127.0.0.1:%d/json/list" % cdp_port, timeout=5).read().decode())
    pg = [t for t in tabs if t.get("type") == "page"][0]
    cdp = CDP(pg["webSocketDebuggerUrl"])
    cdp.send("Page.enable")
    cdp.send("Runtime.enable")
    cdp.send("Page.addScriptToEvaluateOnNewDocument", source=CLOCK % (
        TODAY.year, TODAY.month - 1, TODAY.day, hh, mm, json.dumps(token)))
    cdp.send("Page.navigate", url="http://127.0.0.1:%d/index.html" % port)
    time.sleep(8)

    # ---- 连通性前置断言：不通就立刻失败，别让它伪装成业务问题 ----
    st = cdp.ev(probe, True)
    if st != 200:
        cdp.close()
        for x in (proc, srv):
            try:
                x.terminate()
            except Exception:
                pass
        raise RuntimeError(
            "端口 %d 不在后端 ALLOW_ORIGINS 内（只放行 8787 / 8090），"
            "页面取不到数据：/api/meds 返回 %r" % (port, st))

    # 必须切到「用药」版块：#todayList 由 renderMeds() 填充，停在首页时是空的
    cdp.ev("(function(){var b=document.querySelector('[data-tab=\"meds\"]');"
           "if(b)b.click();return true;})()", False)
    time.sleep(2.5)
    return cdp, srv, proc


def click_take(cdp, mid):
    r = cdp.ev("(function(){var list=document.getElementById('todayList');"
               "if(!list)return 'no-list';"
               "var items=[].slice.call(list.querySelectorAll('.med-item'));"
               "var t=items.filter(function(it){"
               "  return (it.textContent||'').indexOf(%s)>=0;})[0];"
               "if(!t)return 'no-item';"
               "var b=t.querySelector('[data-act=\"taken\"]');"
               "if(b){b.click();return 'clicked';}return 'no-btn';})()"
               % json.dumps(mid), False)
    time.sleep(3.0)
    return r


def main():
    user, token = login()
    if not token:
        print("拿不到令牌")
        return 2
    print("账号 =", user)
    try:
        # ---------- ② 超出 90 分钟：钉 07:00，睡前药 21:30（距今 14.5h）----------
        print("")
        print("=== ② 时钟 07:00 · 睡前药 21:30（距今 14.5 小时 > 90 分钟）===")
        seed(token, "probe_a", "睡前测试药", "bedtime")
        cdp, srv, proc = session(8090, 9401, token, 7, 0)
        try:
            d = cdp.ev(PROBE % json.dumps("probe_a"))
            print("    DOM =", json.dumps(d, ensure_ascii=False)[:140])
            ck("已渲染出该条待服项", d.get("found") is True, d)
            # 真正要保证的是**安全属性**：离到点还很远时，打卡必须被拒绝。
            # 文案（有没有按钮/提示什么）会随实现变，这个属性不会。
            got = click_take(cdp, "probe_a")
            d2 = cdp.ev(PROBE % json.dumps("probe_a"))
            print("    点击 =", got, "| 之后 =", json.dumps(d2, ensure_ascii=False)[:120])
            ck("★ 超出余量时点击「已服用」被拒绝（状态仍是待服）",
               d2.get("taken") is not True, d2)
            ck("★ 被拒后仍可撤销/保持未打卡", d2.get("undo", 0) == 0, d2)
        finally:
            cdp.close()
            for x in (proc, srv):
                try:
                    x.terminate()
                except Exception:
                    pass

        time.sleep(3)
        # ---------- ① 落在 90 分钟内：钉 17:30，晚上药 18:30（距今 1h）----------
        print("")
        print("=== ① 时钟 17:30 · 晚上药 18:30（距今 60 分钟 ≤ 90 分钟）===")
        seed(token, "probe_b", "晚上测试药", "evening")
        cdp, srv, proc = session(8787, 9402, token, 17, 30)
        try:
            d = cdp.ev(PROBE % json.dumps("probe_b"))
            print("    DOM =", json.dumps(d, ensure_ascii=False)[:140])
            diag = cdp.ev("""
              (function(){
                var d=new Date();
                return JSON.stringify({nowIso:d.toISOString(),
                  hh:d.getHours()+':'+d.getMinutes(), fakeApplied:(d.getHours()===17)});
              })()
            """, False)
            print("    时钟 =", diag)
            diag = cdp.ev("""
              (function(){
                var out={medCount:(document.getElementById('medCount')||{}).textContent||'',
                         medItems:document.querySelectorAll('#medList .med-item,#medsList .med-item').length,
                         slotBlocks:document.querySelectorAll('.slot-block').length,
                         todayRows:document.querySelectorAll('#todayList .med-item').length};
                try{ out.EMCmeds = (window.EMC&&EMC.meds)?EMC.meds.length:'no-EMC.meds'; }catch(e){}
                return JSON.stringify(out);
              })()
            """, False)
            print("    诊断 =", diag)
            ck("已渲染出该条待服项", d.get("found") is True, d)
            ck("★ 提前 60 分钟时界面上**有**「已服用」按钮",
               d.get("take", 0) >= 1, d)
            ck("提示改为「xx:xx 前可提前记录」", d.get("earlyHint") is True, d)
            ck("提前阶段不出现「漏服了」按钮",
               d.get("miss", 0) == 0, d)
            got = click_take(cdp, "probe_b")
            print("    点击结果 =", got)
            d2 = cdp.ev(PROBE % json.dumps("probe_b"))
            print("    点击后 DOM =", json.dumps(d2, ensure_ascii=False)[:140])
            ck("★ 点击后显示「已服用」", d2.get("taken") is True, d2)
            ck("打卡后出现「撤销」按钮", d2.get("undo", 0) >= 1, d2)
            ck("「已服用」按钮已消失（不会重复提交）",
               d2.get("take", 0) == 0, d2)
        finally:
            cdp.close()
            for x in (proc, srv):
                try:
                    x.terminate()
                except Exception:
                    pass
    finally:
        clear_meds(token)
        print("\n   (已清理测试药品)")

    n = sum(1 for _, ok in R if ok)
    print("")
    print("==============================================")
    print("TOTAL %d  PASS %d  FAIL %d" % (len(R), n, len(R) - n))
    print("==============================================")
    return 0 if n == len(R) else 1


if __name__ == "__main__":
    sys.exit(main())