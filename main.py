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