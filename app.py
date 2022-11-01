import os
import sys

from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

#####################################################################
# Configuration
#####################################################################
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

# 设置签名所需的密钥，用于保护表单免受跨站请求伪造（Cross-site Request Forgery）的攻击。
app.config['SECRET_KEY'] = 'dev'  # 等同于 app.secret_key = 'dev'
# 这个密钥的值在开发时可以随便设置。
# 基于安全的考虑，在部署时应该设置为随机字符，且不应该明文写在代码里，在部署章节会详细介绍。


#####################################################################
# Models
#####################################################################
# 5，定义数据模型
class User(db.Model, UserMixin):  # 表名将会是 user（自动生成，小写处理）。使用 Flask-Login 步骤二：让 User 模型继承 UserMixin 类，从而让 User 类拥有几个用于判断认证状态的属性和方法，
    # 如果自定义表名，可以定义 __tablename__ 属性。
    id = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(20))  # 名字
    username = db.Column(db.String(20))  # 用户名
    password_hash = db.Column(db.String(128))  # 密码散列值

    def set_password(self, password):  # 用来设置密码的方法，接受密码作为参数
        self.password_hash = generate_password_hash(password)  # 将生成的密码保持到对应字段

    def validate_password(self, password):  # 用于验证密码的方法，接受密码作为参数
        return check_password_hash(self.password_hash, password)  # 返回布尔值
# 因为模型（表结构）发生变化，我们需要重新生成数据库（这会清空数据）：flask initdb --drop


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
#####################################################################
# Commands
#####################################################################
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


@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)  # 设置密码
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)  # 设置密码
        db.session.add(user)

    db.session.commit()  # 提交数据库会话
    click.echo('Done.')
# 通过 flask admin 命令创建管理员账户：xiaolu，密码：123456
# 更多的用户管理功能通常使用 Flask-Login：https://flask-login.readthedocs.io/en/latest/


#####################################################################
# 处理工具
#####################################################################
@app.context_processor
# 使用上下文处理器能将 user 作为全局变量传入所有模板。
def inject_user():
    user = User.query.first()
    return dict(user=user)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


# 使用 Flask-Login 步骤一：创建用户加载回调函数
login_manager = LoginManager(app)  # 实例化扩展类
@login_manager.user_loader
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数。当程序运行后，如果用户已登录， current_user 变量的值会是当前用户的用户模型类记录
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户
    return user  # 返回用户对象


#####################################################################
# views
#####################################################################
@app.route('/', methods=['GET', 'POST'])    # 让视图函数支持 GET 和 POST 请求。
def index():
    """主页视图函数"""
    # 对于 POST 请求，则获取提交的表单数据并保存。
    if request.method == 'POST':  # 判断是否是 POST 请求
        """ request 是 Flask 提供的一个全局对象，它封装了客户端发出的 HTTP 请求中的内容：
        请求的路径（request.path）
        请求的方法（request.method）
        表单数据（request.form）
        查询字符串（request.args）
        远程地址（request.remote_addr）
        请求头（request.headers）
        文件数据（request.files）
        """
        # 获取表单数据
        title = request.form.get('title')  # 传入表单对应输入字段的 name 值
        year = request.form.get('year')
        # 验证数据
        if not title or not year or len(year) > 4 or len(title) > 60:
            """
            在真实工作里会进行更严苛的验证，比如对数据去除首尾的空格。
            一般情况下，我们会使用第三方库（比如 WTForms）来实现表单数据的验证工作。
            """
            flash('Invalid input.')  # 显示错误提示
            """ flash() 函数用来在视图函数里向模板传递提示消息
            该函数会把消息存储到 Flask 提供的 session 对象里，session 对象会把数据存储到浏览器的 cookie 里，记得要设置签名密钥。
            可以在模板中使用 get_flashed_messages() 函数获取到所有的提示消息。
            """
            return redirect(url_for('index'))  # 重定向回主页
        # 保存表单数据到数据库
        movie = Movie(title=title, year=year)  # 创建记录
        db.session.add(movie)  # 添加到数据库会话
        db.session.commit()  # 提交数据库会话
        flash('Item created.')  # 显示成功创建的提示
        return redirect(url_for('index'))  # 重定向回主页
    # 对于 GET 请求，返回渲染后的页面；
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)


@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit(movie_id):
    """条目编辑视图函数"""
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':  # 处理编辑表单的提交请求
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回对应的编辑页面

        movie.title = title  # 更新标题
        movie.year = year  # 更新年份
        db.session.commit()  # 提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index'))  # 重定向回主页

    return render_template('edit.html', movie=movie)  # 传入被编辑的电影记录


@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
def delete(movie_id):
    """条目删除视图函数"""
    movie = Movie.query.get_or_404(movie_id)  # 获取电影记录
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页


@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录视图函数"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)  # 使用 Flask_Login 的 login_user 函数实现用户登录
            flash('Login success.')
            return redirect(url_for('index'))  # 重定向到主页

        flash('Invalid username or password.')  # 如果验证失败，显示错误消息
        return redirect(url_for('login'))  # 重定向回登录页面

    return render_template('login.html')


@app.route('/logout')
@login_required  # 用于视图保护，后面会详细介绍
def logout():
    """用户登出视图函数"""
    logout_user()  # 使用 Flask_Login 的 logout_user 函数实现用户登出
    flash('Goodbye.')
    return redirect(url_for('index'))  # 重定向回首页


if __name__ == '__main__':
    app.run()
    # 访问主页 http://127.0.0.1:5000
    # 浏览器页面内容发生变化，点击 IMDb 链接，页面跳转到 IMDb 页面。
