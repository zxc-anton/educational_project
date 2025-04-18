import os


from datetime import datetime, timezone, timedelta
import unittest
from app import db, create_app
from app.models import User, Post
from config import Config

class Testbing(Config):
    SQLALCHEMY_DATABASE_URI='sqlite://'
    TESTING=True

class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(Testbing)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='Susan', email='susan@gmail.com')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertTrue(u.avatar(128), ("https://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?d=identicon&s=128"))

    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        following = db.session.scalars(u1.following.select()).all()
        followers = db.session.scalars(u2.followers.select()).all()
        self.assertEqual(following, [])
        self.assertEqual(followers, [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 1)
        self.assertEqual(u2.followers_count(), 1)
        u1_following = db.session.scalars(u1.following.select()).all()
        u2_followers = db.session.scalars(u2.followers.select()).all()
        self.assertEqual(u1_following[0].username, 'susan')
        self.assertEqual(u2_followers[0].username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 0)
        self.assertEqual(u2.followers_count(), 0)

    def test_follow_posts(self):
        u1 = User(username="john", email="john@mail.com")
        u2 = User(username="anton", email="anton@mail.com")
        u3 = User(username="mary", email="mary@mail.com")
        u4 = User(username="sany", email="sany@mail.com")

        db.session.add_all([u1, u2, u3, u4])

        now = datetime.now(timezone.utc)
        p1 = Post(body="post from john", timestamp=now+timedelta(seconds=1), author=u1)
        p2 = Post(body="post from anton", timestamp=now+timedelta(seconds=2), author=u2)
        p3 = Post(body="post from mary", timestamp=now+timedelta(seconds=3), author=u3)
        p4 = Post(body="post from sany", timestamp=now+timedelta(seconds=4), author=u4)

        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        u1.follow(u2)
        u1.follow(u3)
        u2.follow(u1)
        u3.follow(u4)
        db.session.commit()

        f1 = db.session.scalars(u1.following_posts()).all()
        f2 = db.session.scalars(u2.following_posts()).all()
        f3 = db.session.scalars(u3.following_posts()).all()
        f4 = db.session.scalars(u4.following_posts()).all()
        self.assertEqual(f1, [p3, p2, p1])
        self.assertEqual(f2, [p2, p1])
        self.assertEqual(f3, [p4, p3])
        self.assertEqual(f4, [p4])


if __name__ == "__main__":
    unittest.main(verbosity=2)


