# -*- coding: utf-8 -*-
# @Time    : 2024/4/27 15:32
# @Author  : KuangRen777
# @File    : carts.py
# @Tags    :
from fastapi import APIRouter, Request, HTTPException, Depends, status, UploadFile, File, Path
from models import Goods, Category, Comments, Users, OrderDetails, Orders, Cart
from tortoise.functions import Count
from tortoise.query_utils import Prefetch
import json
from pydantic import BaseModel, Field, HttpUrl, conint
import shutil
import os
from typing import List, Optional

from utils import *

api_cart = APIRouter()


class CartItemAddRequest(BaseModel):
    goods_id: int
    num: int = Field(default=1, ge=1)


class GoodsTemp:
    def __init__(self, id, title, category_id, user_id, description, price, stock, sales, cover, cover_url, pics,
                 pics_url, details, is_on, is_recommend, created_at, updated_at):
        self.id = id
        self.title = title
        self.category_id = category_id
        self.user_id = user_id
        self.description = description
        self.price = price
        self.stock = stock
        self.sales = sales
        self.cover = cover
        self.cover_url = cover_url
        self.pics = pics
        self.pics_url = pics_url
        self.details = details
        self.is_on = is_on
        self.is_recommend = is_recommend
        self.created_at = created_at
        self.updated_at = updated_at

    def dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category_id": self.category_id,
            "user_id": self.user_id,
            "description": self.description,
            "price": self.price,
            "stock": self.stock,
            "sales": self.sales,
            "cover": self.cover,
            "cover_url": self.cover_url,
            "pics": self.pics,
            "pics_url": self.pics_url,
            "details": self.details,
            "is_on": self.is_on,
            "is_recommend": self.is_recommend,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class CartItems:
    def __init__(self, id, user_id, goods_id, num, is_checked, goods=None):
        self.id = id
        self.user_id = user_id
        self.goods_id = goods_id
        self.num = num
        self.is_checked = is_checked
        self.goods = goods

    def dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "goods_id": self.goods_id,
            "num": self.num,
            "is_checked": self.is_checked,
            "goods": self.goods.dict() if self.goods else None
        }

    def dict_without_goods(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "goods_id": self.goods_id,
            "num": self.num,
            "is_checked": self.is_checked,
        }


class CartQuantityUpdateRequest(BaseModel):
    num: str


class CartCheckedUpdateRequest(BaseModel):
    cart_ids: List[int] = Field(..., description="List of cart IDs to be checked")


@api_cart.post("/", status_code=status.HTTP_201_CREATED)
async def add_to_cart(item_request: CartItemAddRequest, token: str = Depends(oauth2_scheme)):
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

    # Check if the goods exist
    goods = await Goods.get_or_none(id=item_request.goods_id)
    if not goods:
        raise HTTPException(status_code=404, detail="Goods not found")

    # Check if the item is already in the cart
    cart_item = await Cart.get_or_none(user_id=user_id, goods_id=item_request.goods_id)
    if cart_item:
        cart_item.num += item_request.num  # Update quantity
    else:
        # Add new item to the cart
        cart_item = await Cart.create(user_id=user_id, goods_id=item_request.goods_id, num=item_request.num)

    await cart_item.save()
    return {"message": "Added to cart successfully"}


@api_cart.get("/")
async def get_cart_items(request: Request, token: str = Depends(oauth2_scheme)):
    include = request.query_params.get("include")
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

    cart_items_query = Cart.filter(user_id=user_id)

    print(include)

    if include == "goods":
        cart_items_query = cart_items_query.prefetch_related("goods")

    items = await cart_items_query.all()

    if include == "goods":
        resp = {
            "data": [
                CartItems(
                    id=item.id,
                    user_id=item.user_id,
                    goods_id=item.goods_id,
                    num=item.num,
                    is_checked=item.is_checked,
                    goods=
                    GoodsTemp(
                        id=item.goods.id,
                        title=item.goods.title,
                        category_id=item.goods.category_id,
                        user_id=item.goods.user_id,
                        description=item.goods.description,
                        price=item.goods.price,
                        stock=item.goods.stock,
                        sales=item.goods.sales,
                        cover=item.goods.cover,
                        cover_url=f'http://127.0.0.1:8000/upimg/goods_cover/{item.goods.cover}',
                        pics=item.goods.pics,
                        pics_url=[],  # TODO: 这里还没弄
                        details=item.goods.details,
                        is_on=item.goods.is_on,
                        is_recommend=item.goods.is_recommend,
                        created_at=transfer_time(str(item.goods.created_at)),
                        updated_at=transfer_time(str(item.goods.updated_at))
                    ).dict()

                ) for item in items
            ]
        }
    else:
        resp = {
            "data": [
                CartItems(
                    id=item.id,
                    user_id=item.user_id,
                    goods_id=item.goods_id,
                    num=item.num,
                    is_checked=item.is_checked,
                ).dict_without_goods() for item in items
            ]
        }

    return resp


@api_cart.put("/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_cart_quantity(cart_id: int,
                               request: CartQuantityUpdateRequest,
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

    # Verify and fetch the cart item
    cart_item = await Cart.get_or_none(id=cart_id, user_id=user_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found or does not belong to user")

    # Update the quantity
    cart_item.num += eval(request.num)
    await cart_item.save()

    return {}


@api_cart.delete("/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(cart_id: int = Path(..., description="购物车ID"), token: str = Depends(oauth2_scheme)):
    # Decode the JWT token to authenticate and get user ID
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

    # Fetch the cart item to ensure it belongs to the user
    cart_item = await Cart.get_or_none(id=cart_id, user_id=user_id)
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found or does not belong to user")

    # Delete the cart item
    await cart_item.delete()

    return {}


@api_cart.patch("/checked", status_code=status.HTTP_204_NO_CONTENT)
async def update_cart_checked_state(request: CartCheckedUpdateRequest,
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

    # Fetch all cart items for the user
    cart_items = await Cart.filter(user_id=user_id)

    # Update the checked state based on passed IDs
    checked_ids = set(request.cart_ids)
    for item in cart_items:
        item.is_checked = 1 if item.id in checked_ids else 0
        await item.save()

    return {}
