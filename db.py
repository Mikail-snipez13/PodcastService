import json
from werkzeug.security import generate_password_hash


def getPodcastPath(name):
    return 'Podcasts/' + name


class Driver:

    def __init__(self, path):
        self.path = path

    def getUser(self, username):
        with open(self.path, 'r') as file:

            data = json.load(file)
            users = data['users']

            for user in users:
                if user['username'] == username:
                    return User(user=user)

    def allUsers(self):
        with open(self.path, 'r') as file:
            data = json.load(file)
            return data

    def userExists(self, username) -> bool:
        if self.getUser(username) == None:
            return False
        return True

    def createUser(self, username, password):
        user = User(username=username, password=password)
        with open(self.path, 'r+') as file:
            data = json.load(file)
            users = data.get('users')
            users.append(user.__dict__)

            file.seek(0)
            file.write(json.dumps(data, indent=4))
            file.truncate()
        return user


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



    def getJSON(self):
        return json.dumps(self.__dict__, indent=4)
