# -*- coding: utf-8 -*-
# @Time    : 2024/5/13 10:58
# @Author  : KuangRen777
# @File    : comments.py
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

admin_comments = APIRouter()


class UserBase(BaseModel):
    id: int
    name: str
    email: str


class GoodsBase(BaseModel):
    id: int
    title: str
    description: str
    price: int


class CommentBase(BaseModel):
    id: int
    user_id: int
    goods_id: int
    content: str
    rate: int
    star: int
    pics: Optional[List[str]]
    pics_url: Optional[List[str]]
    reply: Optional[str]
    created_at: str
    updated_at: str
    user: Optional[UserBase] = None
    goods: Optional[GoodsBase] = None


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


class CommentsResponse(BaseModel):
    data: List[CommentBase]
    meta: Meta


@admin_comments.get("", response_model=CommentsResponse)
async def get_comments_list(
        current: Optional[int] = Query(1, alias="current", description="Current page number"),
        goods_title: Optional[str] = Query(None, description="Filter by goods title"),
        rate: Optional[int] = Query(None, description="Filter by comment rate"),
        include: Optional[str] = Query(None, description="Fields to include like goods and user"),
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

    # Base query setup
    query = Comments.all()
    if goods_title:
        query = query.filter(goods__title__icontains=goods_title)
    if rate:
        query = query.filter(rate=rate)

    # Including additional related data if specified
    prefetch_relations = []
    if "goods" in include.split(','):
        prefetch_relations.append(Prefetch("goods", queryset=Goods.all()))
    if "user" in include.split(','):
        prefetch_relations.append(Prefetch("user", queryset=Users.all()))
    if prefetch_relations:
        query = query.prefetch_related(*prefetch_relations)

    # Pagination setup
    per_page = 10  # Define your default per_page value
    total_count = await query.count()
    total_pages = (total_count + per_page - 1) // per_page
    comments = await query.offset((current - 1) * per_page).limit(per_page)

    # Convert comments to CommentBase model
    comments_data = [
        CommentBase(
            id=comment.id,
            user_id=comment.user.id if comment.user else None,
            goods_id=comment.goods.id if comment.goods else None,
            content=comment.content,
            rate=comment.rate,
            star=comment.star,
            pics=comment.pics,
            pics_url=[f"http://127.0.0.1:8888/upimg/goods_cover/{pic}" for pic in
                      comment.pics] if comment.pics else None,
            reply=comment.reply,
            created_at=comment.created_at.isoformat(),
            updated_at=comment.updated_at.isoformat(),
            user=UserBase(**comment.user.__dict__) if comment.user else None,
            goods=GoodsBase(**comment.goods.__dict__) if comment.goods else None
        ) for comment in comments
    ]

    return CommentsResponse(
        data=comments_data,
        meta=Meta(
            pagination=Pagination(
                total=total_count,
                count=len(comments_data),
                per_page=per_page,
                current_page=current,
                total_pages=total_pages,
                links=PaginationLinks(
                    previous=f"http://127.0.0.1:8888/api/admin/comments?page={current - 1}" if current > 1 else None,
                    next=f"http://127.0.0.1:8888/api/admin/comments?page={current + 1}" if current < total_pages else None
                )
            )
        )
    )


class UserDetail(BaseModel):
    id: int
    name: str
    email: str


class GoodsDetail(BaseModel):
    id: int
    title: str
    description: str
    price: int


class CommentDetail(BaseModel):
    id: int
    user_id: int
    goods_id: int
    content: str
    rate: int
    star: int
    pics: Optional[List[str]]
    pics_url: Optional[List[str]]
    reply: Optional[str]
    created_at: str
    updated_at: str
    user: Optional[UserDetail] = None
    goods: Optional[GoodsDetail] = None


@admin_comments.get("/{comment_id}", response_model=CommentDetail)
async def get_comment_detail(
        comment_id: int = Path(..., description="The ID of the comment to retrieve"),
        include: Optional[str] = Query(None, description="Fields to include like goods and user"),
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

    # Base query setup with potential prefetches based on 'include'
    prefetch_relations = []
    if include:
        if "goods" in include.split(','):
            prefetch_relations.append(Prefetch("goods", queryset=Goods.all()))
        if "user" in include.split(','):
            prefetch_relations.append(Prefetch("user", queryset=Users.all()))
    comment = await Comments.get_or_none(id=comment_id).prefetch_related(*prefetch_relations)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Construct the detailed response
    comment_detail = CommentDetail(
        id=comment.id,
        user_id=comment.user.id if comment.user else None,
        goods_id=comment.goods.id if comment.goods else None,
        content=comment.content,
        rate=comment.rate,
        star=comment.star,
        pics=comment.pics,
        pics_url=[f"http://127.0.0.1:8888/upimg/comment_pics/{pic}" for pic in comment.pics] if comment.pics else None,
        reply=comment.reply,
        created_at=comment.created_at.isoformat(),
        updated_at=comment.updated_at.isoformat(),
        user=UserDetail(**comment.user.__dict__) if "user" in include.split(',') and comment.user else None,
        goods=GoodsDetail(**comment.goods.__dict__) if "goods" in include.split(',') and comment.goods else None
    )

    return comment_detail


class ReplyRequest(BaseModel):
    reply: str


@admin_comments.patch("/{comment_id}/reply", status_code=200)
async def reply_to_comment(
        reply: str,
        comment_id: int = Path(..., description="The ID of the comment to reply to"),
        # body: ReplyRequest = Body(...),
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

    # Retrieve the comment to be replied to
    comment = await Comments.get_or_none(id=comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Update the reply field
    comment.reply = reply
    await comment.save()

    # Return a success message
    return {"message": "Reply added successfully to the comment"}


@admin_comments.delete("/{comment_id}/delete", status_code=204)
async def delete_comment(
    comment_id: int = Path(..., description="The ID of the comment to be deleted"),
    token: str = Depends(oauth2_scheme)
):
    # Decode JWT token to authenticate and check user permissions
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token")

    # Retrieve the comment to ensure it exists
    comment = await Comments.get_or_none(id=comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Delete the comment
    await comment.delete()

    # No content to return, only status code 204
    return {}
