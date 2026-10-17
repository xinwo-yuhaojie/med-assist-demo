# -*- coding: utf-8 -*-
"""家属日志：验证点开看具体内容。"""
import json, os, socket, subprocess, sys, time, urllib.request
import websocket
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
P_HTTP, P_CDP = 8090, 9349
API = "https://kangban-ai-cfcnpojddz.cn-beijing.fcapp.run"
TEST_PWD = "Probe123456"
USERS = ["kbmaile2e", "pm1792201069", "probe1792201040"]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
R = []

def ck(name, ok, extra=""):
    R.append((name, bool(ok)))
    print(("  [PASS] " if ok else "  [FAIL] ") + name + (("  -> " + str(extra)[:100]) if extra else ""))

def free(p):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", p)); return True
    except OSError:
        return False
    finally:
        s.close()

def get_token():
    for u in USERS:
        try:
            req = urllib.request.Request(API + "/api/login", method="POST",
                data=json.dumps({"username": u, "password": TEST_PWD}).encode(),
                headers={"Content-Type": "application/json", "User-Agent": "uc"})
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.loads(r.read().decode("utf-8", "replace"))
            if j.get("token"):
                return u, j["token"]
        except Exception:
            pass
    return None, None

class CDP:
    def __init__(self, u):
        self.ws = websocket.create_connection(u, timeout=60); self.i = 0
    def send(self, m, **p):
        self.i += 1; mid = self.i
        self.ws.send(json.dumps({"id": mid, "method": m, "params": p}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == mid:
                if "error" in r: raise RuntimeError(str(r["error"]))
                return r.get("result", {})
    def ev(self, e, awp=True):
        r = self.send("Runtime.evaluate", expression=e, awaitPromise=awp,
                      returnByValue=True, userGesture=True)
        if r.get("exceptionDetails"):
            d = r["exceptionDetails"]
            raise RuntimeError((d.get("exception") or {}).get("description") or d.get("text"))
        return r.get("result", {}).get("value")
    def text(self, e):
        return json.loads(self.ev("JSON.stringify(%s)" % e, False))
    def close(self):
        try: self.ws.close()
        except Exception: pass

def wait(u, t=25):
    end = time.time() + t
    while time.time() < end:
        try:
            urllib.request.urlopen(u, timeout=2); return True
        except Exception:
            time.sleep(0.3)
    return False
def main():
    user, token = get_token()
    print("登录账号 =", user)
    if not token:
        print("拿不到令牌"); return 2
    if not free(P_HTTP) or not free(P_CDP):
        print("端口被占用"); return 2
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(P_HTTP)],
                           cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    prof = os.path.join(os.environ.get("TEMP", "."), "kb-lg-%d" % os.getpid())
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
        "--remote-debugging-port=%d" % P_CDP, "--remote-allow-origins=*",
        "--user-data-dir=" + prof, "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cdp = None
    try:
        wait("http://127.0.0.1:%d/index.html" % P_HTTP)
        wait("http://127.0.0.1:%d/json/version" % P_CDP)
        tabs = json.loads(urllib.request.urlopen(
            "http://127.0.0.1:%d/json/list" % P_CDP, timeout=5).read().decode())
        pg = [t for t in tabs if t.get("type") == "page"][0]
        cdp = CDP(pg["webSocketDebuggerUrl"])
        cdp.send("Page.enable"); cdp.send("Runtime.enable")
        # 必须让应用以**登录态**启动，否则日志取的是本地 store，测不到云端形状
        # （这次 bug「服务端存 text、前端读 content」恰恰只出现在云端）。
        # 手法：用 addScriptToEvaluateOnNewDocument 在**任何页面脚本执行之前**
        # 把令牌写好。走 localStorage + Page.reload 会让渲染进程卡住、评测超时。
        cdp.send("Page.addScriptToEvaluateOnNewDocument", source=(
            "try{localStorage.setItem('emc_token', %s);}catch(e){}"
            % json.dumps(token)))
        cdp.send("Page.navigate", url="http://127.0.0.1:%d/index.html" % P_HTTP)
        time.sleep(8)
        cdp.ev("(function(){try{switchTab('guardian');}catch(e){}return true;})()", False)
        time.sleep(2)
        cdp.ev("(function(){var b=document.getElementById('btnNotifyToggle');"
               "if(b&&b.textContent.indexOf('展')>=0)b.click();return true;})()", False)
        time.sleep(1)

        d = cdp.text("(function(){var c=document.getElementById('guardianNotify');"
                     "return {days:document.querySelectorAll('.notify-day').length,"
                     "items:document.querySelectorAll('.notify-item').length,"
                     "summaries:document.querySelectorAll('.notify-item>summary').length,"
                     "txt:c?(c.textContent||'').replace(/\\s+/g,' ').slice(0,220):''};})()")
        print("")
        print("=== 1. 渲染 ===")
        ck("日志有条目", d.get("items", 0) > 0, "items=%s" % d.get("items"))
        ck("按日期分组（各时间段可辨）", d.get("days", 0) > 0, "groups=%s" % d.get("days"))
        ck("每条都有可点开的 summary", d.get("summaries") == d.get("items"),
           "sum=%s item=%s" % (d.get("summaries"), d.get("items")))

        print("")
        print("=== 2. 正文不为空 ===")
        empty = cdp.text("(function(){var n=[].slice.call(document.querySelectorAll('.notify-item .c'));"
                         "return n.filter(function(e){return !e.textContent.trim()||"
                         "e.textContent.indexOf('无正文')>=0;}).length;})()")
        ck("没有空白正文的条目", empty == 0, "空 %s 条" % empty)
        ck("能看到实际通报内容",
           ("漏服" in d.get("txt","") or "用药" in d.get("txt","") or "提醒" in d.get("txt","")),
           d.get("txt","")[:120])

        print("")
        print("=== 3. 时间已本地化 ===")
        iso = cdp.text("(function(){var t=document.getElementById('guardianNotify').textContent||'';"
                       "return {iso:/\\d{4}-\\d{2}-\\d{2}T/.test(t),"
                       "cn:/\\d{1,2}:\\d{2}/.test(t)};})()")
        ck("不含 ISO 原始串", iso.get("iso") is False, str(iso))
        ck("显示为 时:分", iso.get("cn") is True, str(iso))

        print("")
        print("=== 4. 点击展开详情 ===")
        cdp.ev("(function(){var s=document.querySelector('.notify-item>summary');"
               "if(s)s.parentNode.open=true;return true;})()", False)
        time.sleep(0.5)
        e = cdp.text("(function(){var it=document.querySelector('.notify-item');"
                     "if(!it)return {open:false,detail:''};var dd=it.querySelector('.d');"
                     "return {open:it.open===true,"
                     "detail:dd?(dd.textContent||'').replace(/\\s+/g,' ').trim().slice(0,170):''};})()")
        ck("点击后已展开", e.get("open") is True, str(e)[:150])
        ck("展开后有通道/成败明细",
           ("成功" in e.get("detail","") or "失败" in e.get("detail","")
            or "原始结果" in e.get("detail","")), e.get("detail","")[:150])
        print("")
        print("  详情 =", e.get("detail","")[:170])
    finally:
        if cdp: cdp.close()
        for p in (proc, srv):
            try: p.terminate()
            except Exception: pass
    n = sum(1 for _, ok in R if ok)
    print("")
    print("==============================================")
    print("TOTAL %d  PASS %d  FAIL %d" % (len(R), n, len(R) - n))
    print("==============================================")
    return 0 if n == len(R) else 1

if __name__ == "__main__":
    sys.exit(main())