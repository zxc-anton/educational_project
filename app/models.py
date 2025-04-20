from app import db, login
import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
import jwt
from time import time
from flask import current_app
from app.search import add_to_index, remove_from_object, query_index
import json
from time import time

class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return [], 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        query = sa.select(cls).where(cls.id.in_(ids)).order_by(db.case(*when, value=cls.id))
        return db.session.scalars(query), total
    
    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_object(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in db.session.scalars(sa.select(cls)):
            add_to_index(cls.__tablename__, obj)
db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)
followers = sa.Table('followers', 
                     db.metadata,
                     sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
                     sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True))

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    last_message_read_time: so.Mapped[Optional[datetime]]
    notifications: so.WriteOnlyMapped['Notification'] = so.relationship(back_populates='user')

    messages_sent: so.WriteOnlyMapped['Message'] = so.relationship(foreign_keys='Message.sender_id', back_populates='author')
    messages_received: so.WriteOnlyMapped['Message'] = so.relationship(foreign_keys='Message.recipient_id', back_populates='recipient')


    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author')
    following: so.WriteOnlyMapped['User'] = so.relationship(secondary=followers, 
                primaryjoin=(followers.c.follower_id == id), 
                secondaryjoin=(followers.c.followed_id == id),
                back_populates='followers')
    followers: so.WriteOnlyMapped['User'] = so.relationship(secondary=followers,
                primaryjoin=(followers.c.followed_id == id),
                secondaryjoin=(followers.c.follower_id == id),
                back_populates='following')

    def __repr__(self):
        return f"<User {self.username}>"
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"
    
    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None
    
    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(self.followers.select().subquery())
        return db.session.scalar(query)
    
    def following_count(self):
        query = sa.select(sa.func.count()).select_from(self.following.select().subquery())
        return db.session.scalar(query)
    
    def following_posts(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post).join(Post.author.of_type(Author)).join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(Follower.id == self.id, Author.id == self.id,))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )
    
    def get_password_token(self, expires_in=600):
        return jwt.encode({"reset_password":self.id, 'exp': time()+expires_in}, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    def unread_message_count(self):
        query = sa.select(Message).where(Message.recipient == self, Message.check_status == False)
        return db.session.scalar(sa.select(sa.func.count()).select_from(query.subquery()))
    
    @staticmethod
    def check_jwt(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms='HS256')['reset_password']
        except:
            return
        return db.session.get(User, id)
    
    def add_notification(self, name,  data):
        db.session.execute(self.notifications.delete().where(Notification.name == name))
        notification = Notification(user=self, name=name, payload_json=json.dumps(data))
        db.session.add(notification)
        return notification
    
    @login.user_loader
    def load_user(id):
        return db.session.get(User, int(id))



    
class Post(SearchableMixin, db.Model):
    __searchable__ = ['body']
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(default=lambda:datetime.now(timezone.utc), index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    language: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5))
    
    author: so.Mapped[User] = so.relationship(back_populates='posts')

    def __repr__(self):
        return f"<Post {self.body}>"
    


class Message(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    sender_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    recipient_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140), index=True)
    timestamp: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))
    check_status: so.Mapped[bool] = so.mapped_column(default=False, index=True)
    time_seen: so.Mapped[Optional[datetime]] 

    author: so.Mapped[User] = so.relationship(foreign_keys='Message.sender_id', back_populates='messages_sent')
    recipient: so.Mapped[User] = so.relationship(foreign_keys='Message.recipient_id', back_populates='messages_received')

    def __repr__(self):
        return f"<Message {self.body}>"
    
class Notification(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    timestamp: so.Mapped[float] = so.mapped_column(default=time)
    payload_json: so.Mapped[str] = so.mapped_column(sa.Text)
    
    user: so.Mapped[User] = so.relationship(back_populates='notifications')

    def get_data(self):
        return json.loads(str(self.payload_json))
