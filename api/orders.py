# -*- coding: utf-8 -*-
# @Time    : 2024/4/27 20:58
# @Author  : KuangRen777
# @File    : orders.py
# @Tags    :
from fastapi import APIRouter, Request, HTTPException, Depends, status, UploadFile, File, Path, Query
from models import Goods, Category, Comments, Users, OrderDetails, Orders, Cart, Address
from tortoise.functions import Count
from tortoise.query_utils import Prefetch
import json
from pydantic import BaseModel, Field, HttpUrl, conint
import shutil
import os
from typing import List, Optional
from tortoise.transactions import in_transaction
import re

from utils import *

api_orders = APIRouter()


class GoodsTemp:
    def __init__(self, id, cover, title):
        self.id = id
        self.cover = cover
        self.title = title
        self.cover_url = f'http://127.0.0.1/{self.cover}'

    def dict(self):
        return {
            "id": self.id,
            "cover": self.cover,
            "title": self.title,
            "cover_url": self.cover_url
        }


class GoodsTempDetails:
    def __init__(self, id, cover, title, cover_url):
        self.id = id
        self.cover = cover
        self.title = title
        self.cover_url = cover_url

    def dict(self):
        return {
            "id": self.id,
            "cover": self.cover,
            "title": self.title,
            "cover_url": self.cover_url
        }


class CartTemp:
    def __init__(self, id, user_id, goods_id, num, is_checked, created_at, updated_at, goods=None):
        self.id = id
        self.user_id = user_id
        self.goods_id = goods_id
        self.num = num
        self.is_checked = is_checked
        self.created_at = created_at
        self.updated_at = updated_at
        self.goods = goods

    def dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "goods_id": self.goods_id,
            "num": self.num,
            "is_checked": self.is_checked,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "goods": self.goods.dict() if self.goods else None
        }


