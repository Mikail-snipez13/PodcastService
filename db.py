import json
from werkzeug.security import generate_password_hash
import datetime


def get_podcast_path(name):
    return 'Podcasts/Audios/' + name

def get_date_now():
    return datetime.datetime.now().strftime("%a, %d %h %G %T -01:00")

class Driver:

    def __init__(self, path):
        self.path = path

    def get_user(self, username):
        data = self.all_users()
        users = data['users']

        for user in users:
            if user['username'] == username:
                return User(user=user)

    def all_users(self):
        with open(self.path, 'r') as file:
            data = json.load(file)
            return data

    def user_exists(self, username) -> bool:
        if self.get_user(username) is None:
            return False
        return True

    def create_user(self, username, password):
        user = User(username=username, password=password)
        with open(self.path, 'r+') as file:
            data = json.load(file)
            users = data.get('users')
            users.append(user.__dict__)

            file.seek(0)
            file.write(json.dumps(data, indent=4))
            file.truncate()
        return user

    def delete_user(self, username):
        if not self.user_exists(username):
            return 1

        with open(self.path, "r+") as file:
            data = json.load(file)
            data['users'] = [user for user in data.get('users') if user.get('username') != username]

            file.seek(0)
            file.write(json.dumps(data, indent=4))
            file.truncate()
            return 0

    def podcast_exists(self, username, title):
        podcasts = self.get_user(username).podcasts
        for podcast in podcasts:
            if podcast.get('title') == title:
                return True
        return False

    def episode_exists(self, username, pod_title, ep_title):
        podcasts = self.get_user(username).podcasts
        for podcast in podcasts:
            if podcast.get('title') == pod_title:
                items = podcast.get('items')
                for item in items:
                    if item.get('title') == ep_title:
                        return True
        return False

    def create_podcast(self, username, title, link, description, language, author, image, explicit, category):
        podcast = Podcast(title, link, description, language, author, image, explicit, category)
        data = self.all_users()
        users = data.get('users')
        for user in users:
            if user['username'] == username:
                user['podcasts'].append(podcast.__dict__)
                with open(self.path, 'w') as file:
                    file.write(json.dumps(data, indent=4))
                return

    def delete_podcast(self, username, title):
        data = self.all_users()
        users = data.get('users')

        if not self.podcast_exists(username, title):
            return False

        for user in users:
            if user['username'] == username:
                user['podcasts'] = [podcast for podcast in user['podcasts'] if podcast.get('title') != title]
                with open(self.path, 'w') as file:
                    file.write(json.dumps(data, indent=4))
                return True  # if podcast was found

    def add_episode(self, username, data):
        if not self.podcast_exists(username, data.get('podcast_title')):
            return 1

        if self.episode_exists(username, data.get('podcast_title'), data.get('title')):
            return 2

        db = self.all_users()
        users = db.get('users')
        for user in users:
            if user['username'] == username:
                podcasts = user.get('podcasts')
                for podcast in podcasts:
                    if podcast['title'] == data.get('podcast_title'):
                        items = podcast.get('items')
                        items.append(Episode(data['title'], data['description'],
                                             data['author'],
                                             get_date_now(),
                                             data['enclosure'],
                                             data['explicit'],
                                             data['image'],
                                             data['keywords']).__dict__)
                        with open(self.path, 'w') as file:
                            file.write(json.dumps(db, indent=4))
                        return 0

    def delete_episode(self, username, pod_title, ep_title):
        if not self.episode_exists(username, pod_title, ep_title):
            return False

        data = self.all_users()
        users = data.get('users')
        for user in users:
            if user['username'] == username:
                podcasts = user.get('podcasts')
                for podcast in podcasts:
                    if podcast['title'] == pod_title:
                        podcast['items'] = [item for item in podcast['items'] if item.get('title') != ep_title]
                        with open(self.path, 'w') as file:
                            file.write(json.dumps(data, indent=4))
                        return True
        return False




class User:
    def __init__(self, username=None, password=None, user=None):
        if username is not None and password is not None:
            self.username = username
            self.password = generate_password_hash(password)
            self.podcasts = []
            self.roles = ["user"]

        if user is not None:
            self.username = user.get('username')
            self.password = user.get('password')
            self.podcasts = user.get('podcasts')
            self.roles = user.get('roles')

    def add_podcast(self, podcast):
        self.podcasts.append(podcast.__dict__)

    def get_json(self):
        return json.dumps(self.__dict__, indent=4)


class Podcast:
    def __init__(self, title, link, description, language, author, image, explicit, category):
        self.title = title
        self.link = link  # link to rss feed
        self.description = description
        self.language = language  # de
        self.author = author
        self.image = image
        self.explicit = explicit  # valid values => no/false/yes/true/clean
        self.category = category
        self.type = "episodic"
        self.items = []


class Episode:
    def __init__(self, title, description, author, pub_date, enclosure, explicit, image, keywords):
        self.title = title
        self.description = description
        self.author = author
        self.pub_date = pub_date
        self.enclosure = enclosure
        self.explicit = explicit
        self.image = image
        self.keywords = keywords
