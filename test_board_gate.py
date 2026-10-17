#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
看板三道门 · 行为验证（v33）
=================================
不依赖真实后端，直接把 dashboard.html 里的前端逻辑按同样规则复刻一份，
验证四条关键规则：

  1. 门禁密码错误 → 进不去
  2. 门禁密码正确 + board=community + **伪造 managerPw** → 仍必须是社区视图
     （这是 v33 修复的真实漏洞：v25 时 board 只是请求参数，第二道门形同虚设）
  3. 门禁密码正确 + board=manager + managerPw 正确 → 管理者视图
  4. /api/admin/names 只返回**被点的那一个**姓名，且人名密码错误不给

用法：python test_board_gate.py
"""
import sys, io, json, os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 由本文件位置推导，不写死盘符 —— 项目整体移动后仍然有效
BASE = os.path.dirname(os.path.abspath(__file__))

ADMIN_PW = "123456789"
COMMUNITY_PW = "123123123"      # v34：社区治理看板密码（产品指定）
MANAGER_PW = "xinwoyuhaojie"    # v34：管理者看板密码（产品指定）
NAME_PW = COMMUNITY_PW          # v34：揭示人名沿用社区看板密码（同密码，省得再记一个）

# 模拟的用户库：打码姓名 -> 真实姓名
USERS = {
    "zhangguifang": "张桂芳",
    "lixiansheng": "李先生",
    "wangxiaoying": "王晓英",
}


def mask_name(n):
    if not n:
        return ""
    return n[0] + "*" * (len(n) - 1) if len(n) > 1 else n[0] + "*"


def admin_stats(body):
    """复刻 server.js /api/admin/stats 的鉴权规则（v34：两个看板各自硬性验密）"""
    if body.get("password") != ADMIN_PW:
        return 401, {"ok": False, "message": "门禁密码不正确"}
    board = body.get("board") or "community"
    if board == "manager":
        pw = body.get("managerPw")
        if not pw:
            return 403, {"ok": False, "field": "managerPw", "message": "请输入管理者看板密码"}
        if pw != MANAGER_PW:
            return 403, {"ok": False, "field": "managerPw", "message": "管理者看板密码不正确"}
    else:
        pw = body.get("communityPw")
        if not pw:
            return 403, {"ok": False, "field": "communityPw", "message": "请输入社区治理看板密码"}
        if pw != COMMUNITY_PW:
            return 403, {"ok": False, "field": "communityPw", "message": "社区治理看板密码不正确"}
    is_mgr = (board == "manager")
    per_user = []
    for uid, real in USERS.items():
        per_user.append({
            "id": uid,
            "name": real if is_mgr else mask_name(real),
            "gender": "女",
        })
    return 200, {
        "ok": True,
        "board": board,
        "namesMasked": not is_mgr,
        "mgrOk": is_mgr,
        "stats": {"perUser": per_user},
    }


def admin_names(body):
    """复刻 server.js /api/admin/names 的鉴权规则"""
    if body.get("password") != ADMIN_PW:
        return 401, {"ok": False, "message": "门禁密码不正确"}
    uid = body.get("id")
    if uid not in USERS:
        return 404, {"ok": False, "message": "未找到该居民信息"}
    if body.get("namePw") != NAME_PW:
        return 403, {"ok": False, "message": "人名密码不正确"}
    # 只返回被点的那一个
    return 200, {"ok": True, "id": uid, "name": USERS[uid]}


def check(desc, cond):
    print(("  ✅ " if cond else "  ❌ ") + desc)
    return cond


def main():
    ok = True
    print("\n=== 1. 门禁密码 ===")
    st, j = admin_stats({"password": "wrong"})
    ok &= check("错误门禁密码被拒（401）", st == 401)

    print("\n=== 2. 只过门禁、不给看板密码 → 拿不到任何数据 ===")
    ok &= check("缺 communityPw → 403", admin_stats({"password": ADMIN_PW, "board": "community"})[0] == 403)
    ok &= check("缺 managerPw   → 403", admin_stats({"password": ADMIN_PW, "board": "manager"})[0] == 403)
    ok &= check("完全不带看板字段 → 403", admin_stats({"password": ADMIN_PW})[0] == 403)

    print("\n=== 3. 社区治理看板（密码 %s）===" % COMMUNITY_PW)
    st, j = admin_stats({"password": ADMIN_PW, "board": "community",
                         "communityPw": COMMUNITY_PW})
    ok &= check("进入成功 200", st == 200)
    ok &= check("board = community", j.get("board") == "community")
    ok &= check("namesMasked = True", j.get("namesMasked") is True)
    ok &= check("mgrOk = False", j.get("mgrOk") is False)
    masked = [u["name"] for u in j["stats"]["perUser"]]
    ok &= check("人名已打码：" + "、".join(masked),
                all("*" in n for n in masked))
    ok &= check("社区密码给错 → 403",
                admin_stats({"password": ADMIN_PW, "board": "community",
                             "communityPw": "000000"})[0] == 403)

    print("\n=== 4. 管理者看板（密码 %s）===" % MANAGER_PW)
    st, j = admin_stats({"password": ADMIN_PW, "board": "manager", "managerPw": MANAGER_PW})
    ok &= check("进入成功 200", st == 200)
    ok &= check("board = manager", j.get("board") == "manager")
    ok &= check("namesMasked = False", j.get("namesMasked") is False)
    ok &= check("mgrOk = True", j.get("mgrOk") is True)
    real = [u["name"] for u in j["stats"]["perUser"]]
    ok &= check("人名实名：" + "、".join(real),
                all("*" not in n for n in real))
    ok &= check("管理者密码给错 → 403",
                admin_stats({"password": ADMIN_PW, "board": "manager",
                             "managerPw": "nope"})[0] == 403)

    print("\n=== 4b. 两道门不可互换（v25 遗留漏洞的回归防护）===")
    ok &= check("用社区密码进管理者看板 → 403",
                admin_stats({"password": ADMIN_PW, "board": "manager",
                             "managerPw": COMMUNITY_PW})[0] == 403)
    ok &= check("用管理者密码进社区看板 → 403",
                admin_stats({"password": ADMIN_PW, "board": "community",
                             "communityPw": MANAGER_PW})[0] == 403)
    ok &= check("用门禁密码进管理者看板 → 403",
                admin_stats({"password": ADMIN_PW, "board": "manager",
                             "managerPw": ADMIN_PW})[0] == 403)
    ok &= check("伪造 board=manager 但空密码 → 403",
                admin_stats({"password": ADMIN_PW, "board": "manager",
                             "managerPw": ""})[0] == 403)

    print("\n=== 5. 点人名揭示（社区视图）===")
    st, j = admin_names({"password": ADMIN_PW, "id": "lixiansheng", "namePw": "000"})
    ok &= check("人名密码错误被拒（403）", st == 403)
    ok &= check("错误响应里不含真实姓名", "李先生" not in json.dumps(j, ensure_ascii=False))

    st, j = admin_names({"password": ADMIN_PW, "id": "lixiansheng", "namePw": NAME_PW})
    ok &= check("密码正确返回 200", st == 200)
    ok &= check("只返回被点的那一个姓名", j.get("name") == "李先生" and "id" in j)
    ok &= check("不含其他人的姓名",
                all(v not in json.dumps(j, ensure_ascii=False)
                    for k, v in USERS.items() if k != "lixiansheng"))

    st, j = admin_names({"password": "bad", "id": "lixiansheng", "namePw": NAME_PW})
    ok &= check("门禁密码错时即使人名密码对也拿不到（401）", st == 401)

    st, j = admin_names({"password": ADMIN_PW, "id": "nosuch", "namePw": NAME_PW})
    ok &= check("不存在的账号返回 404", st == 404)

    print("\n=== 6. 前端：切换看板必须重输密码 ===")
    try:
        src = open(os.path.join(BASE, "dashboard.html"), encoding="utf-8").read()
        ok &= check("切看板时清空 boardPw", "S.boardPw = ''; save();" in src)
        ok &= check("无旧的 S.mgrPw 残留", "S.mgrPw" not in src)
        ok &= check("无已废弃的 j.mgrDenied 判断", "j.mgrDenied" not in src)
        ok &= check("无已移除的 mgrTip 元素引用", "mgrTip" not in src)
    except Exception as e:
        ok &= check("读取 dashboard.html 失败：%s" % e, False)

    print("\n=== 7. SOS：不再展示未经验证的医院信息 ===")
    try:
        idx = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()
        ok &= check("'附近医院（示意）'已移除", "附近医院（示意）" not in idx)
        ok &= check("演示假医院名（示范）已移除", "（示范）" not in idx)
        ok &= check("NEARBY_HOSPITALS 已置空", "EMC.NEARBY_HOSPITALS = [];" in idx)
        ok &= check("SOS 仍保留 120 与呼叫家属",
                    "sos-120" in idx and "sos-call" in idx)
    except Exception as e:
        ok &= check("读取 index.html 失败：%s" % e, False)

    print("\n" + "=" * 52)
    print("全部通过 ✅" if ok else "存在失败项 ❌")
    print("=" * 52)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())