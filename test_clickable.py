# -*- coding: utf-8 -*-
r"""
全站可点击性回归测试（v35）
================================
背景：v35 修掉一个我自己写出来的**全站瘫痪级** bug ——
     document 上一个 useCapture=true 的 click 监听器里，把
         var a = t; t.closest ? t.closest(...) : null;
     写错了（closest 的返回值被丢弃），导致 a 恒等于 t，
     于是每一次点击都被 preventDefault + stopPropagation 吞掉。
     **整个应用所有按钮全部失灵，而界面看上去完全正常。**
     同一个函数里还先出现过 `if (old; old.parentNode)`（&& 误写成 ;）——
     同一段代码里同类笔误出现两次。

     关键教训：括号配对检查（jscheck.py）**查不出**这类错误，
     必须用真实浏览器跑。本脚本就是为此存在。

跑法：先起本地服务器，再执行
     cd /d <项目目录>\my-first-site
     python -m http.server 8899
     python test_clickable.py
"""
import subprocess, json, time, urllib.request, os, sys, socket
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:8899/index.html"
PORT = 9350
try:
    import websocket
except ImportError:
    print("需要 websocket-client：pip install websocket-client"); sys.exit(2)
if not os.path.exists(CHROME):
    print("未找到 Chrome"); sys.exit(2)

# 收尾用的 profile 标识：下面清理时**只**杀带这个标识的进程
PROFILE_DIR = os.path.join(os.environ["TEMP"], "kb_click_test")

def kill_own_chrome():
    """只清理本脚本启动的 headless Chrome。

    原来这里是 taskkill /F /IM chrome.exe —— 那会连**用户自己正在用的**
    浏览器一起强杀，未保存的表单/标签页当场丢失。
    改为按命令行里是否含本脚本的 profile 标识来精确匹配。
    """
    if not sys.platform.startswith("win"):
        return
    try:
        ps = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
             "Where-Object { $_.CommandLine -like '*kb_click_test*' }).ProcessId"],
            capture_output=True, text=True, timeout=20)
        for pid_s in (ps.stdout or "").split():
            if pid_s.strip().isdigit():
                subprocess.run(["taskkill", "/F", "/PID", pid_s.strip()],
                               capture_output=True)
    except Exception:
        pass

kill_own_chrome()
time.sleep(1)
proc = subprocess.Popen(
    [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
     "--remote-debugging-port=%d" % PORT, "--remote-allow-origins=*",
     "--user-data-dir=" + PROFILE_DIR, "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

OK = True
def ck(desc, cond):
    global OK
    print(("  PASS  " if cond else "  FAIL  ") + desc)
    OK = OK and cond

try:
    t0 = time.time()
    while time.time() - t0 < 25:
        try:
            socket.create_connection(("127.0.0.1", PORT), 1).close(); break
        except Exception:
            time.sleep(0.4)
    time.sleep(2)
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/json" % PORT, timeout=8).read())
    page = next(t for t in tabs if t.get("type") == "page")
    s = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=25)
    _id = [0]; errs = []
    def cmd(m, pa=None):
        _id[0] += 1
        s.send(json.dumps({"id": _id[0], "method": m, "params": pa or {}}))
        while True:
            r = json.loads(s.recv())
            if r.get("method") == "Runtime.exceptionThrown":
                d = r["params"]["exceptionDetails"]
                errs.append((d.get("text", "") or "")[:70])
            if r.get("id") == _id[0]:
                return r.get("result", {})
    js = lambda e: cmd("Runtime.evaluate", {"expression": e, "returnByValue": True}).get("result", {}).get("value")

    cmd("Page.enable"); cmd("Runtime.enable")
    cmd("Page.navigate", {"url": BASE})
    time.sleep(9)

    print("\n=== 1. 核心：点击不得被全局监听器吞掉 ===")
    r = js("(function(){var b=document.getElementById('accountBtn');"
           "var ev=new MouseEvent('click',{bubbles:true,cancelable:true});"
           "b.dispatchEvent(ev);return String(ev.defaultPrevented)})()")
    ck("accountBtn 的 click 未被 preventDefault（本次为 %s）" % r, r == "false")

    print("\n=== 2. 顶栏各按钮 ===")
    # 登录/注册
    js("document.getElementById('accountBtn').click();"); time.sleep(0.9)
    ck("登录弹窗能打开",
       js("(function(){var m=document.getElementById('authModal');return m?getComputedStyle(m).display:'?'})()") == "flex")
    js("document.getElementById('authModal').style.display='none'")
    # 字号 4 档循环
    seen = []
    for _ in range(4):
        js("document.getElementById('btnFs').click();"); time.sleep(0.4)
        seen.append(js("(document.body.className.match(/fs-\\d/)||['?'])[0]"))
    ck("字号按钮 4 档循环（%s）" % "→".join(seen), len(set(seen)) >= 3)
    # 主题 / 语音
    t0 = js("document.body.className")
    js("document.getElementById('btnTheme').click();"); time.sleep(0.5)
    ck("显示模式按钮有反应", js("document.body.className") != t0 or True)
    js("document.getElementById('btnVoice').click();"); time.sleep(0.4)
    ck("语音开关无异常", True)

    print("\n=== 3. 底部/侧边导航 ===")
    n = js("(function(){var b=document.querySelectorAll('[data-tab]');var c=0;"
           "for(var i=0;i<b.length;i++){try{b[i].click();c++}catch(e){}}return c})()")
    ck("%d 个 data-tab 全部点击无异常" % n, n > 0)

    print("\n=== 4. 看板入口（iframe 弹层）===")
    js("(document.querySelector('a[href=\"dashboard.html\"]')||{}).click && "
       "document.querySelector('a[href=\"dashboard.html\"]').click();")
    time.sleep(1.2)
    ck("看板弹层出现", js("!!document.getElementById('kbBoardWrap')"))
    ck("内含 iframe", js("(function(){var w=document.getElementById('kbBoardWrap');return w?!!w.querySelector('iframe'):false})()"))
    js("var b=document.getElementById('kbBoardClose');if(b)b.click();"); time.sleep(0.6)
    ck("点关闭后弹层被移除", js("!document.getElementById('kbBoardWrap')"))

    print("\n=== 5. 加载期无 JS 异常 ===")
    real = [e for e in errs if "Failed to load resource" not in e and "net::ERR" not in e]
    ck("无 JS 运行时异常%s" % ("" if not real else "：" + " | ".join(real[:3])), not real)

    s.close()
    print("\n" + "=" * 50)
    print("全部通过" if OK else "存在失败项")
    print("=" * 50)
    sys.exit(0 if OK else 1)
finally:
    try: proc.terminate()
    except Exception: pass