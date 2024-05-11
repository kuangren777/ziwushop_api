# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 10:31
# @Author  : KuangRen777
# @File    : main.py
# @Tags    :
"""
首先要运行redis-server
"""
from fastapi import FastAPI, Request
# 注册数据库
from tortoise.contrib.fastapi import register_tortoise
from settings import TORTOISE_ORM
# 跨域
from fastapi.middleware.cors import CORSMiddleware
# 静态文件
from fastapi.staticfiles import StaticFiles

# 注册路由
from api.authority import api_auth
from api.index import api_index
from api.goods import api_goods
from api.user import api_user
from api.carts import api_cart
from api.orders import api_orders
from api.city import api_city
from api.address import api_address
from api.admin.index import admin_index
from api.admin.users import admin_users
from api.admin.user import admin_user

# 启动网页服务
import uvicorn

# 创建一个 FastAPI 对象
app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     # allow_origins=origins,  # *：代表所有客户端
#     allow_origins=["*"],  # *：代表所有客户端
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
#     allow_headers=["*"],
# )

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有域名访问，生产环境中应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 注册数据库
register_tortoise(
    app=app,
    config=TORTOISE_ORM,
)

# 设置静态文件路由
app.mount("/upimg/avatars", StaticFiles(directory="upimg/avatars"), name="avatars")
app.mount("/upimg/goods_cover", StaticFiles(directory="upimg/goods_cover"), name="goods_cover")
app.mount("/upimg/goods_pics", StaticFiles(directory="upimg/goods_pics"), name="goods_pics")
app.mount("/upimg/comments_pics", StaticFiles(directory="upimg/comments_pics"), name="comments_pics")
app.mount("/upimg/slides_img", StaticFiles(directory="upimg/slides_img"), name="slides_img")

# 注册路由
app.include_router(api_auth, prefix='/api/auth', tags=['权限接口'])
app.include_router(api_index, prefix='/api/index', tags=['首页接口'])
app.include_router(api_goods, prefix='/api/goods', tags=['商品接口'])
app.include_router(api_user, prefix='/api/user', tags=['用户接口'])
app.include_router(api_cart, prefix='/api/carts', tags=['购物车接口'])
app.include_router(api_orders, prefix='/api/orders', tags=['订单接口'])
app.include_router(api_city, prefix='/api/city', tags=['省市查询接口'])
app.include_router(api_address, prefix='/api/address', tags=['地址接口'])
app.include_router(admin_index, prefix='/api/admin/index', tags=['地址接口'])
app.include_router(admin_users, prefix='/api/admin/users', tags=['地址接口'])
app.include_router(admin_user, prefix='/api/admin/user', tags=['地址接口'])


if __name__ == '__main__':
    uvicorn.run('main:app', host='127.0.0.1', port=8888, reload=True)
