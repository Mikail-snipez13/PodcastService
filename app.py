__author__ = "Mikail Gündüz"
__version__ = "0.0.1"

from flask import Flask, request, send_file, jsonify, abort
from flask_httpauth import HTTPBasicAuth
from db import Driver, getPodcastPath
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
auth = HTTPBasicAuth()
driver = Driver(path="./users.json")


# ------------ Auth ------------
@auth.get_user_roles
def get_user_roles(user):
    return user.roles


@auth.verify_password
def verify_password(username, password):
    user = driver.getUser(username)
    if user != None and check_password_hash(user.password, password):
        return user


# ----------- ROUTES -----------
@app.route('/', methods=['GET'])
@auth.login_required(role='user')
def home():
    return 'logged in as {}'.format(auth.current_user().username)
    # return send_file('./YKWIM.mp3')


@app.route('/allUsers', methods=['GET'])
@auth.login_required(role='admin')
def all_users():
    return driver.allUsers()


@app.route('/createUser', methods=['POST'])
@auth.login_required(role='admin')
def create_user():
    headers = request.headers
    try:
        if headers["username"] is not None and headers["password"] is not None:
            if driver.userExists(headers['username']):
                return {"status": "user exists", "message": "can't create user because the user exists"}

            user = driver.createUser(headers['username'], headers['password'])
            return {"status": "user created", "user": user.__dict__}
    except KeyError:
        return {"error": 400, "message": "missing required headers (username, password)"}, 400


@app.route('/podcast/<name>')
def podcast(name):
    filenames = next(os.walk('Podcasts'), (None, None, []))[2]
    if name in filenames:
        return send_file(getPodcastPath(name))
    return jsonify({"error": 404, "message": "no file found"}), 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, threaded=True)
