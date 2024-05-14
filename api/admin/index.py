# -*- coding: utf-8 -*-
# @Time    : 2024/5/11 18:14
# @Author  : KuangRen777
# @File    : index.py
# @Tags    :

from fastapi import APIRouter, HTTPException
from models import Users, Goods, Orders
from tortoise.functions import Count, Sum
from datetime import datetime, timedelta

admin_index = APIRouter()


@admin_index.get("", tags=["首页统计"])
async def index_stats():
    try:
        # 日期设置
        today_start = datetime.combine(datetime.today(), datetime.min.time())
        today_end = datetime.combine(datetime.today(), datetime.max.time())
        yesterday_start = today_start - timedelta(days=1)
        yesterday_end = today_end - timedelta(days=1)

        # 用户统计
        users_count = await Users.all().count()
        today_users_count = await Users.filter(created_at__gte=today_start, created_at__lte=today_end).count()
        yesterday_users_count = await Users.filter(created_at__gte=yesterday_start, created_at__lte=yesterday_end).count()

        # 用户更新统计
        today_users_updated_count = await Users.filter(updated_at__gte=today_start, updated_at__lte=today_end).count()
        yesterday_users_updated_count = await Users.filter(updated_at__gte=yesterday_start,
                                                           updated_at__lte=yesterday_end).count()

        # 商品统计
        goods_count = await Goods.all().count()
        on_goods_count = await Goods.filter(is_on=1).count()
        off_goods_count = await Goods.filter(is_on=0).count()
        stock_null_goods_count = await Goods.filter(stock=0).count()
        recommend_goods_count = await Goods.filter(is_recommend=1).count()

        # 订单统计
        order_count = await Orders.all().count()
        today_order_count = await Orders.filter(created_at__gte=today_start, created_at__lte=today_end).count()
        yesterday_order_count = await Orders.filter(created_at__gte=yesterday_start, created_at__lte=yesterday_end).count()

        today_order_price = await get_total_price(Orders.filter(created_at__gte=today_start, created_at__lte=today_end))
        yesterday_order_price = await get_total_price(Orders.filter(created_at__gte=yesterday_start, created_at__lte=yesterday_end))
        total_order_price = await get_total_price(Orders.all())

        return {
            "users_count": users_count,
            "goods_count": goods_count,
            "order_count": order_count,
            "goods_info": {
                "on_nums": on_goods_count,
                "un_nums": off_goods_count,
                "stock_null": stock_null_goods_count,
                "recommend_nums": recommend_goods_count
            },
            "users_info": {
                "today_nums": today_users_updated_count,
                "yesterday_nums": yesterday_users_updated_count,
                "total_nums": users_count
            },
            "order_info": {
                "today": {
                    "nums": today_order_count,
                    "total_price": today_order_price
                },
                "yesterday": {
                    "nums": yesterday_order_count,
                    "total_price": yesterday_order_price
                },
                "total": {
                    "nums": order_count,
                    "total_price": total_order_price
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_total_price(query):
    result = await query.annotate(total=Sum('amount')).values_list('total', flat=True)
    return result[0] if result else 0

