# -*- coding: utf-8 -*-
# @Time    : 2024/4/27 20:58
# @Author  : KuangRen777
# @File    : orders.py
# @Tags    :
from fastapi import APIRouter, Request, HTTPException, Depends, status, UploadFile, File, Path, Query, Body
from models import Goods, Category, Comments, Users, OrderDetails, Orders, Cart, Address
from tortoise.functions import Count, Sum
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
        self.cover_url = f'http://127.0.0.1:8888/upimg/goods_cover/{self.cover}'

    def dict(self):
        return {
            "id": self.id,
            "cover": self.cover,
            "title": self.title,
            "cover_url": self.cover_url
        }


class GoodsTempWithPrice:
    def __init__(self, id, cover, title, price):
        self.id = id
        self.cover = cover
        self.title = title
        self.cover_url = f'http://127.0.0.1:8888/upimg/goods_cover/{self.cover}'
        self.price = price

    def dict(self):
        return {
            "id": self.id,
            "cover": self.cover,
            "title": self.title,
            "cover_url": self.cover_url,
            "price": self.price
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


class AddressByOrderPreviewTemp:
    def __init__(self, id, user_id, name, province, city, county, address, phone, is_default, created_at, updated_at):
        self.id = id
        self.user_id = user_id
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
            "user_id": self.user_id,
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
    address_user = await address.user

    return {
        "address": [AddressByOrderPreviewTemp(
            address.id,
            address_user.id,
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
            GoodsTempWithPrice(
                cart_item.goods.id,
                cart_item.goods.cover,
                cart_item.goods.title,
                cart_item.goods.price
            )
        ) for cart_item in cart_items]

    }


async def remove_cart_items(cart_items):
    for item in cart_items:
        await item.delete()  # Assuming a delete method is available


@api_orders.post("", status_code=status.HTTP_201_CREATED)
async def submit_order(address_id: int, token: str = Depends(oauth2_scheme)):
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
        address = await Address.get_or_none(id=address_id, user_id=user.id)
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

        # Remove cart items after order is successfully created
        await remove_cart_items(cart_items)

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
            order_details = await order.order_details
            for detail in order_details:
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


@api_orders.get("")
async def list_orders(
        title: Optional[str] = Query(None),
        include: Optional[str] = Query(None),
        status: Optional[int] = Query(None),
        token: str = Depends(oauth2_scheme),
        page: int = Query(1, gt=0),
        per_page: int = Query(10, gt=0)
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

    # Base query with optional filters
    query = Orders.filter(user_id=user.id).prefetch_related('order_details')
    if status is not None:
        if status == 0:
            query = query.filter(status__in=[1, 2, 3, 4, 5]).order_by('-created_at')
        else:
            query = query.filter(status=status).order_by('-created_at')
    if title is not None:
        query = query.filter(order_details__goods__title__icontains=title)

    # Pagination setup
    total = await query.count()
    orders = await query.offset((page - 1) * per_page).limit(per_page)

    includes = re.split(r'[,.]', include) if include else []

    results = []
    for order in orders:
        address = await order.address
        user = await order.user

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
        ).dict()

        related_data = order_temp

        if include:
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
                ).dict() if address else None
            if 'orderDetails' in includes:
                details = []
                order_details = await order.order_details
                for detail in order_details:
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

        results.append(related_data)

    # Construct the response with pagination metadata
    response = {
        "data": results,
        "meta": {
            "pagination": {
                "total": total,
                "count": len(results),
                "per_page": per_page,
                "current_page": page,
                "total_pages": (total + per_page - 1) // per_page,
                "links": {
                    "previous": f"/api/orders?page={page - 1}&per_page={per_page}" if page > 1 else None,
                    "next": f"/api/orders?page={page + 1}&per_page={per_page}" if page * per_page < total else None
                } if total > per_page else None
            }
        }
    }

    return response


