# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 15:17
# @Author  : KuangRen777
# @File    : goods.py
# @Tags    :
from fastapi import APIRouter, Request, HTTPException, Depends, status
from models import Goods, Category, Comments, Users, OrderDetails, Orders
from tortoise.functions import Count
from tortoise.query_utils import Prefetch
import json
from pydantic import BaseModel


from utils import *

api_goods = APIRouter()


class GoodsTemp:
    def __init__(self, id, title, price, cover, category_id, sales, updated_at, comments_count, collects_count, cover_url):
        self.id = id
        self.title = title
        self.price = price
        self.cover = cover
        self.category_id = category_id
        self.sales = sales
        self.updated_at = updated_at
        self.comments_count = comments_count
        self.collects_count = collects_count
        self.cover_url = cover_url

    def dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'cover': self.cover,
            'category_id': self.category_id,
            'sales': self.sales,
            'updated_at': self.updated_at,
            'comments_count': self.comments_count,
            'collects_count': self.collects_count,
            'cover_url': self.cover_url,
        }


class CategoryTemp:
    def __init__(self, id, name, pid, level, status_, seq):
        self.id = id
        self.name = name
        self.pid = pid
        self.level = level
        self.status = status_
        self.seq = seq
        self.children = []

    def add_child(self, child):
        self.children.append(child)


class CommentRequest(BaseModel):
    goods_id: int
    content: str
    rate: int = None
    star: int = None


@api_goods.get('')
async def goods(request: Request):
    # Extract query parameters
    page = int(request.query_params.get('page', 1)) - 1
    title = request.query_params.get('title', None)
    category_id = request.query_params.get('category_id', None)
    print(category_id)
    sales = int(request.query_params.get('sales', 0))
    recommend = int(request.query_params.get('recommend', 0))
    price = int(request.query_params.get('price', 0))
    comments_count = int(request.query_params.get('comments_count', 0))

    categories_query = await Category.filter(group='menu').all()
    categories = [CategoryTemp(c.id, c.name, c.pid, c.level, c.status, 1) for c in categories_query]
    categories_tree = build_tree(categories)

    # Initial query setup
    query = Goods.filter(is_on=1)
    if title:
        query = query.filter(title__icontains=title)

    if category_id != 0:
        query = query.filter(category_id=category_id)

    if recommend == 1:
        query = query.filter(is_recommend=1)

    # Apply sort
    sort_expr = []
    if sales:
        sort_expr.append('-sales' if sales == 1 else 'sales')
    if price:
        sort_expr.append('-price' if price == 1 else 'price')

    query = query.annotate(comments_count=Count("reviews__id"))
    # Calculate comments count and include it in initial query if needed
    if comments_count:
        sort_expr.append('-comments_count' if comments_count == 1 else 'comments_count')

    if sort_expr:
        query = query.order_by(*sort_expr)

    # Pagination
    goods_list = await query.offset(page * 10).limit(10).all()
    goods_list = [GoodsTemp(g.id, g.title, g.price, g.cover, g.category_id, g.sales, transfer_time(str(g.updated_at)),
                            g.comments_count, 0,
                            f'http://127.0.0.1:8888/upimg/goods_cover/{g.cover}') for g in goods_list]

    # Prepare the response
    # total_items = await query.count()
    # total_pages = (total_items + 9) // 10

    recommend_goods = await Goods.filter(is_recommend=1).offset(0).limit(10).all()
    return {
        "goods": {
            "current_page": page + 1,
            "data": [g for g in goods_list],
        },
        "recommend_goods": recommend_goods,
        "categories": categories_tree,
        # "total_pages": total_pages,
    }


