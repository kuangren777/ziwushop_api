# -*- coding: utf-8 -*-
# @Time    : 2024/5/13 8:34
# @Author  : KuangRen777
# @File    : goods.py
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

admin_goods = APIRouter()


class GoodsBase(BaseModel):
    id: int
    user_id: int
    category_id: int
    title: str
    description: str
    price: int
    stock: int
    sales: int
    cover: str
    cover_url: HttpUrl
    pics: List[str]
    pics_url: List[HttpUrl]
    is_on: int
    is_recommend: int
    details: str
    created_at: str
    updated_at: str


class PaginationLinks(BaseModel):
    previous: Optional[str] = None
    next: Optional[str] = None


class Pagination(BaseModel):
    total: int
    count: int
    per_page: int
    current_page: int
    total_pages: int
    links: PaginationLinks


class Meta(BaseModel):
    pagination: Pagination


class GoodsResponse(BaseModel):
    data: List[GoodsBase]
    meta: Meta


@admin_goods.get("", response_model=GoodsResponse)
async def get_goods_list(
        current: Optional[int] = Query(1, alias="current"),
        title: Optional[str] = None,
        category_id: Optional[int] = None,
        is_on: Optional[int] = None,
        is_recommend: Optional[int] = None,
        include: Optional[str] = None,
        token: str = Depends(oauth2_scheme)
):
    # Decode JWT token to authenticate and get user ID
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    query = Goods.all()
    if title:
        query = query.filter(title__icontains=title)
    if category_id:
        query = query.filter(category_id=category_id)
    if is_on is not None:
        query = query.filter(is_on=is_on)
    if is_recommend is not None:
        query = query.filter(is_recommend=is_recommend)

    # Including additional related data if specified
    if include:
        if "category" in include.split(','):
            query = query.prefetch_related("category")
        if "user" in include.split(','):
            query = query.prefetch_related("user")
        if "comments" in include.split(','):
            query = query.prefetch_related("reviews")

    total_count = await query.count()
    total_pages = (total_count + 10 - 1) // 10  # Assuming per_page is 10
    results = await query.offset((current - 1) * 10).limit(10)

    # Serialize results manually
    goods_data = []
    for goods in results:
        goods_data.append(GoodsBase(
            id=goods.id,
            user_id=goods.user_id,
            category_id=goods.category_id,
            title=goods.title,
            description=goods.description,
            price=goods.price,
            stock=goods.stock,
            sales=goods.sales,
            cover=goods.cover,
            cover_url=f'http://127.0.0.1:8888/upimg/{goods.cover}',
            pics=goods.pics,
            pics_url=[f'http://127.0.0.1:8888/upimg/{pic}' for pic in goods.pics],
            is_on=goods.is_on,
            is_recommend=goods.is_recommend,
            details=goods.details,
            created_at=goods.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            updated_at=goods.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        ))

    return GoodsResponse(
        data=goods_data,
        meta=Meta(
            pagination=Pagination(
                total=total_count,
                count=len(goods_data),
                per_page=10,
                current_page=current,
                total_pages=total_pages,
                links=PaginationLinks(
                    previous=f"http://127.0.0.1:8000/api/admin/goods?page={current - 1}" if current > 1 else None,
                    next=f"http://127.0.0.1:8000/api/admin/goods?page={current + 1}" if current < total_pages else None
                )
            )
        )
    )


class GoodsCreate(BaseModel):
    category_id: int
    title: constr(min_length=1)
    description: Optional[constr(min_length=1)]
    price: conint(gt=0)  # Ensure price is greater than 0
    stock: conint(ge=0)  # Ensure stock is not negative
    cover: Optional[constr(min_length=1)]
    pics: Optional[List[str]] = []
    details: Optional[constr(min_length=1)]


