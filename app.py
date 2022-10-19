from flask import Flask, url_for, render_template
from markupsafe import escape

app = Flask(__name__)


@app.route('/')  # 最简单的路由
def index():
    name = 'xiaolu2333'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    # 使用render_template函数渲染模板：第一个参数是模板的文件名，其余参数是传递给模板的变量
    return render_template('index.html', name=name, movies=movies)


if __name__ == '__main__':
    app.run()
    # 访问 http://127.0.0.1:5000
    # 查看浏览器显示
