# -*- coding: utf-8 -*-
# @Time    : 2024/5/13 14:24
# @Author  : KuangRen777
# @File    : orders.py
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

admin_orders = APIRouter()


class UserBase(BaseModel):
    id: int
    name: str
    email: str


class GoodsBase(BaseModel):
    id: int
    title: str
    description: str
    price: int


class OrderDetailsBase(BaseModel):
    id: int
    goods_id: int
    price: int
    num: int


class OrderBase(BaseModel):
    id: int
    order_no: str
    user_id: int
    amount: int
    status: int
    address_id: int
    express_type: Optional[str]
    express_no: Optional[str]
    pay_time: Optional[str]
    pay_type: Optional[str]
    trade_no: Optional[str]
    created_at: str
    updated_at: str
    user: Optional[UserBase] = None
    goods: List[GoodsBase] = []
    orderDetails: List[OrderDetailsBase] = []


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


class OrdersResponse(BaseModel):
    data: List[OrderBase]
    meta: Meta


@admin_orders.get("", response_model=OrdersResponse)
async def get_orders_list(
        current: Optional[int] = Query(1, alias="current", description="Current page number"),
        order_no: Optional[str] = Query(None, description="Filter by order number"),
        trade_no: Optional[str] = Query(None, description="Filter by trade number"),
        status: Optional[int] = Query(None, description="Filter by order status"),
        include: Optional[str] = Query(None, description="Fields to include like goods, user, orderDetails"),
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

    # 构建基础查询与筛选
    query = Orders.all()
    if order_no:
        query = query.filter(order_no__icontains=order_no)
    if trade_no:
        query = query.filter(trade_no__icontains=trade_no)
    if status is not None:
        query = query.filter(status=status)

    # 包含额外数据的预加载
    prefetch_relations = []
    if "user" in include.split(','):
        prefetch_relations.append("user")

    if prefetch_relations:
        query = query.prefetch_related(*prefetch_relations)

    query = query.order_by("-updated_at")

    # 分页设置
    per_page = 10
    total_count = await query.count()
    total_pages = (total_count + per_page - 1) // per_page
    orders = await query.offset((current - 1) * per_page).limit(per_page)

    orders_data = []
    for order in orders:
        order_address = await order.address.first()
        order_details = []
        if "orderDetails" in include.split(','):
            # 获取订单详情信息，包括相关的商品信息（如果需要）
            order_details = await OrderDetails.filter(order_id=order.id).prefetch_related('goods')

        # 构建订单基本信息
        order_data = OrderBase(
            id=order.id,
            order_no=order.order_no,
            user_id=order.user.id if order.user else None,
            amount=order.amount,
            status=order.status,
            address_id=order_address.id if order.address else None,
            express_type=order.express_type,
            express_no=order.express_no,
            pay_time=order.pay_time.strftime('%Y-%m-%d %H:%M:%S') if order.pay_time else None,
            pay_type=order.pay_type,
            trade_no=order.trade_no,
            created_at=order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            updated_at=order.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            user=UserBase(**order.user.__dict__) if "user" in include.split(',') and order.user else None,
            goods=[GoodsBase(**detail.goods.__dict__) for detail in order_details] if "orderDetails" in include.split(
                ',') else [],
            orderDetails=[OrderDetailsBase(**detail.__dict__) for detail in
                          order_details] if "orderDetails" in include.split(',') else []
        )
        orders_data.append(order_data)

    # 返回响应
    return OrdersResponse(
        data=orders_data,
        meta=Meta(
            pagination=Pagination(
                total=total_count,
                count=len(orders_data),
                per_page=per_page,
                current_page=current,
                total_pages=total_pages,
                links=PaginationLinks(
                    previous=f"http://127.0.0.1:8888/api/admin/orders?page={current - 1}" if current > 1 else None,
                    next=f"http://127.0.0.1:8888/api/admin/orders?page={current + 1}" if current < total_pages else None
                )
            )
        )
    )


# 订单详情接口
@admin_orders.get("/{order_id}", response_model=OrderBase)
async def get_order_details(
        order_id: int = Path(..., description="The order ID to retrieve details for"),
        include: Optional[str] = Query(None, description="Fields to include like goods, user, orderDetails"),
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

    # 查找订单
    order = await Orders.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 根据需要预加载数据
    if "user" in include.split(','):
        await order.fetch_related("user")
    if "orderDetails" in include.split(','):
        order_details = await OrderDetails.filter(order=order).prefetch_related(
            "goods") if "goods" in include else await OrderDetails.filter(order=order)

    # 计算 address_id
    order_address = await order.address.first()
    order_address_id = order_address.id if order_address else None

    # 构建订单基本信息
    order_data = OrderBase(
        id=order.id,
        order_no=order.order_no,
        user_id=order.user.id if order.user else None,
        amount=order.amount,
        status=order.status,
        address_id=order_address_id if order.address else None,
        express_type=order.express_type,
        express_no=order.express_no,
        pay_time=order.pay_time.strftime('%Y-%m-%d %H:%M:%S') if order.pay_time else None,
        pay_type=order.pay_type,
        trade_no=order.trade_no,
        created_at=order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        updated_at=order.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        user=UserBase(**order.user.__dict__) if "user" in include.split(',') and order.user else None,
        goods=[GoodsBase(**detail.goods.__dict__) for detail in
               order_details] if "goods" in include.split(',') else [],
        orderDetails=[OrderDetailsBase(**detail.__dict__) for detail in
                      order_details] if "orderDetails" in include.split(',') else []
    )

    return order_data


class ShippingInfo(BaseModel):
    express_type: str
    express_no: str


@admin_orders.patch("/{order_id}/post", status_code=204)
async def post_order(
        express_type: str,
        express_no: str,
        order_id: int = Path(..., description="The order ID to be updated"),
        token: str = Depends(oauth2_scheme)
):
    # 解码JWT token来验证并获取用户信息
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 确保用户存在
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 查找订单
    order = await Orders.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 更新订单的快递类型和快递单号
    order.express_type = express_type
    order.express_no = express_no
    order.status = 3
    await order.save()

    return {}


class OrderModel(BaseModel):
    id: int
    order_no: str
    user_id: int
    amount: float
    status: int
    address_id: int
    express_type: str
    express_no: str
    pay_time: str
    pay_type: str
    trade_no: str
    created_at: str
    updated_at: str


@admin_orders.get("/fetch_all", response_model=List[OrderModel])
async def fetch_all_orders(token: str = Depends(oauth2_scheme)):
    # 解码JWT token来验证并获取用户信息
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 确保用户存在
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Fetch all orders without applying pagination
        orders = await Orders.all()
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
