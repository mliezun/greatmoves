from pony.orm import Database, Required, Set, PrimaryKey
from datetime import datetime

db = Database()


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    username = Required(str, unique=True)
    password = Required(str)
    email = Required(str, unique=True)
    # Types: Admin or Guest
    type = Required(str, default='G')
    # States: Active or Inactive
    state = Required(str, default='A')

    posts = Set('Post')
    comments = Set('Comment')


class Post(db.Entity):
    id = PrimaryKey(int, auto=True)
    author = Required(User)
    title = Required(str)
    body = Required(str)
    created_at = Required(datetime, default=datetime.now)
    # States: Active or Inactive
    state = Required(str, default='A')

    comments = Set('Comment')


class Comment(db.Entity):
    id = PrimaryKey(int, auto=True)
    post = Required(Post)
    user = Required(User)
    comment = Required(str)
    created_at = Required(datetime, default=datetime.now)
    # States: Active or Inactive
    state = Required(str, default='A')
