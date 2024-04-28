# -*- coding: utf-8 -*-
# @Time    : 2024/4/29 0:20
# @Author  : KuangRen777
# @File    : city.py
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

api_city = APIRouter()

