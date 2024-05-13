# -*- coding: utf-8 -*-
# @Time    : 2024/5/12 0:31
# @Author  : KuangRen777
# @File    : category.py
# @Tags    :
from fastapi import APIRouter, Query, Depends, HTTPException, Path, Body
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, validator, constr, EmailStr, Field
from datetime import datetime
from models import Users
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.transactions import in_transaction

from utils import *

admin_category = APIRouter()


class CategoryModel(BaseModel):
    id: int
    pid: int
    name: str
    level: int
    status: int
    children: List['CategoryModel'] = []


CategoryModel.update_forward_refs()


class CategoryDetail(BaseModel):
    id: int
    pid: int = Field(0, description="Parent ID, 0 if it's a top-level category")
    name: str
    level: int
    status: int
    created_at: datetime
    updated_at: datetime


@admin_category.get("", response_model=List[CategoryModel])
async def get_category_list(
    type: Optional[str] = Query(None),
    token: str = Depends(oauth2_scheme)
):
    # Decode JWT token to authenticate and get user ID
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_email = payload.get("sub")
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch categories based on type
    if type == "all":
        categories = await Category.filter(level=1)
    else:
        categories = await Category.filter(level=1, status=0)

    # Recursive function to fetch children
    async def get_children(parent: Category) -> List[CategoryModel]:
        children = await Category.filter(pid=parent.id)
        return [CategoryModel(
            id=child.id,
            pid=child.pid,
            name=child.name,
            level=child.level,
            status=child.status,
            children=await get_children(child)
        ) for child in children]

    # Construct response
    result = []
    for category in categories:
        category_data = CategoryModel(
            id=category.id,
            pid=category.pid,
            name=category.name,
            level=category.level,
            status=category.status,
            children=await get_children(category)
        )
        result.append(category_data)

    return result


@admin_category.get("/{category_id}", response_model=CategoryDetail)
async def get_category_detail(
    category_id: int = Path(..., description="The ID of the category"),
    token: str = Depends(oauth2_scheme)
):
    # Decode JWT token to authenticate and get user ID
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch the category
    category = await Category.get_or_none(id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Return category details
    return CategoryDetail(
        id=category.id,
        pid=category.pid,
        name=category.name,
        level=category.level,
        status=category.status,
        created_at=category.created_at,
        updated_at=category.updated_at
    )


@admin_category.patch("/{category_id}/status", status_code=204)
async def toggle_category_status(
    category_id: int = Path(..., description="The ID of the category to toggle status"),
    token: str = Depends(oauth2_scheme)
):
    # Decode JWT token to authenticate and check user permissions
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise HTTPException(status_code=403, detail="Permission denied")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Retrieve the category from the database
    category = await Category.get_or_none(id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Toggle the status
    category.status = 1 if category.status == 0 else 0
    await category.save()

    # No content to return, only status code 204
    return


class CategoryCreate(BaseModel):
    name: str = Field(..., description="The name of the category")
    pid: Optional[int] = Field(None, description="Parent category ID")
    group: str = Field(default="menu", description="Group of the category")


@admin_category.post("", status_code=201)
async def create_category(
    category_data: CategoryCreate,
    token: str = Depends(oauth2_scheme)
):
    # Decode JWT token to authenticate and check user permissions
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise HTTPException(status_code=403, detail="Permission denied")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Validate category level limit (no more than two levels)
    if category_data.pid:
        parent_category = await Category.get_or_none(id=category_data.pid)
        if not parent_category:
            raise HTTPException(status_code=404, detail="Parent category not found")
        if parent_category.pid != 0:
            raise HTTPException(status_code=400, detail="不能超过二级分类")

    print(category_data.group)

    # Create the new category
    new_category = Category(
        name=category_data.name,
        pid=category_data.pid or 0,  # Ensure top-level if pid is None
        group=category_data.group
    )
    await new_category.save()

    return {"message": "Category created successfully", "id": new_category.id}


class CategoryUpdate(BaseModel):
    name: str = Field(..., description="The new name of the category")
    pid: Optional[int] = Field(None, description="New parent category ID")


@admin_category.put("/{category_id}", status_code=204)
async def update_category(
    category_id: int = Path(..., description="The ID of the category to update"),
    category_data: CategoryUpdate = Body(...),
    token: str = Depends(oauth2_scheme)
):
    # Decode JWT token to authenticate and check user permissions
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise HTTPException(status_code=403, detail="Permission denied")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch the category to be updated
    category = await Category.get_or_none(id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check if updating to a valid category level
    if category_data.pid is not None:
        parent_category = await Category.get_or_none(id=category_data.pid)
        if parent_category:
            if parent_category.pid != 0:
                raise HTTPException(status_code=400, detail="不能超过二级分类")

    # Update the category
    category.name = category_data.name
    category.pid = category_data.pid if category_data.pid is not None else 0  # Ensure top-level if pid is None
    await category.save()

    # No content to return, only status code 204
    return


class CategorySeqUpdate(BaseModel):
    seq: int = 1  # Default sequence number


@admin_category.patch("/{category_id}/seq", status_code=204)
async def update_category_sequence(
    category_id: int = Path(..., description="The ID of the category to update sequence"),
    seq_data: CategorySeqUpdate = Body(...),
    token: str = Depends(oauth2_scheme)
):
    # Decode JWT token to authenticate and check user permissions
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise HTTPException(status_code=403, detail="Permission denied")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch the category to be updated
    category = await Category.get_or_none(id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Update the sequence number
    category.seq = seq_data.seq
    await category.save()

    # No content to return, only status code 204
    return
