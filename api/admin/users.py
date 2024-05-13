# -*- coding: utf-8 -*-
# @Time    : 2024/5/11 19:10
# @Author  : KuangRen777
# @File    : users.py
# @Tags    :
from fastapi import APIRouter, Query, Depends, HTTPException, Path, Body
from typing import Optional, List, Any
from pydantic import BaseModel, HttpUrl, validator, constr, EmailStr
from datetime import datetime
from models import Users
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.transactions import in_transaction

from utils import *

admin_users = APIRouter()

# Pydantic models
# 定义Pydantic模型，从Users模型中创建，排除不需要返回的字段
User_Pydantic = pydantic_model_creator(Users, name="User", exclude=("password", "password_verified", "remember_token"))
UserIn_Pydantic = pydantic_model_creator(Users, name="UserIn", exclude_readonly=True)


# Manually define the Pydantic model to ensure all fields are included correctly
class UserPublic(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str]
    avatar: Optional[str]
    is_locked: int
    created_at: datetime
    updated_at: datetime


class PaginationLinks(BaseModel):
    previous: Optional[HttpUrl] = None
    next: Optional[HttpUrl] = None


class Pagination(BaseModel):
    total: int
    count: int
    per_page: int
    current_page: int
    total_pages: int
    links: PaginationLinks


class Meta(BaseModel):
    pagination: Pagination


class UsersResponse(BaseModel):
    data: list[Any] = []
    meta: Meta


class UserUpdate(BaseModel):
    name: constr(min_length=1)
    email: EmailStr


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


# 创建一个用于接收用户数据的Pydantic模型
class UserCreate(BaseModel):
    name: constr(min_length=1)
    email: EmailStr
    password: constr(min_length=6)


@admin_users.get("", response_model=UsersResponse)
async def get_users(
        current: int = Query(1, alias="current"),
        per_page: int = Query(10, alias="per_page"),
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        token: str = Depends(oauth2_scheme)
):
    # 验证 JWT token 以认证并获取用户信息
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 确保用户存在
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 构建查询并应用过滤
    query = Users.all()
    if name:
        query = query.filter(name__icontains=name)
    if email:
        query = query.filter(email__icontains=email)
    if phone:
        query = query.filter(phone=phone)

    query = query.order_by("-created_at")

    # 计算总数和总页数
    total_count = await query.count()
    total_pages = (total_count + per_page - 1) // per_page

    # 应用分页并获取数据
    users = await query.offset((current - 1) * per_page).limit(per_page)

    # 格式化用户数据
    formatted_users = []
    for user in users:
        avatar_url = user.avatar if user.avatar else "http://127.0.0.1:8888/upimg/avatars/default_avatars.jpg"
        avatar = avatar_url
        formatted_users.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "avatar": avatar,
            "avatar_url": avatar_url,
            "is_locked": user.is_locked,
            "created_at": user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "updated_at": user.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    print(formatted_users)

    return UsersResponse(
        data=formatted_users,
        meta=Meta(
            pagination=Pagination(
                total=total_count,
                count=len(formatted_users),
                per_page=per_page,
                current_page=current,
                total_pages=total_pages,
                links=PaginationLinks(
                    previous=f"http://127.0.0.1:8888/api/admin/users?page={current - 1}&per_page={per_page}" if current > 1 else None,
                    next=f"http://127.0.0.1:8888/api/admin/users?page={current + 1}&per_page={per_page}" if current < total_pages else None
                )
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
        avatar_url=f'http://127.0.0.1:8888/upimg/avatar/{user_detail.avatar}' if user_detail.avatar else
        'http://127.0.0.1:8888/upimg/avatars/default_avatars.jpg',
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
        admin_id = user.id

    user = await Users.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Toggle the is_locked status
    user.is_locked = 1 if user.is_locked == 0 else 0
    await user.save()

    return {}


@admin_users.get("/user", response_model=UserDetailsResponse)
async def get_current_user_info(token: str = Depends(oauth2_scheme)):
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
        admin_id = user.id

    # 格式化日期时间字段
    formatted_created_at = user.created_at.strftime('%Y-%m-%d %H:%M:%S')
    formatted_updated_at = user.updated_at.strftime('%Y-%m-%d %H:%M:%S')

    return UserDetailsResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        avatar_url=f'http://127.0.0.1:8888/upimg/avatar/{user.avatar}' if user.avatar else None,
        is_locked=user.is_locked,
        created_at=formatted_created_at,
        updated_at=formatted_updated_at
    )


@admin_users.post("", status_code=201)
async def create_user(
        user_data: UserCreate,
        token: str = Depends(oauth2_scheme)
):
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
        admin_id = user.id

    # 检查邮箱是否已被使用
    existing_user = await Users.get_or_none(email=user_data.email)
    if existing_user:
        raise HTTPException(status_code=422, detail="Email is already in use")

    # 创建新用户
    hashed_password = pwd_context.hash(user_data.password)  # 假设hash_password是有效的密码哈希函数
    new_user = await Users.create(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password
    )

    return {"message": "User created successfully", "user_id": new_user.id}


@admin_users.put("/{user_id}", status_code=201)
async def update_user(
        user_id: int = Path(..., title="The ID of the user to update", ge=1),
        user_data: UserUpdate = Body(...),
        token: str = Depends(oauth2_scheme)
):
    # 验证JWT token和用户权限（RBAC）
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if not user_email:  # 示例中简化权限验证，实际应检查更多信息
            raise HTTPException(status_code=403, detail="Permission denied")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 检查要更新的用户是否存在
    user = await Users.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 检查邮箱是否已被使用，但排除当前用户
    existing_user = await Users.get_or_none(email=user_data.email)
    if existing_user and existing_user.id != user_id:
        raise HTTPException(status_code=422, detail="Email is already in use")

    # 更新用户信息
    user.name = user_data.name
    user.email = user_data.email
    await user.save()

    return {"message": "User updated successfully", "user_id": user.id}
