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
    # 如果自定义表名，可以定义 __tablename__ 属性。
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
# 修改数据模型后，需要重新生成数据库迁移脚本，然后再执行脚本更新数据库。
# Flask 数据库迁移 flask-migrate： https://cloud.tencent.com/developer/article/1585940

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

# 8，数据库基本的CRUD操作
# 8.1，创建数据
# (venv) dfl@WebDev:~/learn/flask/watchlist$ flask shell
# Python 3.10.6 (main, Aug 10 2022, 11:40:04) [GCC 11.3.0] on linux
# App: app
# Instance: /home/dfl/learn/flask/watchlist/instance
# >>> from app import User, Movie
# >>> user = User(name='xiaolu2333')    # 在实例化模型类的时候，我们并没有传入 id 字段（主键），因为 SQLAlchemy 会自动处理这个字段。
# >>> m1 = Movie(title='Leon', year='1994')
# >>> m2 = Movie(title='Mahjong', year='1996')
# >>> db.session.add(user)  # 把新创建的记录添加到数据库会话
# >>> db.session.add(m1)
# >>> db.session.add(m2)
# >>> db.session.commit()  # 提交数据库会话，只需要在最后调用一次即可
# 创建数据的时候，我们也可以使用 add_all() 方法一次性添加多个记录，传入的参数是列表。
# >>> db.session.add_all([m1, m2])
# >>> db.session.commit()
# 8.2，查询数据
# 通过对模型类的 query 属性调用可选的过滤方法和查询方法就可以获取到对应的单个（模型类实例）或多个记录（模型类实例列表）：
# <模型类>.query.<过滤方法（可选）>.<查询方法>
# 8.2.1，查询所有记录
# >>> movies = Movie.query.all()    # 获取所有电影记录
# >>> type(movies)                  # 返回的是一个列表
# <class 'list'>
# >>> type(movies[0])               # 列表中的元素是 Movie 类的实例
# <class 'app.Movie'>
# >>> Movie.query.count()        # 获取电影记录的数量
# 2
# 8,2,2 过滤查询：filter/filter_by/limit/offset/order_by/group_by/having/first/first_or_404/get/get_or_404
# >>> Movie.query.first()        # 获取第一个电影记录
# <Movie 1>
# >>> Movie.query.get(1)         # 获取主键为 1 的电影记录
# <Movie 1>
# >>> Movie.query.filter_by(title='Leon').first()  # 获取标题为 Leon 的电影记录
# <Movie 1>
# >>> Movie.query.order_by(Movie.title).all()  # 获取所有电影记录，并按照标题进行排序
# [<Movie 1>, <Movie 2>]
# >>> Movie.query.order_by(Movie.title.desc()).all()  # 获取所有电影记录，并按照标题进行降序排序
# [<Movie 2>, <Movie 1>]
# >>> Movie.query.paginate(page=1, per_page=1).items  # 获取第 1 页，每页 1 条记录
# [<Movie 1>]
# >>> Movie.query.filter(Movie.title.like('%on%')).all()  # 获取标题中包含 on 的电影记录
# [<Movie 1>]
# >>> Movie.query.filter(Movie.title.ilike('%ON%')).all()  # 获取标题中包含 on 的电影记录，不区分大小写
# [<Movie 1>]
# >>> Movie.query.filter(Movie.title.in_(['Leon', 'Mahjong'])).all()  # 获取标题为 Leon 或 Mahjong 的电影记录
# [<Movie 1>, <Movie 2>]
# >>> Movie.query.filter(Movie.title.notin_(['Leon', 'Mahjong'])).all()  # 获取标题不为 Leon 或 Mahjong 的电影记录
# []
# >>> Movie.query.filter(Movie.title.is_('Leon')).all()  # 获取标题为 Leon 的电影记录
# []
# >>> Movie.query.filter(Movie.title.isnot('Leon')).all()  # 获取标题不为 Leon 的电影记录
# [<Movie 1>, <Movie 2>]
# >>> Movie.query.filter(Movie.title == 'Leon').all()  # 获取标题为 Leon 的电影记录
# [<Movie 1>]
# >>> Movie.query.filter(Movie.title != 'Leon').all()  # 获取标题不为 Leon 的电影记录
# [<Movie 2>]
# >>> Movie.query.filter(Movie.title > 'Leon').all()  # 获取标题大于 Leon 的电影记录
# [<Movie 2>]
# >>> Movie.query.filter(Movie.title >= 'Leon').all()  # 获取标题大于等于 Leon 的电影记录
# [<Movie 1>, <Movie 2>]
# >>> Movie.query.filter(Movie.title < 'Leon').all()  # 获取标题小于 Leon 的电影记录
# []
# >>> Movie.query.filter(Movie.title <= 'Leon').all()  # 获取标题小于等于 Leon 的电影记录
# [<Movie 1>]
# >>> Movie.query.filter(Movie.title != 'Leon').filter(Movie.year == '1996').all()  # 获取标题不为 Leon 并且年份为 1996 的电影记录
# [<Movie 2>]
# >>> Movie.query.filter(Movie.title != 'Leon', Movie.year == '1996').all()  # 获取标题不为 Leon 并且年份为 1996 的电影记录
# [<Movie 2>]
# >>> Movie.query.filter(or_(Movie.title == 'Leon', Movie.title == 'Mahjong')).all()  # 获取标题为 Leon 或 Mahjong 的电影记录
# [<Movie 1>, <Movie 2>]
# >>> Movie.query.filter(and_(Movie.title == 'Leon', Movie.year == '1996')).all()  # 获取标题为 Leon 并且年份为 1996 的电影记录
# [<Movie 1>]
# >>> Movie.query.first_or_404(Movie.title == 'Leon')  # 获取标题为 Leon 的电影记录，如果不存在则返回 404 错误
# <Movie 1>
# >>> Movie.query.get_or_404(1)  # 获取主键为 1 的电影记录，如果不存在则返回 404 错误
# <Movie 1>
# >>> Movie.query.filter(Movie.title == 'Leon').first_or_404()  # 获取标题为 Leon 的电影记录，如果不存在则返回 404 错误
# <Movie 1>
# >>> Movie.query.filter(Movie.title == 'Leon').one_or_none()  # 获取标题为 Leon 的电影记录，如果不存在则返回 None
# <Movie 1>
# >>> Movie.query.filter(Movie.title == 'Leon').one()  # 获取标题为 Leon 的电影记录，如果不存在或者存在多条记录则抛出异常
# <Movie 1>
# >>> Movie.query.filter(Movie.title == 'Leon').count()  # 获取标题为 Leon 的电影记录的数量
# 1
# >>> Movie.query.filter(Movie.title == 'Leon').exists()  # 判断标题为 Leon 的电影记录是否存在
# True
# >>> Movie.query.filter(Movie.title == 'Leon').limit(1).all()  # 获取标题为 Leon 的电影记录的前 1 条记录
# [<Movie 1>]
# >>> Movie.query.filter(Movie.title == 'Leon').offset(1).all()  # 获取标题为 Leon 的电影记录的第 2 条记录
# []
# >>> Movie.query.filter(Movie.title == 'Leon').order_by(Movie.year).all()  # 获取标题为 Leon 的电影记录并按照年份升序排序
# [<Movie 1>]
# >>> Movie.query.filter(Movie.title == 'Leon').order_by(Movie.year.desc()).all()  # 获取标题为 Leon 的电影记录并按照年份降序排序
# [<Movie 1>]
# >>> Movie.query.filter(Movie.title == 'Leon').order_by(Movie.year.asc()).all()  # 获取标题为 Leon 的电影记录并按照年份升序排序
# [<Movie 1>]
# >>> Movie.query.filter(Movie.title == 'Leon').order_by(Movie.year.desc()).order_by(Movie.title).all()  # 获取标题为 Leon 的电影记录并按照年份降序排序，如果年份相同则按照标题升序排序
# [<Movie 1>]
# >>> Movie.query.filter(Movie.title == 'Leon').order_by(Movie.year.desc(), Movie.title).all()  # 获取标题为 Leon 的电影记录并按照年份降序排序，如果年份相同则按照标题升序排序
# [<Movie 1>]
# >>> Movie.query.filter(Movie.title == 'Leon').order_by(Movie.year.desc(), Movie.title.desc()).all()  # 获取标题为 Leon 的电影记录并按照年份降序排序，如果年份相同则按照标题降序排序
# [<Movie 1>]
# >>> Movie.query.filter(Movie.year > '1996', Movie.year < '2000').all()    # 获取年份大于 1996 并且小于 2000 的电影记录
# [<Movie 1>]
# >>> Movie.query.filter(Movie.year.between('1996', '2000')).all()    # 获取年份在 1996 到 2000 之间的电影记录
# [<Movie 1>]
# 8.3 更新记录
# >>> movie = Movie.query.get(1)  # 获取主键为 1 的电影记录
# >>> movie.title = 'Leon: The Professional'  # 修改标题
# >>> movie.year = '1994'  # 修改年份
# >>> db.session.commit()  # 提交会话
# >>> # 统一将标题包含 Leon 的电影记录的标题修改为 Leon: The Professional
# >>> Movie.query.filter(Movie.title.like('%Leon%')).update({'title': 'Leon: The Professional'})
# 1
# >>> db.session.commit()  # 提交会话
# 8.4 删除记录
# >>> movie = Movie.query.get(1)  # 获取主键为 1 的电影记录
# >>> db.session.delete(movie)  # 删除电影记录
# >>> db.session.commit()  # 提交会话
# >>> Movie.query.filter(Movie.title.like('%Leon%')).delete()   # 删除所有标题包含 Leon 的电影记录
# Flask-SQLAlchemy：https://flask-sqlalchemy.palletsprojects.com/en/2.x/


# 向数据库插入测试数据。
import click
@app.cli.command()
def forge():
    # 先创建所有表
    db.create_all()
    # 准备测试数据
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
    # 添加测试数据
    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    # 提交会话
    db.session.commit()
    # 提示成功
    click.echo('Done.')
# 通过 flask forge 命令向数据库插入测试数据：
# (venv) dfl@WebDev:~/learn/flask/watchlist$ flask forge
# Done.


@app.errorhandler(404)  # 传入要处理的错误代码
# app.errorhandler() 装饰器注册一个错误处理函数。
# 它的作用和视图函数类似，当 404 错误发生时，这个函数会被触发，返回值会作为响应主体返回给客户端
def page_not_found(e):  # 接受异常对象作为参数
    user = User.query.first()
    return render_template('404.html', user=user), 404  # 返回模板和状态码


@app.route('/')
def index():
    user = User.query.first()  # 读取第一条用户记录
    movies = Movie.query.all()  # 读取所有电影记录
    return render_template('index.html', user=user, movies=movies)


if __name__ == '__main__':
    app.run()
    # 访问一个不存在的页面 http://127.0.0.1:5000/xxx
    # 浏览器页面内容发生变化，显示了自定义的 404 页面
