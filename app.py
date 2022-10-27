__author__ = "Mikail Gündüz"
__version__ = "0.0.1"

from flask import Flask, request, send_file, jsonify, abort
from flask_httpauth import HTTPBasicAuth
from db import Driver, get_podcast_path
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
auth = HTTPBasicAuth()
driver = Driver(path="./users.json")


# ------------ AUTH ------------
@auth.get_user_roles
def get_user_roles(user):
    return user.roles


@auth.verify_password
def verify_password(username, password):
    user = driver.get_user(username)
    if user != None and check_password_hash(user.password, password):
        return user


# ----------- ROUTES -----------
@app.route('/', methods=['GET'])
@auth.login_required(role='user')
def home():
    return 'logged in as {}'.format(auth.current_user().username)
    # return send_file('./YKWIM.mp3')


@app.route('/user/all', methods=['GET'])
@auth.login_required(role='admin')
def all_users():
    return driver.all_users()


@app.route('/user/create', methods=['POST'])
@auth.login_required(role='admin')
def create_user():
    body = request.json
    try:
        if body["username"] is not None and body["password"] is not None:
            if driver.user_exists(body['username']):
                return {"status": "user exists", "message": "can't create user because the user exists"}

            user = driver.create_user(body['username'], body['password'])
            return {"status": "user created", "user": user.__dict__}
    except KeyError:
        return {"error": 400, "message": "missing required data (username, password)"}, 400

@app.route('/user/delete', methods=['DELETE'])
@auth.login_required(role='admin')
def delete_user():
    args = request.args

    try:
        username = args['username']
    except KeyError:
        return {"error": "400", "message": "missing required headers (username)"}, 400

    if driver.delete_user(username) == 1:
        return {"status": "no user found", "message": "no user to delete"}, 404
    return {"status": "deleted user", "message": "user {} was deleted".format(username)}

@app.route('/podcast/episode/<name>', methods=['GET'])
def podcast(name):
    filenames = next(os.walk('Podcasts/Audios/'), (None, None, []))[2]
    if name in filenames:
        return send_file(get_podcast_path(name))
    return jsonify({"error": 404, "message": "no file found"}), 404

@app.route('/podcast/create', methods=['POST'])
@auth.login_required()
def create_podcast():
    body = request.json

    if driver.podcast_exists(auth.current_user().username, body.get('title')):
        return {"status": "podcast exists",
                    "message": "The podcast already exists. Please create one with different title."}

    try:
        driver.create_podcast(auth.current_user().username,
                              body['title'],
                              body['link'],
                              body['description'],
                              body['language'],
                              body['author'],
                              body['image'],
                              body['explicit'],
                              body['category'])
        return {"status": "successful", "message": "created the podcast for {}".format(auth.current_user().username)}
    except KeyError:
        return {"error": "400", "message": "missing required data"}, 400

@app.route('/episode/create', methods=['POST'])
@auth.login_required(role='user')
def create_episode():
    data = request.json
    try:
        status = driver.add_episode(auth.current_user().username, data)
        if status == 1:
            return {"status": "failed", "message": "podcast doesn't exist"}
        if status == 2:
            return {"status": "failed", "message": "episode already exists"}
        return {"status": "successful", "message": "created the episode for {}".format(auth.current_user().username)}
    except KeyError:
        return {"error": "400", "message": "missing required data"}, 400

#delete episode
@app.route('/episode/delete', methods=['DELETE'])
@auth.login_required(role='user')
def delete_episode():
    try:
        data = request.json
        if driver.delete_episode(auth.current_user().username, data.get('pod_title'), data.get('ep_title')):
            return {"status": "successful", "message": "episode was deleted"}
        return {"status": "failed", "message": "episode doesn't exist"}
    except KeyError:
        return {"error": "400", "message": "missing required data (title)"}, 400


@app.route('/podcast/delete', methods=['DELETE'])
@auth.login_required(role='user')
def delete_podcast():
    try:
        data = request.json
        status = driver.delete_podcast(username=auth.current_user().username, title=data['title'])
        if status:
            return {"status": "successful", "message": "podcast was deleted for {}".format(auth.current_user().username)}
        return {"status": "failed", "message": "no podcast with this title"}
    except KeyError:
        return {"error": "400", "message": "missing required data (title)"}

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, threaded=True)
