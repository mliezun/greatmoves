from flask import Flask, render_template, session, request, redirect, url_for, abort
from werkzeug.contrib.fixers import ProxyFix
from flask_seasurf import SeaSurf
from flask_misaka import Misaka
from pony.orm import select, db_session, commit
from models import db, User, Post, Comment
import bcrypt
import misaka

app = Flask(__name__)

app.config.update(dict(
    SECRET_KEY='development key',
))

csrf = SeaSurf(app)
Misaka(app)

db.bind(provider='sqlite', filename='database.sqlite', create_db=True)
db.generate_mapping(create_tables=True)


@app.route('/')
@db_session
def index():
    posts = select(p for p in Post if p.state == 'A')
    return render_template('index.html', posts=posts)


@app.route('/post/new', methods=['GET', 'POST'])
@db_session
def new_post():
    if not session.get('logged_in') or session['user_type'] != 'A':
        abort(401)
    if request.method == 'POST':
        Post(author=session['user_id'], title=request.form['title'], body=request.form['body'])
        commit()
        return redirect(url_for('index'))
    return render_template('new_post.html')


@app.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@db_session
def edit_post(post_id):
    if not session.get('logged_in') or session['user_type'] != 'A':
        abort(401)
    post = select(p for p in Post if p.id == post_id and p.state == 'A').first()
    if not post:
        abort(404)
    if request.method == 'POST':
        post.title = request.form['title']
        post.body = request.form['body']
        commit()
        return redirect(url_for('show_post', post_id = post.id))
    return render_template('new_post.html', post = post)


@app.route('/post/<int:post_id>')
@db_session
def show_post(post_id):
    post = select(p for p in Post if p.id == post_id and p.state == 'A').first()
    if not post:
        abort(404)
    return render_template('post.html', post=post, comments=post.comments.order_by(Comment.id))


@app.route('/post/<int:post_id>/comment/new', methods=['POST'])
@db_session
def new_comment(post_id):
    if not session.get('logged_in'):
        abort(401)
    if request.method == 'POST':
        if len(request.form['comment']) > 0:
            Comment(post=post_id, user=session['user_id'], comment=request.form['comment'])
            commit()
    return redirect(url_for('show_post', post_id=post_id))


@app.route('/user/login', methods=['GET', 'POST'])
@db_session
def login():
    error = None
    if request.method == 'POST':
        user = select(u for u in User if u.username == request.form['username'] and u.state == 'A').first()
        if not user or not bcrypt.hashpw(request.form['password'].encode('utf-8'), user.password.encode('utf-8')) == user.password:
            error = 'Invalid username or password'
        else:
            session['logged_in'] = True
            session['username'] = user.username
            session['user_id'] = user.id
            session['user_type'] = user.type
            print(user.type)
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/user/logout')
@db_session
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.route('/user/new', methods=['GET', 'POST'])
@db_session
def signup():
    error = None
    if request.method == 'POST':
        user = select(u for u in User if u.username == request.form['username'] or u.email == request.form['email']).first()
        if user:
            error = 'The username or the email is already taken'
        else:
            User(
                username=request.form['username'],
                password=bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                email=request.form['email']
            )
            commit()
            return redirect(url_for('index'))
    return render_template('signup.html', error=error)

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run()
