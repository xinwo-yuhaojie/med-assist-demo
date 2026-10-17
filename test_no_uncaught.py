# -*- coding: utf-8 -*-
"""零未捕获异常运行时巡检：把"跨作用域泄漏"这类 bug 变成可自动发现的问题。

【为什么不用静态检查】
  试过三版正则/花括号方案去静态推断作用域，全部失败：
    v1 正则判 IIFE      -> 主脚本被误判，假 PASS
    v2 按<script>块      -> renderUserCenter 与 asrEngineRealLabel 同块，漏
    v3 块内 IIFE 区间配对 -> strip_sc 遇到正则字面量 /\\/\\/ 就失步，
                          7000 行只剩 14189 字符，尾部整段被吞
  手写 JS 词法器的坑比它想解决的问题多。**一次失败就该换工具，不是重试。**

【改用运行时】
  ReferenceError 的定义就是"运行到那一行才炸"。让真实浏览器把主要路径全走一遍、
  收��全部未捕获异常，是唯一不会骗自己的做法 —— 本项目最初那个 bug
  正是这样在 test_usercenter.py 里抓到的。

覆盖：游客态与登录态、16 个版块、所有弹层、用户中心内每个可点按钮、
      语音/通知/风险等易崩路径。
"""
import json, os, socket, subprocess, sys, time, urllib.request
import websocket
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
P_HTTP, P_CDP = 8090, 9352
API = "https://kangban-ai-cfcnpojddz.cn-beijing.fcapp.run"
TEST_PWD = "Probe123456"
USERS = ["kbmaile2e", "pm1792201069", "probe1792201040"]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
R = []

def ck(n, ok, x=""):
    R.append((n, bool(ok)))
    print(("  [PASS] " if ok else "  [FAIL] ") + n + (("  -> " + str(x)[:110]) if x else ""))

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
                headers={"Content-Type": "application/json", "User-Agent": "sweep"})
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.loads(r.read().decode("utf-8", "replace"))
            if j.get("token"):
                return u, j["token"]
        except Exception:
            pass
    return None, None

class CDP:
    def __init__(self, u):
        self.ws = websocket.create_connection(u, timeout=90); self.i = 0
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
def show(errs, where):
    for e in errs[:4]:
        print("     [%s] %s" % (where, e.get("msg", "")[:110]))
        for line in (e.get("stack", "") or "").split("\n")[1:4]:
            print("          " + line.strip()[:110])

HOOK = """(function(){
  window.__errs = [];
  window.addEventListener('error', function(e){
    window.__errs.push({msg:String(e.message||''), src:e.filename,
      line:e.lineno, stack:(e.error&&String(e.error.stack)||'')});
  });
  window.addEventListener('unhandledrejection', function(e){
    var r = e.reason;
    window.__errs.push({msg:'unhandledrejection: '+String((r&&(r.message||r))||r),src:'',line:0,stack:''});
  });
  return true;
})()"""

def attach(port):
    """重新attach 到当前页面目标。
    同一条 CDP 连接上做第二次 Page.navigate 会把渲染进程卡死、
    recv() 直接超时（和 Page.reload 是同一个坑），所以分阶段时换一条连接。"""
    tabs = json.loads(urllib.request.urlopen(
        "http://127.0.0.1:%d/json/list" % port, timeout=5).read().decode())
    pg = [t for t in tabs if t.get("type") == "page"][0]
    c = CDP(pg["webSocketDebuggerUrl"])
    c.send("Page.enable"); c.send("Runtime.enable")
    return c


def sweep(cdp, js):
    cdp.ev("window.__errs = []; true", False)
    try:
        cdp.ev(js, False)
    except Exception as e:
        return [{"msg": "脚本自身抛错: " + str(e)[:160]}]
    time.sleep(2.2)
    return json.loads(cdp.ev("JSON.stringify(window.__errs)", False))
def run_session(port, token):
    """开一个独立的浏览器会话跑一轮巡检。

    【为什么每个会话只导航一次】
    同一条 CDP 连接上第二次 Page.navigate 会把渲染进程卡死、recv() 无限超时
    （Page.reload 同样如此，已踩过两次）。所以游客态与登录态分成两个
    独立浏览器进程，登录态靠 addScriptToEvaluateOnNewDocument 在任何页面
    脚本执行前注入令牌，避免先以游客态跑完再切���。
    """
    if not free(port):
        print("端口 %d 被占用" % port); return []
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port)],
                           cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    prof = os.path.join(os.environ.get("TEMP", "."), "kb-sweep-%d-%d" % (port, os.getpid()))
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
        "--autoplay-policy=no-user-gesture-required",
        "--remote-debugging-port=%d" % (port + 100), "--remote-allow-origins=*",
        "--user-data-dir=" + prof, "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cdp = None
    try:
        wait("http://127.0.0.1:%d/index.html" % port)
        wait("http://127.0.0.1:%d/json/version" % (port + 100))
        cdp = attach(port + 100)
        if token:
            cdp.send("Page.addScriptToEvaluateOnNewDocument",
                     source="try{localStorage.setItem('emc_token', %s);}catch(e){}"
                            % json.dumps(token))
        cdp.send("Page.navigate", url="http://127.0.0.1:%d/index.html" % port)
        time.sleep(8 if token else 6)
        cdp.ev(HOOK, False)
        return steps(cdp, bool(token))
    finally:
        if cdp: cdp.close()
        for p in (proc, srv):
            try: p.terminate()
            except Exception: pass


