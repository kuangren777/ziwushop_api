# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 11:07
# @Author  : KuangRen777
# @File    : authority.py
# @Tags    :
from fastapi import APIRouter, Request
from models import Users

api_auth = APIRouter()


@api_auth.post("/auth/register")
async def register(request: Request):
    pt = await request.json()

    name = pt.get("name")
    email = pt.get("email")
    password = pt.get("password")
    password_confirmation = pt.get("password_confirmation")
    if not name or not email or not password or not password_confirmation:
        return {"code": 400, "msg": "参数错误"}
    if password != password_confirmation:
        return {"code": 400, "msg": "两次密码不一致"}
    if await Users.get_or_none(email=email):
        return {"code": 400, "msg": "邮箱已存在"}

    # 加入数据库
    user = await Users.create(name=name, email=email, password=password)
    return {"code": 200, "msg": "注册成功", "data": {"user": user}}