class AddressTemp:
    def __init__(self, id, name, province, city, county, address, phone, is_default, created_at, updated_at):
        self.id = id
        self.name = name
        self.province = province
        self.city = city
        self.county = county
        self.address = address
        self.phone = phone
        self.is_default = is_default
        self.created_at = created_at
        self.updated_at = updated_at

    def dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "province": self.province,
            "city": self.city,
            "county": self.county,
            "address": self.address,
            "phone": self.phone,
            "is_default": self.is_default,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class OrdersTemp:
    def __init__(self, id, order_no, user_id, amount, status, address_id, express_type, express_no, pay_time, pay_type,
                 trade_no, created_at, updated_at):
        self.id = id
        self.order_no = order_no
        self.user_id = user_id
        self.amount = amount
        self.status = status
        self.address_id = address_id
        self.express_type = express_type
        self.express_no = express_no
        self.pay_time = pay_time
        self.pay_type = pay_type
        self.trade_no = trade_no
        self.created_at = created_at
        self.updated_at = updated_at

    def dict(self):
        return {
            "id": self.id,
            "order_no": self.order_no,
            "user_id": self.user_id,
            "amount": self.amount,
            "status": self.status,
            "address_id": self.address_id,
            "express_type": self.express_type,
            "express_no": self.express_no,
            "pay_time": self.pay_time,
            "pay_type": self.pay_type,
            "trade_no": self.trade_no,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class UserTemp:
    def __init__(self, id, email, username, phone, avatar, created_at, updated_at):
        self.id = id
        self.email = email
        self.username = username
        self.phone = phone
        self.avatar = avatar
        self.created_at = created_at
        self.updated_at = updated_at

    def dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "phone": self.phone,
            "username": self.username,
            "avatar": self.avatar,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class OrderDetailsTemp:
    def __init__(self, id, order_id, goods_id, num, price):
        self.id = id
        self.order_id = order_id
        self.goods_id = goods_id
        self.num = num
        self.price = price
        self.goods = None  # To hold related GoodsTemp

    def dict(self):
        result = vars(self)
        if self.goods:
            result['goods'] = self.goods.dict()
        return result


class OrderCreateRequest(BaseModel):
    address_id: int = Field(..., description="The ID of the address to deliver the order to")


@api_orders.get("/preview")
async def order_preview(token: str = Depends(oauth2_scheme)):
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

    # Fetch default address or fallback to any address
    address = await Address.filter(user_id=user_id, is_default=1).first()
    if not address:
        address = await Address.filter(user_id=user_id).first()
    if not address:
        raise HTTPException(status_code=404, detail="No address found")

    # Fetch checked cart items and related goods
    cart_items = await Cart.filter(user_id=user_id, is_checked=1).prefetch_related('goods')

    return {
        "address": [AddressTemp(
            address.id,
            address.name,
            address.province,
            address.city,
            address.county,
            address.address,
            address.phone,
            address.is_default,
            address.created_at,
            address.updated_at
        ).dict()],
        "carts": [CartTemp(
            cart_item.id,
            cart_item.user_id,
            cart_item.goods_id,
            cart_item.num,
            cart_item.is_checked,
            cart_item.created_at,
            cart_item.updated_at,
            GoodsTemp(
                cart_item.goods.id,
                cart_item.goods.cover,
                cart_item.goods.title,
            )
        ) for cart_item in cart_items]

    }


@api_orders.post("/", status_code=status.HTTP_201_CREATED)
async def submit_order(order_request: OrderCreateRequest, token: str = Depends(oauth2_scheme)):
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

    async with in_transaction():
        # Check if the address exists and belongs to the user
        address = await Address.get_or_none(id=order_request.address_id, user_id=user.id)
        if not address:
            raise HTTPException(status_code=404, detail="Address not found or address is not yours.")

        # Retrieve all checked cart items
        cart_items = await Cart.filter(user_id=user.id, is_checked=1).prefetch_related('goods')

        # Calculate the total amount and prepare order details
        total_amount = 0
        order_details = []
        for item in cart_items:
            if item.goods.stock < item.num:
                raise HTTPException(status_code=400, detail=f"{item.goods.title} stock is insufficient.")

            # Update stock
            item.goods.stock -= item.num
            await item.goods.save()
            total_amount += item.goods.price * item.num

            # Prepare order detail
            detail = OrderDetails(
                order=None,  # to be filled after order creation
                goods_id=item.goods.id,
                price=item.goods.price,
                num=item.num
            )
            order_details.append(detail)

        # Create the order
        order = await Orders.create(
            user=user,
            order_no=generate_order_no(),
            amount=total_amount,
            address=address,
            status=1
        )

        # Link order details to the created order and save them
        for detail in order_details:
            detail.order = order
            await detail.save()

        return OrdersTemp(
            order.id,
            order.order_no,
            user_id,
            order.amount,
            order.status,
            address.id,
            order.express_type,
            order.express_no,
            order.pay_time,
            order.pay_type,
            order.trade_no,
            order.created_at,
            order.updated_at
        ).dict()


@api_orders.get("/{order_id}")
async def get_order_details(
    order_id: int,
    include: Optional[str] = Query(None),
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

    order = await Orders.get_or_none(id=order_id).prefetch_related('order_details')
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    address = await order.address
    user = await order.user

    # Optionally fetch related data based on include parameter
    related_data = {}
    if include:
        includes = re.split(r'[,.]', include)
        # print(includes)
        if 'user' in includes:
            related_data['user'] = UserTemp(
                user.id,
                user.email,
                user.name,
                user.phone,
                user.avatar,
                transfer_time_datetime(user.created_at),
                transfer_time_datetime(user.updated_at)
            ).dict() if user else None
        if 'address' in includes:
            related_data['address'] = AddressTemp(
                address.id,
                address.name,
                address.province,
                address.city,
                address.county,
                address.address,
                address.phone,
                address.is_default,
                transfer_time_datetime(address.created_at),
                transfer_time_datetime(address.updated_at)
            ).dict() if order.address else None
        if 'orderDetails' in includes:
            details = []
            for detail in order.order_details:
                detail_temp = OrderDetailsTemp(
                    id=detail.id,
                    order_id=detail.order_id,
                    goods_id=detail.goods_id,
                    num=detail.num,
                    price=detail.price
                )
                if 'goods' in includes:
                    order_details = await OrderDetails.get_or_none(id=detail.id)

                    goods = await order_details.goods
                    if goods:
                        detail_temp.goods = GoodsTemp(
                            id=goods.id,
                            cover=goods.cover,
                            title=goods.title
                        )
                details.append(detail_temp)
            related_data['orderDetails'] = [d.dict() for d in details]

    # Create an OrdersTemp instance
    order_temp = OrdersTemp(
        id=order.id,
        order_no=order.order_no,
        user_id=user.id,
        amount=order.amount,
        status=order.status,
        address_id=address.id,
        express_type=order.express_type,
        express_no=order.express_no,
        pay_time=order.pay_time,
        pay_type=order.pay_type,
        trade_no=order.trade_no,
        created_at=transfer_time_datetime(order.created_at),
        updated_at=transfer_time_datetime(order.created_at)
    )

    response_data = order_temp.dict()
    response_data.update(related_data)  # Add related data to the response

    # print(response_data)
    return response_data
