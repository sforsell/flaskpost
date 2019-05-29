from datetime import datetime, timedelta
import unittest
from app import app, db
from app.models import User, Post


class TestUserModelCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_password_hashing(self):
        susan = User(username='susan')
        susan.set_password('kittycat')
        self.assertFalse(susan.check_password('puppy'))
        self.assertTrue(susan.check_password('kittycat'))

    def test_avatar(self):
        john = User(username='john', email='john@mail.com')
        self.assertEqual(john.avatar(128),
                         'https://www.gravatar.com/avatar/97c712aa60976209ae6d1c741b1338d3?d=retro&s=128')

    def test_follow(self):
        john = User(username='john', email='john@mail.com')
        susan = User(username='susan', email='susan@mail.com')
        db.session.add(john)
        db.session.add(susan)
        db.session.commit()
        # nobody has any followers or are following anyone
        self.assertEqual(john.followed.all(), [])
        self.assertEqual(john.followers.all(), [])
        self.assertEqual(susan.followed.all(), [])
        self.assertEqual(susan.followers.all(), [])

        john.follow(susan)
        db.session.commit()

        self.assertEqual(john.followers.count(), 0)
        self.assertEqual(susan.followed.count(), 0)
        self.assertTrue(john.is_following(susan))
        self.assertFalse(susan.is_following(john))
        self.assertEqual(john.followed.count(), 1)
        self.assertEqual(john.followed.first().username, 'susan')
        self.assertEqual(susan.followers.count(), 1)
        self.assertEqual(susan.followers.first().username, 'john')

        # john made a mistake. susan only posts cat related content and john is totally a dog person
        john.unfollow(susan)
        db.session.commit()
        self.assertFalse(john.is_following(susan))
        self.assertEqual(john.followed.count(), 0)
        self.assertEqual(susan.followers.count(), 0)

    def test_follow_posts(self):
        # create four users
        john = User(username='john', email='john@mail.com')
        susan = User(username='susan', email='susan@mail.com')
        jane = User(username='jane', email='jane@mail.com')
        steve = User(username='steve', email='steve@mail.com')
        db.session.add_all([john, susan, jane, steve])

        # create four posts
        now = datetime.utcnow()
        john_post = Post(body="post from john", author=john,
                         timestamp=now + timedelta(seconds=1))  # oldest post
        susan_post = Post(body="post from susan", author=susan,
                          timestamp=now + timedelta(seconds=4))  # newest post
        jane_post = Post(body="post from jane", author=jane,
                         timestamp=now + timedelta(seconds=3))  # second to newest post
        steve_post = Post(body="post from steve", author=steve,
                          timestamp=now + timedelta(seconds=2))  # second to oldest post
        db.session.add_all([john_post, susan_post, jane_post, steve_post])
        db.session.commit()

        # setup the followers
        john.follow(susan)
        john.follow(steve)
        susan.follow(jane)
        jane.follow(steve)
        db.session.commit()

        # check each users feed (order of posts is important)
        john_feed = john.followed_posts().all()
        susan_feed = susan.followed_posts().all()
        jane_feed = jane.followed_posts().all()
        steve_feed = steve.followed_posts().all()
        self.assertEqual(john_feed, [susan_post, steve_post, john_post])
        self.assertEqual(susan_feed, [susan_post, jane_post])
        self.assertEqual(jane_feed, [jane_post, steve_post])
        self.assertEqual(steve_feed, [steve_post])

    if __name__ == '__main__':
        unittest.main(verbosity=2)
