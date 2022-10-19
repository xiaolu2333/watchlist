from flask import Flask, url_for
from markupsafe import escape

app = Flask(__name__)


@app.route('/')  # 最简单的路由
def test_1():
    return '<h1>Hello Totoro!</h1><img src="http://helloflask.com/totoro.gif">'


@app.route('/user/<string:name>')  # 动态路由：在路由中使用变量
def test_2(name):
    return f'<h1>Hello {escape(name)}!</h1>'
    # 用户输入的数据会包含恶意代码，所以不能直接作为响应返回，
    # 需要使用 MarkupSafe（Flask 的依赖之一）提供的 escape() 函数对 name 变量进行转义处理，
    # 比如把 < 转换成 &lt;。这样在返回响应时浏览器就不会把它们当做代码执行。


@app.route('/users', endpoint='user_list')  # 为路由起别名：指定 endpoint 参数
def test_3():
    return 'User List'


@app.route('/test')
def test_url_for():
    # url_for() 函数可获取 URL。

    # 第一个参数是视图函数的名字，可通过函数视图名称获取 URL。
    print(url_for('test_1'))  # -> /
    print(url_for('test_url_for'))  # -> /test

    # 第一个参数也可以是 endpoint 的名字，可通过 endpoint 获取 URL。
    print(url_for('user_list'))  # -> /users

    # 后面的参数是 URL 规则中的变量部分
    print(url_for('test_2', name='greyli'))  # -> /user/greyli
    # 多余的关键字参数会被作为查询字符串附加到 URL 后面。
    print(url_for('test_url_for', num=2))  # 输出：/test?num=2

    return 'Test page'


if __name__ == '__main__':
    app.run()
    # 访问 http://127.0.0.1:5000/test
    # 查看控制台结果