@api_goods.get("/{good_id}")
async def get_good_details(good_id: int):
    """
    异步获取指定ID商品及其关联数据。

    参数:
    - good_id: 商品的唯一标识符。

    返回值:
    - goods: 包含指定商品及其预加载的相关数据的对象。例如，商品评论、用户信息和商品类别。
    """
    goods = await Goods.filter(id=good_id).prefetch_related(
        Prefetch("reviews", queryset=Comments.all().prefetch_related(Prefetch("user", queryset=Users.all()), "order")),
        # 预加载商品的所有评论及其用户和订单信息
        Prefetch("user", queryset=Users.all()),  # 预加载商品的发布用户信息
        Prefetch("category", queryset=Category.all())  # 预加载商品所属的类别信息
    ).first()  # 获取查询结果中的第一个商品

    if not goods:
        raise HTTPException(status_code=404, detail="Goods not found")

    # Assuming 'like_goods' are similar items in the same category excluding the current item
    like_goods = await Goods.filter(category=goods.category).exclude(id=good_id).limit(5).all()

    # Check if goods.pics is already a dict or list; if not, parse it
    goods_pics = goods.pics if isinstance(goods.pics, (dict, list)) else json.loads(goods.pics) if goods.pics else []

    return {
        "goods": {
            "id": goods.id,
            "user_id": goods.user.id,
            # "user_name": goods.user.name,
            "category_id": goods.category.id,
            # "category_name": goods.category.name,
            "title": goods.title,
            "description": goods.description,
            "price": goods.price,
            "stock": goods.stock,
            "sales": goods.sales,
            "cover": goods.cover,
            "pics": goods.pics,
            "is_on": 1 if bool(goods.is_on) else 0,
            "is_recommend": 1 if bool(goods.is_recommend) else 0,
            "details": goods.details,
            "created_at": transfer_time(str(goods.created_at.isoformat())) if goods.created_at else None,
            "updated_at": transfer_time(str(goods.updated_at.isoformat())) if goods.updated_at else None,
            "collects_count": 0,
            "cover_url": goods.cover,
            "pics_url": goods_pics,
            "is_collected": 0,
            "comments": [
                {
                    "id": comment.id,
                    "user_id": comment.user.id,
                    # "user_name": comment.user.name,
                    "order_id": comment.order.id,
                    "goods_id": goods.id,
                    "rate": comment.rate,
                    "star": comment.star,
                    "content": comment.content,
                    "reply": comment.reply,
                    "pics": json.loads(comment.pics) if comment.pics else [],
                    "created_at": transfer_time(str(comment.created_at.isoformat())) if comment.created_at else None,
                    "updated_at": transfer_time(str(comment.updated_at.isoformat())) if comment.updated_at else None,
                    "user": {
                        "id": comment.user.id,
                        "name": comment.user.name,
                        "avatar": comment.user.avatar,
                        "avatar_url": f'https://127.0.0.1:8888/upimg/avatars/{comment.user.avatar}.png'
                        if comment.user.avatar else None,
                    }
                } for comment in goods.reviews
            ]
        },
        "like_goods": [
            {
                "id": lg.id,
                "title": lg.title,
                "price": lg.price,
                "cover_url": lg.cover,
                "sales": lg.sales
            } for lg in like_goods
        ]
    }


@api_goods.post("/comment", status_code=status.HTTP_201_CREATED)
async def post_comment(request: CommentRequest, token: str = Depends(oauth2_scheme)):
    # Decode the JWT token to authenticate the user
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        user = await Users.get(email=user_email)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure the user has purchased the goods and confirmed receipt
    order = await Orders.filter(user_id=user.id, order_details__goods__id=request.goods_id, status=4).first()
    if not order:
        raise HTTPException(status_code=400, detail={"message": "商品还没有购买，不能参与评价", "status_code": 400})

    # Check if the user has already commented on this goods
    existing_comment = await Comments.filter(user_id=user.id, goods_id=request.goods_id).exists()
    if existing_comment:
        raise HTTPException(status_code=400, detail={"message": "此商品已经评论过了", "status_code": 400})

    # Create the comment
    new_comment = await Comments.create(
        user_id=user.id,
        goods_id=request.goods_id,
        content=request.content,
        rate=request.rate,
        star=request.star,
        order_id=order.id,
    )

    return {"message": "评论创建成功", "status_code": 201}



