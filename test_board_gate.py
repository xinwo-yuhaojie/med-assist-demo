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
import sys, io, json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ADMIN_PW = "123456789"
MANAGER_PW = "xinwoyuhaojie"
NAME_PW = "123123123"

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
    """复刻 server.js /api/admin/stats 的鉴权规则"""
    if body.get("password") != ADMIN_PW:
        return 401, {"ok": False, "message": "密码不正确"}
    want_mgr = body.get("board") == "manager"
    is_mgr = False
    mgr_denied = False
    if want_mgr:
        if body.get("managerPw") and body["managerPw"] == MANAGER_PW:
            is_mgr = True
        else:
            mgr_denied = True
    per_user = []
    for uid, real in USERS.items():
        per_user.append({
            "id": uid,
            "name": real if is_mgr else mask_name(real),
            "gender": "女",
        })
    return 200, {
        "ok": True,
        "board": "manager" if is_mgr else "community",
        "namesMasked": not is_mgr,
        "mgrOk": is_mgr,
        "mgrDenied": mgr_denied,
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

    print("\n=== 2. 社区视图（正常路径）===")
    st, j = admin_stats({"password": ADMIN_PW, "board": "community"})
    ok &= check("门禁通过返回 200", st == 200)
    ok &= check("board = community", j.get("board") == "community")
    ok &= check("namesMasked = True", j.get("namesMasked") is True)
    ok &= check("mgrOk = False", j.get("mgrOk") is False)
    masked = [u["name"] for u in j["stats"]["perUser"]]
    ok &= check("人名已打码：" + "、".join(masked),
                all("*" in n for n in masked))

    print("\n=== 3. 伪造 board=manager 但看板密码错（v33 修复的关键漏洞）===")
    st, j = admin_stats({"password": ADMIN_PW, "board": "manager", "managerPw": "guess"})
    ok &= check("仍降级为 community", j.get("board") == "community")
    ok &= check("mgrOk = False", j.get("mgrOk") is False)
    ok &= check("mgrDenied = True（前端可提示密码错误）", j.get("mgrDenied") is True)
    ok &= check("人名仍是打码的",
                all("*" in u["name"] for u in j["stats"]["perUser"]))

    print("\n=== 3b. 完全不传 managerPw ===")
    st, j = admin_stats({"password": ADMIN_PW, "board": "manager"})
    ok &= check("缺失密码同样降级为 community", j.get("board") == "community")
    ok &= check("人名仍是打码的",
                all("*" in u["name"] for u in j["stats"]["perUser"]))

    print("\n=== 4. 管理者看板（两道密码都对）===")
    st, j = admin_stats({"password": ADMIN_PW, "board": "manager", "managerPw": MANAGER_PW})
    ok &= check("board = manager", j.get("board") == "manager")
    ok &= check("namesMasked = False", j.get("namesMasked") is False)
    ok &= check("mgrOk = True", j.get("mgrOk") is True)
    real = [u["name"] for u in j["stats"]["perUser"]]
    ok &= check("人名实名：" + "、".join(real),
                all("*" not in n for n in real))

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

    print("\n" + "=" * 52)
    print("全部通过 ✅" if ok else "存在失败项 ❌")
    print("=" * 52)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())