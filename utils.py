# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 16:50
# @Author  : KuangRen777
# @File    : utils.py
# @Tags    :
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer

import jwt
import time
# redis
import redis
from PASSWORD import *

import secrets
from passlib.context import CryptContext

# 配置Redis连接
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)  # decode_responses确保返回的数据是字符串

# 密码加密配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def generate_verification_code(length=6):
    # 生成一个六位数的验证码
    return ''.join(secrets.choice('0123456789') for i in range(length))


def save_verification_code(email, code):
    # 保存验证码到Redis，有效期为600秒（10分钟）
    redis_client.setex(f"email_code:{email}", 600, code)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def add_token_to_blacklist(token: str) -> bool:
    try:
        # 解码JWT令牌以获取过期时间
        payload = jwt.decode(token, options={"verify_signature": False})  # 关闭签名验证仅用于获取声明
        exp = payload.get('exp')

        # 计算令牌的剩余有效时间
        current_time = time.time()
        ttl = exp - current_time  # Time to live

        if ttl > 0:
            # 将令牌添加到Redis黑名单
            redis_client.setex(token, int(ttl), 'blacklisted')
        return True
    except Exception as e:
        print(f"Error adding token to blacklist: {e}")
        return False


def transfer_time(input_time_str):
    # 将输入时间字符串解析为 datetime 对象
    input_time = datetime.fromisoformat(input_time_str)

    # 将 datetime 对象格式化为所需格式的时间字符串
    output_time_str = input_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return output_time_str


def build_tree(elements, parent_id=0):
    branch = []
    for element in elements:
        if element.pid == parent_id:
            children = build_tree(elements, element.id)
            node = {
                'id': element.id,
                'pid': element.pid,
                'name': element.name,
                'level': element.level,
                'status': element.status,
                'seq': 1
            }
            if children:  # 只有当有子分类时才添加 `children` 字段
                node['children'] = children
            branch.append(node)
    return branch

