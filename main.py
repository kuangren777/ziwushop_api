# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 10:31
# @Author  : KuangRen777
# @File    : main.py
# @Tags    :
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

# 启动网页服务
import uvicorn

# 创建一个 FastAPI 对象
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,  # *：代表所有客户端
    allow_origins=["*"],  # *：代表所有客户端
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# 注册数据库
register_tortoise(
    app=app,
    config=TORTOISE_ORM,
)

# 设置静态文件路由
app.mount("/upimg/avatar", StaticFiles(directory="upimg/avatar"), name="avatar")
app.mount("/upimg/goods_cover", StaticFiles(directory="upimg/goods_cover"), name="goods_cover")
app.mount("/upimg/goods_pics", StaticFiles(directory="upimg/goods_pics"), name="goods_pics")
app.mount("/upimg/comments_pics", StaticFiles(directory="upimg/comments_pics"), name="comments_pics")
app.mount("/upimg/slides_img", StaticFiles(directory="upimg/slides_img"), name="slides_img")

# 注册路由
app.include_router(api_auth, prefix='/api', tags=['图书接口'])
app.include_router(api_index, prefix='/api', tags=['作者接口'])
app.include_router(api_goods, prefix='/api', tags=['商品接口'])


if __name__ == '__main__':
    uvicorn.run('main:app', host='127.0.0.1', port=8888, reload=True)