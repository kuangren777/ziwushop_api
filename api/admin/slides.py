# -*- coding: utf-8 -*-
# @Time    : 2024/5/13 17:46
# @Author  : KuangRen777
# @File    : slides.py
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
from tortoise.exceptions import DoesNotExist

from utils import *

admin_slides = APIRouter()


# 分页链接的数据模型
class PaginationLinks(BaseModel):
    previous: Optional[str] = None
    next: Optional[str] = None


# 分页元数据的数据模型
class Pagination(BaseModel):
    total: int
    count: int
    per_page: int
    current_page: int
    total_pages: int
    links: PaginationLinks


# 元数据的数据模型
class Meta(BaseModel):
    pagination: Pagination


# 轮播图的数据模型
class SlideBase(BaseModel):
    id: int
    title: str
    url: str
    img: str
    img_url: str
    seq: int
    status: int
    created_at: str
    updated_at: str


# 轮播图响应的数据模型
class SlidesResponse(BaseModel):
    data: List[SlideBase]
    meta: Meta


# 获取轮播图列表
@admin_slides.get("", response_model=SlidesResponse)
async def get_slides_list(
        current: Optional[int] = Query(1, alias="current", description="Current page number"),
        token: str = Depends(oauth2_scheme)
):
    # 验证JWT token以认证用户信息
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 确保用户存在
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 设置每页显示条数
    per_page = 10
    # 计算总数据量
    total_count = await Slides.all().count()
    # 计算总页数
    total_pages = (total_count + per_page - 1) // per_page
    # 查询当前页的数据
    slides = await Slides.all().offset((current - 1) * per_page).limit(per_page)

    # 转换数据模型
    slides_data = [SlideBase(
        id=slide.id,
        title=slide.title,
        url=slide.url,
        img=slide.img,
        img_url=f"http://127.0.0.1:8888/upimg/{slide.img}",
        seq=slide.seq,
        status=slide.status,
        created_at=slide.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        updated_at=slide.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    ) for slide in slides]

    # 构建分页链接
    pagination_links = PaginationLinks(
        previous=f"http://127.0.0.1:8888/api/admin/slides?current={current - 1}" if current > 1 else None,
        next=f"http://127.0.0.1:8888/api/admin/slides?current={current + 1}" if current < total_pages else None
    )

    # 构建响应数据
    return SlidesResponse(
        data=slides_data,
        meta=Meta(
            pagination=Pagination(
                total=total_count,
                count=len(slides_data),
                per_page=per_page,
                current_page=current,
                total_pages=total_pages,
                links=pagination_links
            )
        )
    )


# 轮播图的数据模型
class SlideDetail(BaseModel):
    id: int
    title: str
    url: str
    img: str
    img_url: str
    seq: int
    status: int
    created_at: str
    updated_at: str


# 获取单个轮播图的详细信息
@admin_slides.get("/{slide_id}", response_model=SlideDetail)
async def get_slide_detail(
        slide_id: int = Path(..., description="The ID of the slide to retrieve"),
        token: str = Depends(oauth2_scheme)
):
    # 验证JWT token以认证用户信息
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 确保用户存在
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 根据ID查询轮播图
    slide = await Slides.get_or_none(id=slide_id)
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    # 构建并返回轮播图详细信息
    return SlideDetail(
        id=slide.id,
        title=slide.title,
        url=slide.url,
        img=slide.img,
        img_url=f"http://127.0.0.1:8888/upimg/{slide.img}",
        seq=slide.seq,
        status=slide.status,
        created_at=slide.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        updated_at=slide.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    )


# 请求体的数据模型
class SlideCreate(BaseModel):
    title: str
    img: str
    url: Optional[str] = None
    status: Optional[int] = 1


# 响应体的数据模型
class SlideResponse(BaseModel):
    id: int
    title: str
    img: str
    img_url: str
    url: Optional[str]
    status: int
    created_at: str
    updated_at: str


# 添加轮播图
@admin_slides.post("", response_model=SlideResponse, status_code=201)
async def create_slide(
        slide_data: SlideCreate,
        token: str = Depends(oauth2_scheme)
):
    # 验证JWT token以认证用户信息
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 确保用户存在
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 创建新的轮播图
    new_slide = await Slides.create(
        title=slide_data.title,
        img=slide_data.img[28:],
        url=slide_data.url,
        status=slide_data.status
    )

    # 构建响应数据
    return SlideResponse(
        id=new_slide.id,
        title=new_slide.title,
        img=new_slide.img,
        img_url=f"http://127.0.0.1:8888/upimg/default/{new_slide.img}",
        url=new_slide.url,
        status=new_slide.status,
        created_at=new_slide.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        updated_at=new_slide.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    )


# 请求体的数据模型
class SlideUpdate(BaseModel):
    title: str
    img: str
    url: Optional[HttpUrl] = None
    status: Optional[int] = 1


# 修改轮播图
@admin_slides.put("/{slide_id}", status_code=204)
async def update_slide(
        slide_id: int = Path(..., description="The ID of the slide to update"),
        slide_data: SlideUpdate = Body(...),
        token: str = Depends(oauth2_scheme)
):
    # 验证JWT token以认证用户信息
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 确保用户存在
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 查找并更新指定的轮播图
    slide = await Slides.get_or_none(id=slide_id)
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    slide.title = slide_data.title
    print(slide_data.img)
    if slide_data.img != slide.img:
        slide.img = slide_data.img[28:]
    slide.url = slide_data.url
    slide.status = slide_data.status
    await slide.save()

    return {}


@admin_slides.delete("/{slide_id}", status_code=204)
async def delete_slide(
        slide_id: int = Path(..., description="The ID of the slide to delete"),
        token: str = Depends(oauth2_scheme)
):
    # 验证JWT token以认证用户信息
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 确保用户存在
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 查找并删除指定的轮播图
    slide = await Slides.get_or_none(id=slide_id)
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    await slide.delete()

    return {}


# 更新轮播图排序
@admin_slides.patch("/{slide_id}/seq", status_code=204)
async def update_slide_sequence(
        slide_id: int = Path(..., description="The ID of the slide to update"),
        seq: int = Body(1, description="New sequence number for the slide"),
        token: str = Depends(oauth2_scheme)
):
    # 验证JWT token以认证用户信息
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 确保用户存在
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 查找并更新指定的轮播图
    slide = await Slides.get_or_none(id=slide_id)
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    slide.seq = seq
    await slide.save()

    return {}


@admin_slides.patch("/{slide_id}/status", status_code=204)
async def toggle_slide_status(
        slide_id: int = Path(..., description="The ID of the slide to toggle status"),
        token: str = Depends(oauth2_scheme)
):
    # 验证JWT token以认证用户信息
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 确保用户存在
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 查找并更新指定的轮播图状态
    slide = await Slides.get_or_none(id=slide_id)
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")

    slide.status = 0 if slide.status == 1 else 1
    await slide.save()

    return {}



