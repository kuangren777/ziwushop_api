# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 12:11
# @Author  : KuangRen777
# @File    : index.py
# @Tags    :
from fastapi import APIRouter, Request
from models import Slides, Goods, Category
from datetime import datetime

from utils import *

api_index = APIRouter()


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


class GoodsTemp:
    def __init__(self, id, title, price, stock, sales, cover, description, collects_count, cover_url):
        self.id = id
        self.title = title
        self.price = price
        self.stock = stock
        self.sales = sales
        self.cover = cover
        self.description = description
        self.collects_count = collects_count
        self.cover_url = cover_url

    def dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "price": self.price,
            "stock": self.stock,
            "sales": self.sales,
            "cover": self.cover,
            "description": self.description,
            "collects_count": self.collects_count,
            "cover_url": self.cover_url
        }


class SlidesTemp:
    def __init__(self, id, title, url, img, status, seq, created_at, updated_at, img_url):
        self.id = id
        self.title = title
        self.url = url
        self.img = img
        self.status = status
        self.seq = seq
        self.created_at = created_at
        self.updated_at = updated_at
        self.img_url = img_url

    def dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "img": self.img,
            "status": self.status,
            "seq": self.seq,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "img_url": self.img_url
        }


@api_index.get('/index')
async def index(request: Request):
    json_data = request.query_params
    page = int(json_data.get('page', 1)) - 1  # API 通常从第1页开始计数，而程序内部从第0页开始
    sales = json_data.get('sales', '0') == '1'
    recommend = json_data.get('recommend', '0') == '1'
    new = json_data.get('new', '0') == '1'

    categories_query = await Category.filter(group='menu').all()
    categories = [CategoryTemp(c.id, c.name, c.pid, c.level, c.status, 1) for c in categories_query]
    categories_tree = build_tree(categories)

    goods_query = Goods.filter(is_on=1)
    if sales:
        goods_query = goods_query.filter(sales__gt=50).order_by('-sales')
    if recommend:
        goods_query = goods_query.filter(is_recommend=1)
    if new:
        goods_query = goods_query.order_by('-created_at')

    total_items = await goods_query.count()

    if total_items == 0 or page * 10 >= total_items:
        # 如果没有商品或请求的页码超过了可用商品数
        goods_resp = {
            "categories": categories_tree,
            "goods": {
                "current_page": page + 1,
                "data": [],
                "first_page_url": f"https://127.0.0.1/api/index?page=1",
                "from": None,
                "next_page_url": None,
                "path": "https://127.0.0.1/api/index",
                "per_page": 10,
                "prev_page_url": None if page <= 0 else f"https://127.0.0.1/api/index?page={page}",
                "to": None
            }
        }
    else:
        goods_query = goods_query.offset(page * 10).limit(10)
        goods_list = await goods_query

        goods = [GoodsTemp(g.id, g.title, g.price, g.stock, g.sales, f'upimg/goods_cover/{g.cover}.png',
                           g.description, 0, f'https://127.0.0.1/upimg/goods_cover/{g.cover}.png') for g in goods_list]

        goods_resp = {
            "current_page": page + 1,
            "data": [g.dict() for g in goods],
            "first_page_url": f"https://127.0.0.1/api/index?page=1",
            "from": page * 10 + 1,
            "next_page_url": f"https://127.0.0.1/api/index?page={page + 2}",
            "path": "https://127.0.0.1/api/index",
            "per_page": 10,
            "prev_page_url": f"https://127.0.0.1/api/index?page={page}" if page > 0 else None,
            "to": (page + 1) * 10
        }

    slides_query = await Slides.filter(status=1).order_by('seq').all()
    slides = [SlidesTemp(s.id, s.title, s.url, f'upimg/slides_img/{s.img}.png', s.status, s.seq,
                         transfer_time(f"{s.created_at}"), transfer_time(f"{s.updated_at}"),
                         f'https://127.0.0.1/upimg/slides_img/{s.img}.png') for s in
              slides_query]

    links = [
        {
            "id": 1,
            "name": "学习猿地",
            "url": "https://kuanrgen777.top",
            "img": "http://shopadmin.eduwork.cn/static/logo.434d10f5.png",
            "seq": 1,
            "status": 1,
            "created_at": "2022-09-03T08:40:31.000000Z",
            "updated_at": "2022-09-03T08:40:31.000000Z",
            "img_url": "http://shopadmin.eduwork.cn/static/logo.434d10f5.png"
        },
    ]

    return {
        "categories": categories_tree,
        "goods": goods_resp,
        "slides": slides,
        "links": links,
    }
