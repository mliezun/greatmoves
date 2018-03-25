import os
from random import randrange

import bcrypt
from flask import Flask, render_template, session, request, redirect, url_for, abort, send_from_directory
from flask_misaka import Misaka
from flask_seasurf import SeaSurf
from pony.orm import select, db_session, commit, desc
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.utils import secure_filename

from mailgun import send_account_verification, send_password_reset
from models import db, User, Post, Comment
from enlibrar_py2 import book
from threading import Thread, Timer

UPLOAD_FOLDER = 'pdfs/'
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    posts = select(p for p in Post if p.state == 'A').order_by(desc(Post.id))[:10]
    return render_template('index.html', posts=posts)


@app.route('/more_posts/<int:last_post_id>')
@db_session
def more_posts(last_post_id):
    posts = select(p for p in Post if p.state == 'A' and p.id < last_post_id).order_by(desc(Post.id))[:10]
    return render_template('more_posts.html', posts=posts)


@app.route('/post/new', methods=['GET', 'POST'])
@db_session
def new_post():
    if not session.get('user_state') == 'A' or session['user_type'] != 'A':
        abort(401)
    if request.method == 'POST':
        Post(author=session['user_id'], title=request.form['title'], body=request.form['body'])
        commit()
        return redirect(url_for('index'))
    return render_template('new_post.html')


@app.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@db_session
def edit_post(post_id):
    if not session.get('user_state') == 'A' or session['user_type'] != 'A':
        abort(401)
    post = select(p for p in Post if p.id == post_id and p.state == 'A').first()
    if not post:
        abort(404)
    if request.method == 'POST':
        post.title = request.form['title']
        post.body = request.form['body']
        commit()
        return redirect(url_for('show_post', post_id=post.id))
    return render_template('new_post.html', post=post)


@app.route('/post/hide/<int:post_id>', methods=['POST'])
@db_session
def hide_post(post_id):
    if not session.get('user_state') == 'A' or session['user_type'] != 'A':
        abort(401)
    post = select(p for p in Post if p.id == post_id).first()
    if not post:
        abort(404)
    post.state = 'I'
    commit()
    return redirect(url_for('index'))


@app.route('/post/<int:post_id>')
@db_session
def show_post(post_id):
    post = select(p for p in Post if p.id == post_id and p.state == 'A').first()
    if not post:
        abort(404)
    return render_template('post.html',
                           post=post,
                           comments=select(c for c in Comment if c.post == post and c.state == 'A'))


@app.route('/post/<int:post_id>/comment/new', methods=['POST'])
@db_session
def new_comment(post_id):
    if not session.get('user_state') == 'A':
        abort(401)
    if request.method == 'POST':
        if len(request.form['comment']) > 0:
            Comment(post=post_id, user=session['user_id'], comment=request.form['comment'])
            commit()
    return redirect(url_for('show_post', post_id=post_id))


@app.route('/post/<int:post_id>/comment/<int:comment_id>/hide', methods=['POST'])
@db_session
def hide_comment(post_id, comment_id):
    if not session.get('user_state') == 'A' or session['user_type'] != 'A':
        abort(401)
    comment = select(c for c in Comment if c.id == comment_id).first()
    if not comment:
        abort(404)
    comment.state = 'I'
    commit()
    return redirect(url_for('show_post', post_id=post_id))


@app.route('/user/login', methods=['GET', 'POST'])
@db_session
def login():
    error = None
    if request.method == 'POST':
        user = select(u for u in User if u.username == request.form['username'] and u.state != 'I').first()
        if not user or not bcrypt.hashpw(request.form['password'].encode('utf-8'),
                                         user.password.encode('utf-8')) == user.password:
            error = 'Invalid username or password'
        elif user.state == 'P':
            error = 'You need to verify your email'
        else:
            session['user_state'] = user.state
            session['username'] = user.username
            session['user_id'] = user.id
            session['user_type'] = user.type
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/user/logout')
def logout():
    session.pop('user_state', None)
    return redirect(url_for('index'))


def get_token():
    return str(randrange(101, 1000) ** randrange(100, 1001))[:100]


@app.route('/user/new', methods=['GET', 'POST'])
@db_session
def signup():
    error = None
    if request.method == 'POST':
        user = select(
            u for u in User if u.username == request.form['username'] or u.email == request.form['email']).first()
        if user:
            error = 'The username or the email is already taken'
        elif len(request.form['password']) < 6:
            error = 'The password must be at least 6 characters long'
        else:
            u = User(
                username=request.form['username'],
                password=bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                email=request.form['email'],
                token=get_token()
            )
            commit()
            send_account_verification(render_template('email_verify.html', user=u).encode('utf'), u.email)
            return render_template('login.html', error='Please verify your email and log in')
    return render_template('signup.html', error=error)


@app.route('/user/<username>/verify/<token>')
@db_session
def email_verify(username, token):
    error = None
    user = select(u for u in User if u.username == username and u.token == token).first()
    if user:
        user.state = 'A'
        user.token = get_token()
        commit()
        error = 'Your email has been verified'
    return render_template('login.html', error=error)


@app.route('/user/reset', methods=['GET', 'POST'])
@db_session
def reset_password_form():
    if request.method == 'POST':
        user = select(u for u in User if u.username == request.form['username'] and u.state != 'I').first()
        error = 'There is no user with that username'
        if user:
            error = 'Check your email to reset your password'
            send_password_reset(render_template('email_password.html', user=user).encode('utf'), user.email)
        return render_template('login.html', error=error)

    return render_template('reset_password.html', url=url_for('reset_password_form'), password=False)


@app.route('/user/<username>/reset/<token>', methods=['GET', 'POST'])
@db_session
def reset_password(username, token):
    if request.method == 'POST':
        user = select(u for u in User if u.username == username and u.state != 'I' and u.token == token).first()
        error = "You can't reset your password"
        if user:
            user.password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user.token = get_token()
            commit()
            error = 'Your password has been changed'
        return render_template('login.html', error=error)

    return render_template('reset_password.html',
                           url=url_for('reset_password', username=username, token=token),
                           password=True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/enlibrario/', methods=['GET', 'POST'])
def enlibrario():
    if request.method == 'POST':
        print request.files
        if 'file' not in request.files:
            return render_template('enlibrario.html', error='You have to select a file to upload')
        file = request.files['file']
        if file.filename == '':
            return render_template('enlibrario.html', error='You have to select a file to upload')
        if file and allowed_file(file.filename):
            filename = str(randrange(10000, 100000)) + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            def create_book():
                book(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            t = Thread(target=create_book)
            t.start()
            return redirect(url_for('wait', filename=filename))
    return render_template('enlibrario.html')


@app.route('/enlibrario/<filename>')
def download(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return redirect(url_for('enlibrario'))
    filepath2 = os.path.join(app.config['UPLOAD_FOLDER'], filename.replace('.pdf', '_formatted.pdf'))
    if not os.path.exists(filepath2):
        return redirect(url_for('wait', filename=filename))

    def deleteFile(path):
        os.remove(path)

    deleteFile(filepath)
    t = Timer(15 * 60, lambda: deleteFile(filepath2))
    t.start()
    return send_from_directory(UPLOAD_FOLDER, filename.replace('.pdf', '_formatted.pdf'), as_attachment=True)


@app.route('/enlibrario/<filename>/status')
def status(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename.replace('.pdf', '_formatted.pdf'))
    return os.path.exists(filepath) and 'S' or 'N'


@app.route('/enlibrario/<filename>/wait')
def wait(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return redirect(url_for('enlibrario'))
    return render_template('waitbook.html', filename=filename)


app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run(debug=True)
