# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 0:11
# @Author  : KuangRen777
# @File    : models.py
# @Tags    :
from tortoise.models import Model
from tortoise import fields


class Users(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True)
    password = fields.CharField(max_length=255)
    phone = fields.CharField(max_length=255, null=True)
    avatar = fields.CharField(max_length=255, null=True)
    is_locked = fields.IntField(default=0, null=True)
    password_verified = fields.DatetimeField(null=True)
    remember_token = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class Category(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    pid = fields.IntField(default=0, null=True)
    status = fields.IntField(default=1, null=True)
    level = fields.IntField(default=1, null=True)
    group = fields.CharField(max_length=255, default='goods', null=True)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class Goods(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.Users', related_name='goods')
    category = fields.ForeignKeyField('models.Category', related_name='goods')
    title = fields.CharField(max_length=255)
    description = fields.CharField(max_length=255)
    price = fields.IntField()
    stock = fields.IntField()
    cover = fields.CharField(max_length=255)
    pics = fields.JSONField()  # Assuming JSON storage is supported
    details = fields.TextField()
    sales = fields.IntField(default=0, null=True)
    is_on = fields.IntField(default=0, null=True)
    is_recommend = fields.IntField(default=0, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    def __str__(self):
        return self.title


class Comments(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.Users', related_name='reviews')
    order = fields.ForeignKeyField('models.Orders', related_name='reviews')
    goods = fields.ForeignKeyField('models.Goods', related_name='reviews')
    content = fields.CharField(max_length=255)
    rate = fields.IntField(default=1, null=True)
    star = fields.IntField(default=5, null=True)
    reply = fields.CharField(max_length=255, null=True)
    pics = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.content} by user {self.user}"


class Orders(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.Users', related_name='orders')
    order_no = fields.CharField(max_length=255)
    amount = fields.IntField()
    address = fields.ForeignKeyField('models.Address', related_name='orders')
    status = fields.IntField(default=1, null=True)
    express_type = fields.CharField(max_length=255, null=True)
    express_no = fields.CharField(max_length=255, null=True)
    pay_time = fields.DatetimeField(null=True)
    pay_type = fields.CharField(max_length=255, null=True)
    trade_no = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    def __str__(self):
        return self.order_no


class OrderDetails(Model):
    id = fields.IntField(pk=True)
    order = fields.ForeignKeyField('models.Orders', related_name='order_details')
    goods = fields.ForeignKeyField('models.Goods', related_name='order_details')
    price = fields.IntField()
    num = fields.IntField()
    created_at = fields.DatetimeField(auto_now_add=True, null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.num} x {self.goods} at {self.price} each"


class Slides(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    img = fields.CharField(max_length=255)
    url = fields.CharField(max_length=255, null=True)
    status = fields.IntField(default=0, null=True)
    seq = fields.IntField(default=1, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    def __str__(self):
        return self.title


class Cart(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.Users', related_name='cart')
    goods = fields.ForeignKeyField('models.Goods', related_name='cart')
    num = fields.IntField(default=1, null=True)
    is_checked = fields.IntField(default=1, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    def __str__(self):
        return f"Cart Item: {self.goods} x {self.num} for user {self.user}"


class Address(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.Users', related_name='address')
    name = fields.CharField(max_length=255)
    province = fields.CharField(max_length=255)
    city = fields.CharField(max_length=255)
    county = fields.CharField(max_length=255)
    address = fields.CharField(max_length=255)
    phone = fields.CharField(max_length=255)
    is_default = fields.IntField(default=0, null=True)
    created_at = fields.DatetimeField(auto_now_add=True, null=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.address}"