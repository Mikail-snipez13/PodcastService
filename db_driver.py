import json
from io import BytesIO

class Driver:

    def __init__(self, path):
        self.path = path

    def getUser(self, username):
        with open(self.path, 'r') as file:

            data = json.load(file)
            users = data['users']

            for user in users:
                if user['username'] == username:
                    return user

    def allUsers(self):
        with open(self.path, 'r') as file:
            data = json.load(file)
            return data

    def getPodcastPath(self, name):
        return 'Podcasts/' + name