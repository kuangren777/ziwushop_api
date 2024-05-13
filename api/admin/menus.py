# -*- coding: utf-8 -*-
# @Time    : 2024/5/13 17:39
# @Author  : KuangRen777
# @File    : menus.py
# @Tags    :
from fastapi import APIRouter, Query, Depends, HTTPException, Path, Body
from typing import Optional, List, Any
from pydantic import BaseModel, HttpUrl, validator, constr, EmailStr, Field, constr, conint
from datetime import datetime
from models import Users, Goods
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.transactions import in_transaction
from tortoise.query_utils import Prefetch

from utils import *

admin_menus = APIRouter()


# Pydantic模型定义
class Menu(BaseModel):
    id: int
    pid: int
    name: str
    level: int
    status: int
    children: Optional[List['Menu']] = []


# 循环引用处理
Menu.update_forward_refs()


# 数据库模型（此处假设为示例，根据实际情况替换）
class Menus:
    # 假设的数据库查询方法
    @staticmethod
    async def get_menus(type: Optional[str] = None):
        # 模拟数据
        sample_data = [
            {"id": 1, "pid": 0, "name": "用户管理", "level": 1, "status": 1, "children": [
                {"id": 3, "pid": 1, "name": "用户列表", "level": 2, "status": 1, "children": []}
            ]},
            {"id": 2, "pid": 0, "name": "商品管理", "level": 1, "status": 1, "children": [
                {"id": 4, "pid": 2, "name": "商品列表", "level": 2, "status": 1, "children": []},
                {"id": 5, "pid": 2, "name": "添加商品", "level": 2, "status": 1, "children": []}
            ]}
        ]
        if type == "all":
            return sample_data
        else:
            return [menu for menu in sample_data if menu["status"] == 1]


@admin_menus.get("", response_model=List[Menu])
async def get_menus_list(
    type: Optional[str] = Query(None, description="Type of menus to fetch"),
    token: str = Depends(oauth2_scheme)
):
    # JWT token验证
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 获取菜单数据
    menus_data = await Menus.get_menus(type)
    return [Menu(**menu) for menu in menus_data]