@admin_goods.post("", status_code=201)
async def create_goods(
    goods_data: GoodsCreate,
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
        user_id = user.id

    # Check if the category exists and is valid
    category = await Category.get_or_none(id=goods_data.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="分类不存在")
    if category.status == 0:
        raise HTTPException(status_code=400, detail="分类被禁用")
    if category.level != 2:
        raise HTTPException(status_code=400, detail="只能向2级分类添加商品")

    # Create the new goods
    new_goods = await Goods.create(
        user_id=user_id,
        category_id=goods_data.category_id,
        title=goods_data.title,
        description=goods_data.description if goods_data.description else '暂无',
        price=goods_data.price,
        stock=goods_data.stock,
        cover=goods_data.cover[28:] if goods_data.cover else 'goods_cover/default.png',
        pics=goods_data.pics if goods_data.pics else [],
        details=goods_data.details if goods_data.details else '暂无'
    )

    return {"message": "Goods created successfully", "id": new_goods.id}


class GoodsDetail(BaseModel):
    id: int
    user_id: int
    category_id: int
    title: str
    description: str
    price: int
    stock: int
    sales: int
    cover: str
    cover_url: HttpUrl
    pics: List[str]
    pics_url: List[HttpUrl]
    is_on: int
    is_recommend: int
    details: str
    created_at: str
    updated_at: str
    category: Optional[Any] = None
    user: Optional[Any] = None
    comments: Optional[List[Any]] = None


@admin_goods.get("/{good_id}", response_model=GoodsDetail)
async def get_good_details(
    good_id: int = Path(..., description="The ID of the good to fetch details for"),
    include: Optional[str] = Query(None, description="Comma-separated values to include related data"),
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
        user_id = user.id

    # Start building the query to fetch the good
    query = Goods.get_or_none(id=good_id)

    flag = [0]
    # Including additional related data if specified
    if include:
        if "category" in include.split(','):
            query = query.prefetch_related("category")
            flag.append('category')
        if "user" in include.split(','):
            query = query.prefetch_related("user")
            flag.append('user')
        if "comments" in include.split(','):
            query = query.prefetch_related(Prefetch("reviews", queryset=Comments.all()))
            flag.append('comments')

    good = await query
    if not good:
        raise HTTPException(status_code=404, detail="Good not found")

    category = await good.category
    category_id = category.id if category else None

    # Construct the response
    good_detail = GoodsDetail(
        id=good.id,
        user_id=user_id,
        category_id=category_id,
        title=good.title,
        description=good.description,
        price=good.price,
        stock=good.stock,
        sales=good.sales,
        cover=good.cover,
        cover_url=f'http://127.0.0.1:8888/{good.cover}',
        pics=good.pics,
        pics_url=[f"http://127.0.0.1:8888/{pic}" for pic in good.pics],
        is_on=good.is_on,
        is_recommend=good.is_recommend,
        details=good.details,
        created_at=good.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        updated_at=good.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        category=good.category if "category" in flag else None,
        user=good.user if "user" in flag else None,
        comments=[comment for comment in good.reviews] if "comments" in flag else None
    )

    return good_detail


class GoodsUpdate(BaseModel):
    category_id: int
    title: constr(min_length=1)
    description: constr(min_length=1)
    price: conint(gt=0)  # Ensure price is greater than 0
    stock: conint(ge=0)  # Ensure stock is not negative
    cover: constr(min_length=1)
    pics: List[str] = []
    details: constr(min_length=1)


@admin_goods.put("/{good_id}", status_code=204)
async def update_goods(
    good_id: int = Path(..., description="The ID of the good to update"),
    goods_data: GoodsUpdate = Body(...),
    token: str = Depends(oauth2_scheme)
):
    # Decode JWT token to authenticate and check user permissions
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token")

    # Check if the category exists and is valid
    category = await Category.get_or_none(id=goods_data.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="分类不存在")
    if category.status == 0:
        raise HTTPException(status_code=400, detail="分类被禁用")
    if category.level != 2:
        raise HTTPException(status_code=400, detail="只能向2级分类添加商品")

    # Fetch the good to update
    good = await Goods.get_or_none(id=good_id)
    if not good:
        raise HTTPException(status_code=404, detail="Good not found")

    # Update the good with new data
    good.category_id = goods_data.category_id
    good.title = goods_data.title
    good.description = goods_data.description
    good.price = goods_data.price
    good.stock = goods_data.stock
    if len(goods_data.cover) > 40:
        good.cover = goods_data.cover[28:]
    good.pics = goods_data.pics
    good.details = goods_data.details
    await good.save()

    # No content to return, only status code 204
    return {}


@admin_goods.patch("/{good_id}/on", status_code=204)
async def toggle_goods_on_off(
    good_id: int = Path(..., description="The ID of the good to toggle on/off"),
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
        user_id = user.id

    # Fetch the good to update its on/off status
    good = await Goods.get_or_none(id=good_id)
    if not good:
        raise HTTPException(status_code=404, detail="Good not found")

    # Toggle the is_on status
    good.is_on = 0 if good.is_on else 1
    await good.save()

    # No content to return, only status code 204
    return {}


@admin_goods.patch("/{good_id}/recommend", status_code=204)
async def toggle_goods_recommendation(
    good_id: int = Path(..., description="The ID of the good to toggle recommendation"),
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
        user_id = user.id

    # Fetch the good to update its recommendation status
    good = await Goods.get_or_none(id=good_id)
    if not good:
        raise HTTPException(status_code=404, detail="Good not found")

    # Toggle the is_recommend status
    good.is_recommend = 0 if good.is_recommend else 1
    await good.save()

    # No content to return, only status code 204
    return {}


