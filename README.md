# 反向代理模块文档

## 概述

一个用于Flask应用中的反向代理模块，它是一个反向代理实现，主要用于代理API接口，修改请求或者和响应数据。

## 功能

- 多种集成方法: Upstream 类可以通过装饰器、直接方法调用、URL 规则或蓝图集成到 Flask 应用中。
- 灵活的请求处理: 支持所有常见的 HTTP 方法，包括 GET、POST、PUT、DELETE、PATCH、OPTIONS 和 HEAD。
- 请求和响应自定义: 在请求发送到上游服务器之前和响应返回给客户端之前修改请求和响应。
- 全局代理: 轻松设置 Flask 应用中所有路由的全局代理。

## 请求方式

支持以下HTTP请求方式：

- GET
- OPTIONS
- POST
- PUT
- PATCH
- DELETE
- HEAD

## 安装

确保在您的环境中安装了 Flask 和 requests

```python
pip install Flask requests
```

## 实例化Upstream类

```
def __init__(self, host, host_prefix=None, app=None, proxy=None, timeout=10):
```

- host: 上游服务器的主机。。（https://www.example.com）
- host_prefix: 添加到上游服务器URI。完整请求就是：host + host_prefix。
- app:  Flask 应用实例用于全局代理。
- proxy:  requests 会话的代理设置。 {"http":"127.0.0.1:8888"}
- timeout: 请求超时时间。

## 实例化Upstream类

- ### 基本代理：

```
from flask_reverse_proxy import Upstream 
rproxy = Upstream(host='https://www.example.com', timeout=20)
```

- ### 反向对象带有URI的代理：

```
from flask_reverse_proxy import Upstream 
rproxy = Upstream(host='https://www.example.com', host_prefix='/course', timeout=20)

```

- ### 全局代理

```
from flask_reverse_proxy import Upstream 
rproxy = Upstream(host='https://www.example.com', timeout=20, app=app)
```

## 用法

### 基本用法

#### 1. 装饰器用法

```python
from flask import Flask
from flask_reverse_proxy import Upstream

app = Flask(__name__)
rproxy = Upstream(host='https://www.example.com')

@app.route('/', methods=['GET', 'POST'])
@rproxy.proxy
def home():
    return "Hello, World!"

```

#### 2. 直接方法调用（用于修改数据）

```
@app.route('/publishment/news/', methods=['GET', 'POST'])
def news():
    resp = rproxy.proxy()
    resp.data = resp.data.decode().replace('成功', '失败')
    return resp
```

#### 3. 添加 URL 规则

```
app.add_url_rule('/course/search/', endpoint='course', view_func=rproxy.proxy, methods=['GET', 'POST'])
```

#### 4. 注册蓝图

```
blueprint = Blueprint('blueprint', __name__)
blueprint.add_url_rule('/platform/introduction/', endpoint='platform', view_func=rproxy.proxy, methods=['GET','POST'])
from flask import Blueprint
app.register_blueprint(blueprint)

```

#### 5. 带URI的蓝图

```
rproxy_prefix = Upstream(host='https://www.example.com', host_prefix='/course', timeout=20)
blueprint = Blueprint('blueprint2', __name__, url_prefix='/center')
blueprint.add_url_rule('/<path:path>', endpoint='platform', view_func=rproxy_prefix.proxy)
blueprint.add_url_rule('/', endpoint='platform', view_func=rproxy_prefix.proxy)
app.register_blueprint(blueprint)
```

网站访问: 127.0.0.1/center/<path:path> 反向代理实际访问:https://www.example.com/course

#### 6. 全局代理

```
app = Flask(__name__)
rproxy = Upstream(host='https://www.example.com', timeout=20,app=app)
```

或者

```
app = Flask(__name__)
rproxy = Upstream(host='https://www.example.com', timeout=20)
rproxy.any_proxy(app)
```

带app参数的实例化会直接代理全局或者用any_proxy方法实现全局代理，参数为flask实例化的app。

## 注意事项

- 在请求头中，Host会被设置为上游的host。
- 如果请求中包含Referer，它将被设置为请求的实际URL。
- 响应中，access-control-allow-origin和access-control-allow-credentials会被设置，以允许跨域请求。
- 特定的响应头如content-security-policy会被移除。
- Content-Type相关的处理，会根据媒体或文本类型做相应调整。