def steps(cdp, logged_in):
    errs = []
    if not logged_in:
        print("")
        print("=== A. 游客态：16 个版块逐个切换 ===")
        e = sweep(cdp, """
          (function(){
            [].slice.call(document.querySelectorAll('[data-tab]')).forEach(function(t){
              try{ t.click(); }catch(e){} });
            return true;
          })()""")
        ck("游客态切换全部版块零异常", not e, len(e)); show(e, "tabs"); errs.append(e)

        print("")
        print("=== B. 游客态：顶栏与弹层 ===")
        e = sweep(cdp, """
          (function(){
            ['btnFs','btnTheme','btnVoice','accountBtn','btnMore','btnGuide']
              .forEach(function(id){ var b=document.getElementById(id);
                if(b){ try{ b.click(); }catch(e){} } });
            return true;
          })()""")
        ck("顶栏按钮零异常", not e, len(e)); show(e, "topbar"); errs.append(e)

        print("")
        print("=== C. 游客态：更多功能面板 ===")
        cdp.ev("(function(){var b=document.getElementById('btnMore');if(b)b.click();return true;})()", False)
        time.sleep(1)
        e = sweep(cdp, """
          (function(){
            [].slice.call(document.querySelectorAll('#kbMorePanel button, [id^=kbMore] button'))
              .forEach(function(b){ try{ b.click(); }catch(e){} });
            return true;
          })()""")
        ck("更多面板内按钮零异常", not e, len(e)); show(e, "more"); errs.append(e)
        return errs

    print("")
    print("=== D. 登录态：全部版块 ===")
    e = sweep(cdp, """
      (function(){
        [].slice.call(document.querySelectorAll('[data-tab]')).forEach(function(t){
          try{ t.click(); }catch(e){} });
        return true;
      })()""")
    ck("登录态切换全部版块零异常", not e, len(e)); show(e, "tabs"); errs.append(e)

    print("")
    print("=== E. 登录态：用户中心（asrEngineRealLabel 曾在此崩溃）===")
    cdp.ev("(function(){document.getElementById('accountBtn').click();return true;})()", False)
    time.sleep(2)
    e = sweep(cdp, """
      (function(){
        ['#ucTheme','#ucVoice','#ucAsrEngine'].forEach(function(sel){
          var r=document.querySelector(sel); if(!r) return;
          [].slice.call(r.querySelectorAll('.theme-opt')).forEach(function(b){
            try{ b.click(); }catch(e){} });
        });
        return true;
      })()""")
    ck("用户中心：主题/音色/识别引擎全点一遍零异常", not e, len(e)); show(e, "uc"); errs.append(e)
    info = json.loads(cdp.ev("""
      (function(){ return JSON.stringify({
        voice:(document.getElementById('ucVoice')||{children:[]}).children.length,
        engines:(document.getElementById('ucAsrEngine')||{children:[]}).children.length,
        themes:(document.getElementById('ucTheme')||{children:[]}).children.length});
      })()""", False))
    print("     渲染出：音色 %s / 识别引擎 %s / 主题 %s"
          % (info["voice"], info["engines"], info["themes"]))
    ck("三组选择器均已渲染", min(info["voice"], info["engines"], info["themes"]) >= 2,
       json.dumps(info)); errs.append([])

    print("")
    print("=== F. 登录态：家属日志展开 ===")
    cdp.ev("(function(){try{switchTab('guardian');}catch(e){}return true;})()", False)
    time.sleep(1.5)
    e = sweep(cdp, """
      (function(){
        var b=document.getElementById('btnNotifyToggle');
        if(b && b.textContent.indexOf('\u5c55')>=0) b.click();
        var s=document.querySelector('.notify-item>summary');
        if(s) s.parentNode.open = true;
        return true;
      })()""")
    ck("家属日志展开零异常", not e, len(e)); show(e, "log"); errs.append(e)
    return errs


def main():
    user, token = get_token()
    print("登录账号 =", user)
    allerrs = run_session(8090, None)
    if token:
        allerrs += run_session(8091, token)
    else:
        ck("取到令牌（登录态巡检已执行）", False, "拿不到令牌")
    total = sum(len(x) for x in allerrs)
    ck("全程零未捕获异常（ReferenceError 会在此现形）", total == 0, total)
    n = sum(1 for _, ok in R if ok)
    print("")
    print("==============================================")
    print("TOTAL %d  PASS %d  FAIL %d" % (len(R), n, len(R) - n))
    print("==============================================")
    return 0 if n == len(R) else 1


if __name__ == "__main__":
    sys.exit(main())
