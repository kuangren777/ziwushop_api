# -*- coding: utf-8 -*-
# @Time    : 2024/4/29 0:45
# @Author  : KuangRen777
# @File    : address.py
# @Tags    :
from fastapi import APIRouter, Request, HTTPException, Depends, status, UploadFile, File, Path, Query, Body
from models import Goods, Category, Comments, Users, OrderDetails, Orders, Cart, Address
from tortoise.functions import Count, Sum
from tortoise.query_utils import Prefetch
import json
from pydantic import BaseModel, Field, HttpUrl, conint
import shutil
import os
from typing import List, Optional
from tortoise.transactions import in_transaction
import re

from utils import *

api_address = APIRouter()


class AddressCreate(BaseModel):
    name: str = Field(..., example="John Doe")
    address: str = Field(..., example="123 Main St")
    phone: str = Field(..., example="1234567890")
    province: str = Field(..., example="California")
    city: str = Field(..., example="Los Angeles")
    county: str = Field(..., example="Los Angeles County")
    is_default: int = Field(0, example=1)  # Default to 0 if not provided


class AddressList(BaseModel):
    id: int
    name: str
    province: str
    city: str
    county: str
    address: str
    phone: str
    is_default: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AddressDetail(BaseModel):
    id: int
    name: str
    province: str
    city: str
    county: str
    address: str
    phone: str
    is_default: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AddressUpdate(BaseModel):
    name: str = Field(..., example="John Doe")
    address: str = Field(..., example="123 Main St")
    phone: str = Field(..., example="1234567890")
    province: str = Field(..., example="California")
    city: str = Field(..., example="Los Angeles")
    county: str = Field(..., example="LA County")
    is_default: int = Field(default=0, example=1)


@api_address.post("", status_code=status.HTTP_201_CREATED)
async def add_address(address_data: AddressCreate, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure the user exists
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user_id = user.id

    # If is_default is set to 1, reset all other addresses' default status
    if address_data.is_default:
        await Address.filter(user_id=user.id, is_default=1).update(is_default=0)

    # Create the new address
    address = await Address.create(
        user_id=user.id,
        name=address_data.name,
        address=address_data.address,
        phone=address_data.phone,
        province=address_data.province,
        city=address_data.city,
        county=address_data.county,
        is_default=address_data.is_default
    )
    return {"message": "Address created successfully", "address_id": address.id}


@api_address.get("", response_model=List[AddressList])
async def list_addresses(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure the user exists
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user_id = user.id

    addresses = await Address.filter(user_id=user.id).all()
    if not addresses:
        return []
    return addresses


@api_address.get("/{address_id}", response_model=AddressDetail)
async def get_address_details(address_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure the user exists
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user_id = user.id

    address = await Address.get_or_none(id=address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    address_user = await address.user

    if address_user.id != user.id:
        raise HTTPException(status_code=400, detail="只能查看自己的地址")

    return address


@api_address.put("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_address(
        address_id: int,
        address_data: AddressUpdate,
        token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure the user exists
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user_id = user.id

    # Fetch the existing address to update
    address = await Address.get_or_none(id=address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    address_user = await address.user

    if address_user.id != user.id:
        raise HTTPException(status_code=403, detail="Permission denied to update this address")

    if address_data.name == "" or address_data.address == "" or address_data.phone == "" or address_data.province == "" or address_data.city == "" or address_data.county == "":
        raise HTTPException(status_code=422, detail="Address data cannot be empty")

    # If setting this address as default, reset defaults for other addresses
    if address_data.is_default:
        await Address.filter(user_id=user.id, is_default=1).update(is_default=0)

    # Update address
    update_data = address_data.dict(exclude_unset=True)
    await address.update_from_dict(update_data).save()

    return {"message": "Address updated successfully"}


@api_address.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
        address_id: int,
        token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure the user exists
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user_id = user.id

    # Retrieve the address to ensure it exists and belongs to the current user
    address = await Address.get_or_none(id=address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    address_user = await address.user

    if address_user.id != user.id:
        raise HTTPException(status_code=403, detail="Permission denied to delete this address")

    # Delete the address
    await address.delete()
    return {"message": "Address deleted successfully"}


@api_address.patch("/{address_id}/default", status_code=status.HTTP_204_NO_CONTENT)
async def set_default_address(
    address_id: int,
        token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ensure the user exists
    user = await Users.get_or_none(email=user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        user_id = user.id

    # Retrieve the address to ensure it exists and belongs to the current user
    address = await Address.get_or_none(id=address_id)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    address_user = await address.user
    if address_user.id != user.id:
        raise HTTPException(status_code=403, detail="Permission denied to modify this address")

    # Reset the default status of all other addresses
    await Address.filter(user_id=user.id).update(is_default=0)

    # Set the selected address as the default
    address.is_default = 1
    await address.save()

    return {"message": "Default address set successfully"}