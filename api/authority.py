# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 11:07
# @Author  : KuangRen777
# @File    : authority.py
# @Tags    :
import os
import uuid

from fastapi import APIRouter, HTTPException, status, Body, Request, UploadFile, File
from fastapi.responses import JSONResponse

from models import Users
from tortoise.contrib.fastapi import HTTPNotFoundError
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
import jwt

from datetime import datetime, timedelta
from utils import *
from PASSWORD import *

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from email_sender import send_verification_email


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


class PasswordUpdateModel(BaseModel):
    old_password: str = Field(..., description="旧密码")
    password: str = Field(..., description="新密码")
    password_confirmation: str = Field(..., description="确认新密码")


class EmailRequestModel(BaseModel):
    email: EmailStr


class EmailUpdateRequest(BaseModel):
    email: EmailStr
    code: str


# 路由
api_auth = APIRouter()


@api_auth.post("/register", status_code=status.HTTP_201_CREATED)
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


@api_auth.post("/login")
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


@api_auth.options("/login")
async def login_option():
    return {
        "GET": "This endpoint supports GET requests", "POST": "This endpoint supports POST requests"
    }


@api_auth.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, token: str = Depends(oauth2_scheme)):
    print(f"Authorization header: {request.headers.get('Authorization')}")
    # 假设有一个函数add_token_to_blacklist处理令牌黑名单
    success = add_token_to_blacklist(token)
    if not success:
        raise HTTPException(status_code=400, detail="无法退出登录")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_auth.post("/refresh")
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
    except jwt.PyJWTError:
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


@api_auth.post("/password/update", status_code=status.HTTP_204_NO_CONTENT)
async def update_password(password_update: PasswordUpdateModel, token: str = Depends(oauth2_scheme)):
    if redis_client.get(token):
        raise HTTPException(status_code=401, detail="Token is blacklisted")

    # 解码JWT token并获取用户信息
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        user = await Users.get(email=user_email)
    except jwt.PyJWTError:
        raise credentials_exception

    # 验证旧密码
    if not pwd_context.verify(password_update.old_password, user.password):
        raise HTTPException(status_code=422, detail={
            "message": "The given data was invalid.",
            "errors": {"old_password": ["旧密码不正确"]},
            "status_code": 422
        })

    # 验证新密码和确认密码是否匹配
    if password_update.password != password_update.password_confirmation:
        raise HTTPException(status_code=422, detail={
            "message": "The given data was invalid.",
            "errors": {"password_confirmation": ["密码与确认密码不一致"]},
            "status_code": 422
        })

    # 更新密码
    user.password = pwd_context.hash(password_update.password)
    await user.save()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api_auth.post("/email/code", status_code=status.HTTP_204_NO_CONTENT)
async def get_email_code(email_data: EmailRequestModel, token: str = Depends(oauth2_scheme)):
    # 解码JWT token并获取用户信息
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        user = await Users.get(email=user_email)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 验证新邮箱是否已被使用
    if await Users.filter(email=email_data.email).exists():
        raise HTTPException(status_code=422, detail={
            "message": "The given data was invalid.",
            "errors": {"email": ["邮箱已被注册。"]},
            "status_code": 422
        })

    # 生成验证码
    verification_code = generate_verification_code()

    # 保存验证码
    save_verification_code(user_email, verification_code)

    send_verification_email(email_data.email, verification_code)

    return {}


@api_auth.patch("/email/update", status_code=status.HTTP_204_NO_CONTENT)
async def update_email(request: EmailUpdateRequest, token: str = Depends(oauth2_scheme)):
    # Decode JWT token to get user Email.
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await Users.get(email=user_email)

    # Validate the code from Redis
    redis_key = f"email_code:{user.email}"
    stored_code = redis_client.get(redis_key)
    if not stored_code or stored_code != request.code:
        raise HTTPException(status_code=422, detail={
            "message": "The given data was invalid.",
            "errors": {"code": ["验证码不正确或已过期"]},
            "status_code": 422
        })

    # Check if email is already in use
    if await Users.filter(email=request.email).exists():
        raise HTTPException(status_code=422, detail={
            "message": "The given data was invalid.",
            "errors": {"email": ["邮箱已被注册。"]},
            "status_code": 422
        })

    # Update the user's email
    user.email = request.email
    await user.save()

    # Clean up the code from Redis after successful update
    redis_client.delete(redis_key)

    return {}


@api_auth.post("/upload")
async def upload_cover_file(file: UploadFile = File(...)):
    # 为文件生成一个唯一的文件名
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join('upimg/goods_cover/', unique_filename)

    # 将上传的文件保存到服务器
    with open(file_path, "wb") as buffer:
        while content := await file.read(1024):  # 读取文件内容并写入
            buffer.write(content)

    # 构造文件访问URL
    file_url = f"http://127.0.0.1:8888/upimg/goods_cover/{unique_filename}"

    return JSONResponse(status_code=200, content={"url": file_url})
