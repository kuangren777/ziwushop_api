# -*- coding: utf-8 -*-
# @Time    : 2024/5/11 23:39
# @Author  : KuangRen777
# @File    : user.py
# @Tags    :
from fastapi import APIRouter, Query, Depends, HTTPException, Path
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, validator
from datetime import datetime
from models import Users
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.transactions import in_transaction

from utils import *

admin_user = APIRouter()

# 创建Pydantic模型用于用户详细信息的序列化
UserDetail = pydantic_model_creator(Users, name="UserDetail")


class UserDetailsResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    avatar: Optional[str]
    avatar_url: Optional[HttpUrl]
    is_locked: int
    created_at: str  # 使用字符串来自定义格式
    updated_at: str  # 使用字符串来自定义格式


@admin_user.get("", response_model=UserDetailsResponse)
async def get_current_user_info(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 确保用户存在
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 格式化日期时间字段
    formatted_created_at = user.created_at.strftime('%Y-%m-%d %H:%M:%S')
    formatted_updated_at = user.updated_at.strftime('%Y-%m-%d %H:%M:%S')

    return UserDetailsResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        avatar_url=f'http://127.0.0.1:8888/upimg/avatar/{user.avatar}' if user.avatar else
        'http://127.0.0.1:8888/upimg/avatar/default_avatars.jpg',
        is_locked=user.is_locked,
        created_at=formatted_created_at,
        updated_at=formatted_updated_at
    )