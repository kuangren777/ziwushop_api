# -*- coding: utf-8 -*-
# @Time    : 2024/5/11 19:10
# @Author  : KuangRen777
# @File    : users.py
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

admin_users = APIRouter()

# Pydantic models
User_Pydantic = pydantic_model_creator(Users, name="User")
UserIn_Pydantic = pydantic_model_creator(Users, name="UserIn", exclude_readonly=True)


class PaginationLinks(BaseModel):
    previous: Optional[HttpUrl] = None
    next: Optional[HttpUrl] = None


class PaginationMeta(BaseModel):
    total: int
    count: int
    per_page: int
    current_page: int
    total_pages: int
    links: PaginationLinks


class UsersResponse(BaseModel):
    data: List[User_Pydantic]
    meta: PaginationMeta


# 创建一个Pydantic模型，用于序列化用户数据
UserDetail = pydantic_model_creator(Users, name="UserDetail")


# 基础的用户信息响应模型
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


@admin_users.get("", response_model=UsersResponse)
async def get_users(
        current: Optional[int] = Query(1, alias="page"),
        per_page: int = Query(10, alias="per_page"),
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        token: str = Depends(oauth2_scheme)
):
    # Decode JWT token to authenticate and get user ID
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure the user exists
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user_id = user.id

    query = Users.all()
    if name:
        query = query.filter(name__icontains=name)
    if email:
        query = query.filter(email=email)
    if phone:
        query = query.filter(phone=phone)

    total_count = await query.count()
    total_pages = (total_count + per_page - 1) // per_page
    results = await User_Pydantic.from_queryset(query.offset((current - 1) * per_page).limit(per_page))

    return UsersResponse(
        data=results,
        meta=PaginationMeta(
            total=total_count,
            count=len(results),
            per_page=per_page,
            current_page=current,
            total_pages=total_pages,
            links=PaginationLinks(
                previous=f"http://127.0.0.1:8888/{current - 1}&per_page={per_page}" if current > 1 else None,
                next=f"http://127.0.0.1:8888/api/admin/users?page={current + 1}&per_page={per_page}" if current < total_pages else None
            )
        )
    )


@admin_users.get("/{user_id}", response_model=UserDetailsResponse)
async def get_user_details(
        user_id: int = Path(..., title="The ID of the user to retrieve", ge=1),
        token: str = Depends(oauth2_scheme)):
    # Decode JWT token to authenticate and get user ID
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure the user exists
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user_id = user.id

    # 查询指定ID的用户
    user = await Users.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 使用Pydantic模型转换
    user_detail = await UserDetail.from_tortoise_orm(user)
    # 格式化日期时间字段
    formatted_created_at = user.created_at.strftime('%Y-%m-%d %H:%M:%S')
    formatted_updated_at = user.updated_at.strftime('%Y-%m-%d %H:%M:%S')

    return UserDetailsResponse(
        id=user_detail.id,
        name=user_detail.name,
        email=user_detail.email,
        phone=user_detail.phone,
        avatar=user_detail.avatar,
        avatar_url=f'http://127.0.0.1:8888/upimg/avatar/{user_detail.avatar}' if user_detail.avatar else None,
        is_locked=user_detail.is_locked,
        created_at=formatted_created_at,
        updated_at=formatted_updated_at
    )


@admin_users.patch("/{user_id}/lock", status_code=204)
async def toggle_user_lock(user_id: int = Path(..., title="The ID of the user to toggle lock", ge=1),
                           token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure the user exists
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user_id = user.id

    async with in_transaction() as connection:
        user = await Users.get_or_none(id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Toggle the is_locked status
        user.is_locked = 1 if user.is_locked == 0 else 0
        await user.save()

    return {}


