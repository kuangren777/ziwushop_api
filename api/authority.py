# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 11:07
# @Author  : KuangRen777
# @File    : authority.py
# @Tags    :
from fastapi import APIRouter, HTTPException, status, Body, Request
from models import Users
from tortoise.contrib.fastapi import HTTPNotFoundError
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
import jwt

from datetime import datetime, timedelta
from settings import *
from utils import *

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer


# 定义数据模型
class UserRegistrationModel(BaseModel):
    name: str
    email: EmailStr
    password: str
    password_confirmation: str
    avatar: str = None


class LoginModel(BaseModel):
    email: EmailStr
    password: str


# 密码加密配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 路由
api_auth = APIRouter()

# JWT验证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@api_auth.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegistrationModel):
    if user.name is None or user.name == "":
        return HTTPException(status_code=422, detail={"message": "The given data was invalid.",
                                                      "errors": {"name": ["请输入用户名"]}, "status_code": 422})

    if user.password != user.password_confirmation:
        return HTTPException(status_code=422, detail={"message": "The given data was invalid.",
                                                      "errors": {"password_confirmation": ["密码与确认密码不一致"]},
                                                      "status_code": 422})

    # 检查电子邮件是否已经存在
    if await Users.filter(email=user.email).exists():
        return HTTPException(status_code=422, detail={"message": "The given data was invalid.",
                                                      "errors": {"email": ["电子邮件已被注册"]}, "status_code": 422})

    # 密码加密处理
    hashed_password = pwd_context.hash(user.password)

    # 创建新用户
    user_obj = await Users.create(
        name=user.name,
        email=user.email,
        password=hashed_password,
        avatar=user.avatar
    )

    # 创建 JWT token
    token_data = {"sub": user_obj.email, "id": str(user_obj.id)}
    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")

    return {"token": token}


@api_auth.post("/auth/login")
async def login(user_credentials: LoginModel):
    # 根据邮箱查找用户
    user = await Users.get_or_none(email=user_credentials.email)
    if not user:
        return HTTPException(status_code=404, detail="邮箱未注册")

    # 验证密码
    if not pwd_context.verify(user_credentials.password, user.password):
        return HTTPException(status_code=401, detail="密码错误")

    # 创建JWT token
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": user.email,
        "exp": expire
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    # 返回token信息
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 返回秒数
    }


@api_auth.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, token: str = Depends(oauth2_scheme)):
    print(f"Authorization header: {request.headers.get('Authorization')}")
    # 假设有一个函数add_token_to_blacklist处理令牌黑名单
    success = add_token_to_blacklist(token)
    if not success:
        raise HTTPException(status_code=400, detail="无法退出登录")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_auth.post("/auth/refresh")
async def refresh_token(token: str = Depends(oauth2_scheme)):
    if redis_client.get(token):
        raise HTTPException(status_code=401, detail="Token is blacklisted")

    # 验证并解析旧的token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate token")

    success = add_token_to_blacklist(token)
    if not success:
        raise HTTPException(status_code=400, detail="无法刷新令牌")

    # 创建新的token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
