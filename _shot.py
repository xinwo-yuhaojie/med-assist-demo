# -*- coding: utf-8 -*-
"""为申报书抓取系统真实界面截图。

用游客态（自带演示数据），比空账号有内容得多，截图才有说服力。
每张都用 CDP 的 Page.captureScreenshot 真实渲染，不是手工拼图。
"""
import base64
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
P_HTTP, P_CDP = 8090, 9400
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = os.path.join(HERE, "_shots")
os.makedirs(OUT, exist_ok=True)

# (文件名, 中文图注, 准备动作JS)
# 注意：一律用 **DOM 点击**，不要调 switchTab()。
# switchTab 定义在主脚本作用域内、并非全局，裸调会抛 ReferenceError，
# 而这里用 try/catch 包着 -> 静默失败 -> 截出来的全是同一张首页。
# （踩过一次：7 张图 MD5 完全相同。）
# 而且下面还有 MD5 去重校验，同类失败会自动暴露。
SHOTS = [
    ("01_home_elder", "老人端首页：今日概览、智能体驾驶舱与一键打卡", "home"),
    ("02_meds", "用药管理：分时段用药计划、库存余量与打卡", "meds"),
    ("03_risk", "AI 风险智能筛查：相互作用与多重用药预警", "risk"),
    ("04_assistant", "智能助手：多轮对话与用药知识问答", "chat"),
    ("05_guardian", "家属端守护：通知日志逐条可展开查看通报明细", "guardian"),
    ("06_bp", "健康监测：血压血糖趋势与异常标注", "bp"),
    ("07_health", "健康档案：用药记录与健康指标汇总", "health"),
    ("08_data", "数据统计：依从率与周期小结", "data"),
    ("09_usercenter", "用户中心：语音播报设置（四种音色可选）", "__account__"),
]


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
        return r.get("result", {}).get("value")

    def shot(self, path, full=False):
        p = {"format": "png"}
        if full:
            p["captureBeyondViewport"] = True
        r = self.send("Page.captureScreenshot", **p)
        data = base64.b64decode(r["data"])
        open(path, "wb").write(data)
        return len(data)

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(P_HTTP)],
                           cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    prof = os.path.join(os.environ.get("TEMP", "."), "kb-shot-%d" % os.getpid())
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                             "--hide-scrollbars", "--force-device-scale-factor=2",
                             "--window-size=430,932",
                             "--remote-debugging-port=%d" % P_CDP, "--remote-allow-origins=*",
                             "--user-data-dir=" + prof, "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cdp = None
    try:
        end = time.time() + 25
        while time.time() < end:
            try:
                urllib.request.urlopen("http://127.0.0.1:%d/index.html" % P_HTTP, timeout=2)
                urllib.request.urlopen("http://127.0.0.1:%d/json/version" % P_CDP, timeout=2)
                break
            except Exception:
                time.sleep(0.4)
        tabs = json.loads(urllib.request.urlopen(
            "http://127.0.0.1:%d/json/list" % P_CDP, timeout=5).read().decode())
        pg = [t for t in tabs if t.get("type") == "page"][0]
        cdp = CDP(pg["webSocketDebuggerUrl"])
        cdp.send("Page.enable")
        cdp.send("Runtime.enable")
        cdp.send("Emulation.setDeviceMetricsOverride", width=430, height=932,
                 deviceScaleFactor=2, mobile=True)
        # 首次使用向导会盖住整屏（"第一步：先把声音打开"），申报书截图不能带它。
        # 必须在**任何页面脚本执行前**写入完成标记 —— 页面加载后再写就来不及，
        # 向导早已弹出。
        cdp.send("Page.addScriptToEvaluateOnNewDocument", source=(
            "try{localStorage.setItem('emc_v26_wizard_done','1');"
            "localStorage.setItem('emc_v26_wizard_seen','9');}catch(e){}"))
        cdp.send("Page.navigate", url="http://127.0.0.1:%d/index.html" % P_HTTP)
        time.sleep(7)

        seen = {}
        for fn, cap, tab in SHOTS:
            try:
                if tab == "__account__":
                    cdp.ev("(function(){var b=document.getElementById('accountBtn');"
                           "if(b)b.click();return true;})()", False)
                else:
                    ok = cdp.ev(
                        "(function(){var b=document.querySelector('[data-tab=\"%s\"]');"
                        "if(!b)return 'no-btn';b.click();return 'clicked';})()" % tab, False)
                    if ok != "clicked":
                        print("  FAIL %-16s 找不到版块按钮 %s (%s)" % (fn, tab, ok))
                        continue
                time.sleep(2.4)
                # 滚回顶部，避免截到滚动中段
                cdp.ev("window.scrollTo(0,0); true", False)
                time.sleep(0.6)
                p = os.path.join(OUT, fn + ".png")
                n = cdp.shot(p)
                h = hashlib.md5(open(p, "rb").read()).hexdigest()[:12]
                if h in seen:
                    print("  !!   %-16s 与 %s 完全相同 —— 切换没生效" % (fn, seen[h]))
                else:
                    seen[h] = fn
                print("  OK   %-16s %6.1f KB  %-12s %s" % (fn, n / 1024.0, h, cap))
            except Exception as e:
                print("  FAIL %-16s %s" % (fn, str(e)[:80]))
    finally:
        if cdp:
            cdp.close()
        for p in (proc, srv):
            try:
                p.terminate()
            except Exception:
                pass
    print("")
    print("输出目录 =", OUT)
    for f in sorted(os.listdir(OUT)):
        print("  ", f)


if __name__ == "__main__":
    main()