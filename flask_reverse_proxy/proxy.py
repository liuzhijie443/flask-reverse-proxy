import datetime
import functools
import requests
from flask import request, Response, current_app
from urllib.parse import urlparse
import urllib3

urllib3.disable_warnings()


# 请求方式：['GET' , 'OPTIONS' , 'POST- ' , 'PUT' , 'PATCH' , 'DELETE' , 'HEAD']
# 上游类
class Upstream(object):
    """
    # 1.装饰器方式使用
    @app.route('/',methods=['GET','POST'])
    @rproxy.proxy
    def home():
        print('/')


    # 2.方法中使用（用于修改数据）
    @app.route('/publishment/news/',methods=['GET','POST'])
    def news():
        resp = rproxy.proxy()
        resp.data = resp.data.decode().replace('成功','失败')
        return resp


    # 3.添加规则使用
    app.add_url_rule('/course/search/', endpoint='course', view_func=rproxy.proxy,methods=['GET','POST'])

    # 4.蓝图使用
    blueprint = Blueprint('blueprint', __name__)
    # 添加蓝图规则
    blueprint.add_url_rule('/platform/introduction/', endpoint='platform', view_func=rproxy.proxy, methods=['GET','POST'])
    # 注册蓝图
    app.register_blueprint(blueprint)


    # 5.蓝图带前缀的使用方法
    # 网站访问: 127.0.0.1/center/123 >> 反向代理实际访问:https://www.learning.mil.cn/course
    # 实例化，实际需要访问的网站自动带上前缀prefix
    rproxy_prefix = Upstream(host='https://www.learning.mil.cn', host_prefix='/course', timeout=20)
    # 蓝图，本地访问的链接需要加上前缀prefix
    blueprint = Blueprint('blueprint2', __name__, url_prefix='/center')
    # 添加蓝图规则
    blueprint.add_url_rule('/<path:path>', endpoint='platform', view_func=rproxy_prefix.proxy)
    blueprint.add_url_rule('/', endpoint='platform', view_func=rproxy_prefix.proxy)
    # 注册蓝图
    app.register_blueprint(blueprint)

    # 6.全局代理使用
    # 实例化Flask
    app = Flask(__name__)
    # 实例 反向代理项目 （带app参数会直接代理全局）
    rproxy = Upstream(host='https://www.learning.mil.cn', timeout=20,app=app)
    # （或者用any_proxy方法实现全局代理，参数为flask实例化的app）
    rproxy.any_proxy(app)


    """
    # 代理上游的host
    host = None
    # 代理上游协议
    scheme = None
    # 请求上游请求超时时间
    timeout = None
    # 请求上游的前缀host+host_prefix
    host_prefix = None
    # 实例化requests
    x = None
    # 请求方式
    methods = ['GET', 'OPTIONS', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD']

    # 初始化
    def __init__(self, host, host_prefix=None, app=None, proxy=None, timeout=10):
        # 解析网站
        parsed_url = urlparse(host)
        self.scheme = parsed_url.scheme or 'http'
        self.host = parsed_url.netloc
        self.timeout = timeout
        # 设置网站前缀
        self.host_prefix = host_prefix
        # 实例化requests并且判断是否使用代理
        self.x = requests.Session()
        self.x.verify = False
        if isinstance(proxy, dict):
            self.x.proxies = proxy
        # 全局代理
        if app:
            self.any_proxy(app)

    # 全局代理
    def any_proxy(self, app):
        # 代理全部内容
        methods = ['GET', 'OPTIONS', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD']
        app.add_url_rule('/', endpoint='anyproxy1', view_func=self.proxy, methods=methods)
        app.add_url_rule('/<path:path>', endpoint='anyproxy2', view_func=self.proxy, methods=methods)
        app.add_url_rule('/static/<path:path>/<path:any>', endpoint='anyproxy3', view_func=self.proxy,
                         methods=methods)

    # 反向代理
    def proxy(self, func=None, *args, **kwargs):
        @functools.wraps(func)
        def _view(*args, **kwargs):
            # 获取请求的uri
            uri = request.path
            time = datetime.datetime.now()
            print(f"{time} {uri}")
            # 如果是否为蓝图规则请求
            if request.blueprint:
                # 查询蓝图请求的前缀
                local_prefix = current_app.blueprints[request.blueprint].url_prefix
                # 如果存在蓝图前缀则把前缀去掉，获取到真是请求的uri
                if local_prefix is not None:
                    uri = request.path.split(local_prefix)[1]

            # 拼接链接
            base_url = '%s://%s' % (self.scheme, self.host)
            url = base_url + (self.host_prefix or "") + uri

            # 请求头修改
            headers = dict(request.headers)
            headers['Host'] = self.host
            headers[
                'User-Agent'] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63060012)"

            if 'Referer' in headers: headers['Referer'] = url
            if 'Origin' in headers: del headers['Origin']

            # 实际请求网站
            resp = self.x.request(url=url,
                                  method=request.method,
                                  headers=headers,
                                  params=dict(request.args),
                                  data=request.get_data(),
                                  # 是否允许重定向
                                  allow_redirects=True,
                                  stream=True,
                                  timeout=self.timeout
                                  )

            # 响应请求头修改
            resp.headers['access-control-allow-origin'] = '*'
            resp.headers['access-control-allow-credentials'] = 'True'
            if 'content-security-policy' in resp.headers: del resp.headers['content-security-policy']
            if 'content-security-policy-report-only' in resp.headers: del resp.headers[
                'content-security-policy-report-only']
            if 'clear-site-data' in resp.headers: del resp.headers['clear-site-data']
            excluded_headers = [
                'content-length', 'transfer-encoding', 'connection', 'Content-Encoding'
            ]
            for h in excluded_headers:
                if h in resp.headers:
                    resp.headers.pop(h)

            # 请求响应准备
            response = Response(resp.content, resp.status_code, dict(resp.headers))

            # 判断Content-Type类型
            if 'Content-Type' in resp.headers:
                content_type = resp.headers['Content-Type']
                media_types = ['image', 'video', 'audio']
                text_types = ['text/plain', 'text/html', 'application/json']
                # 判断是否媒体类型
                if any(i in content_type for i in media_types):
                    pass
                # 判断是否文本类型
                elif any(i in content_type for i in text_types):
                    html = resp.text
                    response = Response(html, resp.status_code, dict(resp.headers))
                else:
                    pass

            # response解码
            # response.content_encoding = resp.apparent_encoding

            return response

        # 判断返回什么类型数据
        return _view() if func is None else _view
