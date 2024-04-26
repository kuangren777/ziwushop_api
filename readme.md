# [一小时学会FastApi](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=一小时学会fastapi)

一个用于构建 API 的现代、快速（高性能）的web框架

快速构建api，异步框架（django和flask旧版本不是异步框架）

易于使用和学习

自动生成的交互式文档

![image-20240408160808350](https://kuangren-220811.oss-cn-shanghai.aliyuncs.com/Markdown_IMG/1.png)

基于：Python3.10

工具：Pycharm

目的：一小时学会FastApi

### [1、安装fastapi（python web框架）和uvicorn（类似于uwsgi的web服务器）](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_1、安装fastapi（python-web框架）和uvicorn（类似于uwsgi的web服务器）)

pip install fastapi -i https://pypi.tuna.tsinghua.edu.cn/simple

pip install uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple

### [2、前后端分离和前后端不分离（概念）](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_2、前后端分离和前后端不分离（概念）)

前后端不分离

![image-20240408161313089](https://kuangren-220811.oss-cn-shanghai.aliyuncs.com/Markdown_IMG/2.png)

![image-20240408161543816](https://kuangren-220811.oss-cn-shanghai.aliyuncs.com/Markdown_IMG/3.png)

### [3、restful风格的api](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_3、restful风格的api)

| 请求方法 | 请求地址 | 后端操作        |
| -------- | -------- | --------------- |
| POST     | /book/   | 增加图书        |
| GET      | /book/   | 获取所有图书    |
| GET      | /book/1  | 获取id为1的图书 |
| PUT      | /book/1  | 修改id为1的图书 |
| DELETE   | /book/1  | 删除id为1的图书 |

### [4、快速创建一个fastapi项目](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_4、快速创建一个fastapi项目)

1fastapi.py

```
# 从fastapi导出FastAPI类
from fastapi import FastAPI
# 导web服务器
import uvicorn

# 实例化对象
app = FastAPI()

# 路由
@app.get("/")
async def root():
    return {"message": "Hello B站程序员科科"}

# 启动项目
if __name__ == '__main__':
    uvicorn.run("1fastapi:app", host="127.0.0.1", port=8080, reload=True)Copy to clipboardErrorCopied
```

![image-20240408162313029](https://kuangren-220811.oss-cn-shanghai.aliyuncs.com/Markdown_IMG/4.png)

### [5、fastapi接口文档](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_5、fastapi接口文档)

```
# 增删改查

# @app.get()
# @app.post()
# @app.put()
# @app.delete()

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello B站程序员科科"}

@app.get("/get")
def get_test():
    return {"method": "get方法"}


@app.post("/post")
def post_test():
    return {"method": "post方法"}


@app.put("/put")
def put_test():
    return {"method": "put方法"}

@app.delete("/delete")
def delete_test():
    return {"method": "delete方法"}

if __name__ == '__main__':
    uvicorn.run("1fastapi:app", host="127.0.0.1", port=8080, reload=True)Copy to clipboardErrorCopied
```

![image-20240408162313029](https://kuangren-220811.oss-cn-shanghai.aliyuncs.com/Markdown_IMG/5.png)

### [6、路由分发（类似django中的include）](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_6、路由分发（类似django中的include）)

在1fastapi同级目录创建一个api目录，同时新建三个文件，文件名book，cbs，zz

![image-20240408162916150](https://kuangren-220811.oss-cn-shanghai.aliyuncs.com/Markdown_IMG/6.png)

1fastapi里添加如下两行

```
from api.book import api_book
from api.cbs import api_cbs
from api.zz import api_zz

app.include_router(api_book, prefix="/book", tags=["图书接口", ])
app.include_router(api_cbs, prefix="/cbs", tags=["出版社接口", ])
app.include_router(api_zz, prefix="/zz", tags=["作者接口", ])Copy to clipboardErrorCopied
```

图书、出版社、作者依次添加增删改查接口

```
# 类似于django里的 path
from fastapi import APIRouter
# 生成路由对象
api_book = APIRouter()

@api_book.get("/get")
async def get_test():
    return {"method": "get方法"}


@api_book.post("/post")
async def post_test():
    return {"method": "post方法"}


@api_book.put("/put")
async def put_test():
    return {"method": "put方法"}

@api_book.delete("/delete")
async def delete_test():
    return {"method": "delete方法"}Copy to clipboardErrorCopied
```

![image-20240408163701044](https://kuangren-220811.oss-cn-shanghai.aliyuncs.com/Markdown_IMG/7.png)

### [7、request对象](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_7、request对象)

```
# 注意：这里post请求一定要加上 await 因为上传默认是一种非常繁忙操作，所以request.json()或者request.form()都会发送异步请求，所以要用 await 接收


# 通过request.json()得到post请求结果
# 注册接口
@app.post("/test_post")
async def register(request: Request):
    json_data = await request.json()
    print(json_data)

# 通过request.query_params()得到get请求结果
# 注册接口
@app.get("/test_get")
async def register(request: Request):
    json_data = request.query_params
    print(json_data)Copy to clipboardErrorCopied
```

### [8、静态文件static](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_8、静态文件static)

```python
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 设置静态文件路由
app.mount("/upimg", StaticFiles(directory="upimg"), name="upimg")Copy to clipboardErrorCopied
```

表示如果访问的路由是 127.0.0.1:8000/upimg 时，fastapi 会把所有的请求发送给当前目录下 upimg 找到这个目录下所有静态文件

127.0.0.1:8000/upimg/1.jpg

### [9、jinjia2](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_9、jinjia2)

pip3.10 install Jinja2 -i https://pypi.tuna.tsinghua.edu.cn/simple

```
from fastapi.templating import Jinja2Templates

# 设置 jinjia2 路径
templates = Jinja2Templates(directory="templates")

@app.get('/jinjia2tem')
async def jinjia2tem(request: Request):
    return templates.TemplateResponse('index.html',{'request': request, "books": ["平凡的世界", "活着", "兄弟", "文城"]})


Copy to clipboardErrorCopied
```

index.html

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Title</title>
</head>
<body>

<p>{{ books.0 }}</p>
<p>{{ books.1 }}</p>


</body>
</html>Copy to clipboardErrorCopied
```

### [10、tortoise_orm（orm操作mysql组件）](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_10、tortoise_orm（orm操作mysql组件）)

pip install tortoise-orm -i https://pypi.tuna.tsinghua.edu.cn/simple

1fastapi.py

```
from tortoise.contrib.fastapi import register_tortoise
from settings import TORTOISE_ORM

register_tortoise(
    app=app,
    config=TORTOISE_ORM,
)Copy to clipboardErrorCopied
```

settings.py

```
TORTOISE_ORM = {
    'connections': {
        'default': {
            # 'engine': 'tortoise.backends.asyncpg',  PostgreSQL
            'engine': 'tortoise.backends.mysql',  # MySQL or Mariadb
            'credentials': {
                'host': '127.0.0.1',
                'port': '3306',
                'user': 'root',
                'password': '123456',
                'database': 'fastapi',
                'minsize': 1,
                'maxsize': 5,
                "echo": True
            }
        },
    },
    'apps': {
        'models': {
            'models': ['models', "aerich.models"],
            'default_connection': 'default',

        }
    },
    'use_tz': False,
    'timezone': 'Asia/Shanghai'
}Copy to clipboardErrorCopied
```

### [11、新建models模型](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_11、新建models模型)

```
from tortoise.models import Model
from tortoise import fields

class Publish(Model):
    name = fields.CharField(max_length=32, verbose_name="出版社名称")
    email = fields.CharField(max_length=32,verbose_name="出版社邮箱")

class Author(Model):
    name = fields.CharField(max_length=32, verbose_name="作者")
    age = fields.IntField(verbose_name="年龄")

class Book(Model):
    title = fields.CharField(max_length=32, verbose_name="书籍名称")
    price = fields.IntField(verbose_name="价格")
    # pub_date = models.DateField(verbose_name="出版日期")
    img_url = fields.CharField(max_length=255, null=True,blank=True,verbose_name="")
    bread = fields.IntField(verbose_name="阅读量")
    bcomment = fields.IntField(verbose_name="评论量")
    publishs = fields.ForeignKeyField('models.Publish', related_name='books')
    authors = fields.ManyToManyField('models.Author', related_name='books', description="作者")Copy to clipboardErrorCopied
```

ModuleNotFoundError: No module named 'aiomysql'

pip install aiomysql -i https://pypi.tuna.tsinghua.edu.cn/simple

### [12、aerich是一种ORM迁移工具，需要结合tortoise异步orm框架使用。安装aerich](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_12、aerich是一种orm迁移工具，需要结合tortoise异步orm框架使用。安装aerich)

pip install aerich -i https://pypi.tuna.tsinghua.edu.cn/simple

aerich init -t settings.TORTOISE_ORM

aerich init-db

aerich migrate 修改迁移

aerich upgrade 真正迁移

aerich downgrade 回退迁移

### [13、出版社增删改查](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_13、出版社增删改查)

```
@api_cbs.get("/")
async def getAllPublish():
    # 这是 list 对象
    # publish_obj = await Publish.all()
    # 这是 queryset 对象
    # publish_obj = Publish.all()

    # filter
    # users = await User.filter(name=name).all()

    # get
    # user = await User.get(id=user_id)

    # order_by
    # users = await User.all().order_by('name')

    # limit
    # users = await User.all().limit(limit)


    #print(publish_obj)
    #return {'code': 200, 'data': publish_obj}

# 增加
@api_cbs.post("/")
async def addPublish(request: Request):
    # 拿到前端传递的图书
    json_data = await request.json()
    name = json_data["name"]
    email = json_data["email"]
    # 方式2
    publish = await Publish.create(name=name,email=email)
    return {'code': 200, 'message': "增加成功", 'data': publish}

# 查看一个
@api_cbs.get("/{Publish_id}")
async def update_Publish(Publish_id: int):
    publish = await Publish.get(id=Publish_id).values("id","name","email")
    return publish

# 修改一个
@api_cbs.put("/{Publish_id}")
async def update_Publish(Publish_id: int,request: Request):
    # 拿到前端传递的图书
    json_data = await request.json()
    name = json_data["name"]
    email = json_data["email"]
    await Publish.filter(id=Publish_id).update(name=name,email=email)
    return {'code': 200, 'message': "修改成功"}

# 删除一个
@api_cbs.delete("/{Publish_id}")
async def delete_Publish(Publish_id: int):
    deleted_count = await Publish.filter(id=Publish_id).delete()
    if not deleted_count:
        return {'code': 500, 'message': "删除失败"}
    return {'code': 200, 'message': "删除成功"}
Copy to clipboardErrorCopied
```

### [13、跨域问题解决](https://docs.ake999.com/#/ProjectDocs/fastapi/onehour/一小时学会FastApi?id=_13、跨域问题解决)

```
from fastapi.middleware.cors import CORSMiddleware

# origins = [
#     "http://localhost:63342"
# ]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,  # *：代表所有客户端
    allow_origins=["*"],  # *：代表所有客户端
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
```