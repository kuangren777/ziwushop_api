# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 15:17
# @Author  : KuangRen777
# @File    : goods.py
# @Tags    :
from fastapi import APIRouter, Request
from models import Goods, Category
from tortoise.functions import Count

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
    def __init__(self, id, name, pid, level, status, seq):
        self.id = id
        self.name = name
        self.pid = pid
        self.level = level
        self.status = status
        self.seq = seq
        self.children = []

    def add_child(self, child):
        self.children.append(child)


@api_goods.get('/goods')
async def goods(request: Request):
    # Extract query parameters
    page = int(request.query_params.get('page', 1)) - 1
    title = request.query_params.get('title', None)
    category_id = int(request.query_params.get('category_id', None))
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
                            f'https://127.0.0.1:8888/upimg/goods_cover/{g.cover}.png') for g in goods_list]

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