@api_orders.get("/{order_id}/express")
async def get_order_express(
        order_id: int = Path(..., description="The ID of the order"),
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

    # Retrieve the order from the database
    order = await Orders.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_user = await order.user
    if order_user.id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")

    # Check if order has necessary details for tracking
    if not order.express_type or not order.express_no:
        raise HTTPException(status_code=400, detail="无效的输入[缺少快递单号或订单编号]")

    # Call the external tracking service
    try:
        result = delivery_query(order.express_type, order.express_no, None, None, None)
    except Exception as e:  # Broad exception handling for demonstration; specify your exceptions
        raise HTTPException(status_code=500, detail="内部服务器错误 500。 内部请求出错")

    # Return the result from the tracking service
    return {
        "EBusinessID": "test1371565",
        "OrderCode": "",
        "ShipperCode": "SF",
        "LogisticCode": "121212",
        "Success": True,
        "State": "3",
        "Reason": None,
        "Traces": [
            {
                "AcceptTime": "2024-04-05 09:00:00",
                "AcceptStation": "到达【北京】北京昌平区回龙观二街",
                "Remark": "在途",
            },
            {
                "AcceptTime": "2024-04-02 09:00:00",
                "AcceptStation": "到达【南京】南京分发中心",
                "Remark": "在途",
            },
            {
                "AcceptTime": "2024-04-02 09:00:00",
                "AcceptStation": "快递由快递员【小明】揽收",
                "Remark": "揽收中",
            }
        ]
    }


@api_orders.patch("/{order_id}/confirm")
async def confirm_order_receipt(
        order_id: int = Path(..., description="The ID of the order to confirm receipt for"),
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

    # Retrieve the order from the database
    order = await Orders.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_user = await order.user

    # Ensure the order belongs to the user making the request
    if order_user.id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to confirm receipt for this order")

    # Check if the order is in the shipped state (status=3)
    if order.status != 3:
        raise HTTPException(status_code=400, detail="订单状态异常")

    # Update the order status to 'received' (assuming status=4 for received)
    order.status = 4
    await order.save()

    # Respond with no content on successful update
    return {"message": "Order confirmed successfully", "status": 204}


@api_orders.post("/{order_id}/comment")
async def comment_on_product(
        order_id: int = Path(..., description="The ID of the order"),
        goods_id: int = Body(..., embed=True),
        content: str = Body(..., embed=True),
        rate: int = Body(1, embed=True),
        star: int = Body(5, embed=True),
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

    # Retrieve the order
    order = await Orders.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_user = await order.user

    # Ensure the order belongs to the user making the request
    if order_user.id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to comment on this order")

    # Ensure the order is in the confirmed receipt state
    if order.status != 4:
        raise HTTPException(status_code=400, detail="订单状态异常")

    # Check if the goods_id is part of this order
    order_detail = await OrderDetails.get_or_none(order_id=order_id, goods_id=goods_id)
    if not order_detail:
        raise HTTPException(status_code=400, detail="此订单不包含该商品")

    # Check if the product has already been commented on
    existing_comment = await Comments.get_or_none(order_id=order_id, goods_id=goods_id)
    if existing_comment:
        raise HTTPException(status_code=400, detail="此商品已经评论过了")

    # Create the comment
    comment = await Comments.create(
        user_id=user.id,
        order_id=order_id,
        goods_id=goods_id,
        content=content,
        rate=rate,
        star=star
    )

    return {"message": "Comment added successfully", "comment_id": comment.id}, 201


# @api_orders.patch("/{order_id}/paytest")
@api_orders.get("/{order_id}/pay")
async def simulate_payment(
        type: str,
        order_id: int = Path(..., description="The ID of the order to simulate payment for"),
        token: str = Depends(oauth2_scheme)
):
    payment_type = type
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

    # Retrieve the order
    order = await Orders.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_user = await order.user

    # Ensure the order belongs to the user making the request
    if order_user.id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to perform payment on this order")

    # Check if the order is in the 'created' state
    if order.status != 1:
        raise HTTPException(status_code=400, detail="订单状态异常, 请重新下单")

    order_detail = await OrderDetails.filter(order_id=order_id).first()
    if not order_detail:
        raise HTTPException(status_code=404, detail="No items found in the order")

    good = await order_detail.goods.first()

    # Calculate the total quantity of all items in the order
    total_quantity = await OrderDetails.filter(order_id=order_id).annotate(total=Sum('num')).values('total')

    # Ensure there's a result for total quantity and extract it
    total_quantity = total_quantity[0]['total'] if total_quantity else 0

    # Simulate payment processing
    if payment_type == "aliyun":
        payment_details = {
            "out_trade_no": f"{order_id}_{get_current_time_str()}",
            "total_amount": order.amount,
            "subject": f"{good.title} 等 {total_quantity} 件商品"
        }
    elif payment_type == "wechat":
        payment_details = {
            "out_trade_no": f"{order_id}_{get_current_time_str()}",
            "total_fee": order.amount,
            "body": f"{good.title} 等 {total_quantity} 件商品"
        }
    else:
        payment_details = {
            "out_trade_no": f"{order_id}_{get_current_time_str()}",
            "total_fee": order.amount,
            "body": f"{good.title} 等 {total_quantity} 件商品"
        }

    # Update the order status to 'paid'
    order.status = 2
    await order.save()

    return payment_details


"""这个功能没有测试，因为好像可以直接用模拟支付"""


# @api_orders.get("/{order_id}/pay")
async def get_payment_qr_code(
        type: str,
        order_id: int = Path(..., description="The ID of the order to generate QR code for"),
        # payment_type: str = Query(..., regex="^(aliyun|wechat)$", description="The payment platform to use"),
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

    # Fetch the order to validate status
    order = await Orders.get_or_none(id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_user = await order.user

    if order_user.id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this order")
    if order.status != 1:
        raise HTTPException(status_code=400, detail="订单状态异常, 请重新下单")

    # Depending on the payment type, prepare the response
    payment_type = type
    if payment_type == "aliyun":
        qr_code_url = "http://127.0.0.1:8888/upimg/alipay.png"
        response = {
            "code": "10000",
            "msg": "Success",
            "out_trade_no": str(order_id),
            "qr_code_url": qr_code_url,
        }
    elif payment_type == "wechat":
        qr_code_url = "/upimg/pay_qrcode.jpg"
        response = {
            "return_code": "SUCCESS",
            "return_msg": "OK",
            "appid": "wx_dummy_appid",
            "mch_id": "dummy_mch_id",
            "nonce_str": "dummy_nonce_str",
            "sign": "dummy_sign",
            "result_code": "SUCCESS",
            "prepay_id": "dummy_prepay_id",
            "trade_type": "NATIVE",
            "code_url": qr_code_url,
            "qr_code_url": 'http://127.0.0.1:8888/upimg/alipay.png'
        }
    else:
        qr_code_url = "/upimg/pay_qrcode.jpg"
        response = {
            "return_code": "SUCCESS",
            "return_msg": "OK",
            "appid": "wx_dummy_appid",
            "mch_id": "dummy_mch_id",
            "nonce_str": "dummy_nonce_str",
            "sign": "dummy_sign",
            "result_code": "SUCCESS",
            "prepay_id": "dummy_prepay_id",
            "trade_type": "NATIVE",
            "code_url": qr_code_url,
            "qr_code_url": 'http://127.0.0.1:8888/upimg/alipay.png'
        }

    return response


@api_orders.get("/{order_id}/status")
async def get_order_status(
        order_id: int = Path(..., description="The ID of the order to check status for"),
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

    time.sleep(1)

    order = await Orders.get_or_none(id=order_id)
    order.status = 2
    await order.save()

    return '2'

