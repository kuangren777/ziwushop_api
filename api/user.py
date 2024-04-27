# -*- coding: utf-8 -*-
# @Time    : 2024/4/27 14:16
# @Author  : KuangRen777
# @File    : user.py
# @Tags    :
from fastapi import APIRouter, Request, HTTPException, Depends, status, UploadFile, File
from models import Goods, Category, Comments, Users, OrderDetails, Orders
from tortoise.functions import Count
from tortoise.query_utils import Prefetch
import json
from pydantic import BaseModel, Field
import shutil
import os

from utils import *

api_user = APIRouter()


class UserResponseModel(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None = None
    avatar: str | None = None
    avatar_url: str = Field(default=None)
    is_locked: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: transfer_time_datetime
        }


class UpdateUserModel(BaseModel):
    name: str


@api_user.get("/user", response_model=UserResponseModel)
async def get_user_details(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await Users.get(email=user_email)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user


@api_user.put("/user", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_details(user_data: UpdateUserModel, token: str = Depends(oauth2_scheme)):
    # Decode the JWT token to authenticate and get the user id
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch the user from the database
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update the user's information
    user.name = user_data.name
    await user.save()

    return {}


@api_user.post("/user/avatar_oss", status_code=status.HTTP_204_NO_CONTENT)
async def update_avatar(avatar: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    # Decode JWT to authenticate and get user ID
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        user = await Users.get(email=user_email)

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        else:
            user_id = user.id

    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure avatar is an image
    if not avatar.content_type.startswith('image/'):
        raise HTTPException(status_code=422, detail={
            "message": "The given data was invalid.",
            "errors": {"avatar": ["Invalid file type"]}
        })

    # Upload to OSS
    file_content = await avatar.read()
    object_name = f'avatars/{user_id}/{avatar.filename}'
    result = bucket.put_object(object_name, file_content)
    if result.status != 200:
        raise HTTPException(status_code=500, detail="Failed to upload avatar")

    # Update user's avatar URL
    avatar_url = f'https://{BUCKET_NAME}.{ENDPOINT}/{object_name}'
    user.avatar = avatar_url
    await user.save()

    return {}


@api_user.post("/user/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def update_avatar(avatar: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    # Decode the JWT to authenticate and get user ID
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_email = payload.get("sub")
    user = await Users.get(email=user_email)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user_id = user.id

    # Ensure avatar is an image
    if not avatar.content_type.startswith('image/'):
        raise HTTPException(status_code=422, detail={
            "message": "The given data was invalid.",
            "errors": {"avatar": ["Invalid file type"]}
        })

    random_string = generate_random_string(10)
    timestamp = int(time.time())
    unique_filename = f"{timestamp}_{random_string}"

    # Define path for saving the avatar
    file_path = f"./upimg/avatars/{user_id}"
    os.makedirs(file_path, exist_ok=True)

    # Get the original file extension
    file_extension = avatar.filename.split(".")[-1]
    # Generate new file name with random string and original file extension
    new_file_name = f"{unique_filename}.{file_extension}"
    file_location = os.path.join(file_path, new_file_name)

    # Save the uploaded file
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(avatar.file, buffer)

    # Update user's avatar URL
    user.avatar = f"{user_id}/{unique_filename}"
    await user.save()

    return {}
