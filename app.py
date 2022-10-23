import os
import sys

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

# 1，根据系统设置数据库文件的路径前缀
WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)

# 2，设置数据库文件的路径
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
# 3，关闭对模型修改的监控
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 4，初始化扩展，传入程序实例 app，这样才能使用 app.config 配置参数
db = SQLAlchemy(app)


# 5，定义数据模型
class User(db.Model):  # 表名将会是 user（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))  # 名字


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主键
    title = db.Column(db.String(60))  # 电影标题
    year = db.Column(db.String(4))  # 电影年份

# 6，在数据库中创建所有模型对应的表
# (venv) $ flask shell
# >>> from app import db
# >>> db.create_all()
# 然后会在上面指定的地方创建 .db 文件，这个文件就是数据库文件，可以用 SQLite 等工具打开查看，一般不需要提交到版本库中。
# 如果改动了模型类，想重新生成表模式，需要先使用 db.drop_all() 删除表，然后重新创建。
# 如果想在不破坏数据库内的数据的前提下变更表的结构，需要使用数据库迁移工具，比如集成了 Alembic 的 Flask-Migrate 扩展。


# 7，一般会创建一个来自动执行创建数据库表操作的自定义命令：
import click
@app.cli.command()  # 注册为命令，可以传入 name 参数来自定义命令，否则函数名称就是命令的名字
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息
# 然后在命令行中执行 flask initdb 命令，就会自动创建数据库表了。
# 如果想要删除表后重新创建，可以执行 flask initdb --drop 命令。



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
