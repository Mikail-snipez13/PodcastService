__author__ = "Mikail Gündüz"
__version__ = "0.0.1"

import flask
from flask import Flask, request, send_file, jsonify, abort
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS, cross_origin
from db import Driver, get_podcast_path, get_config, get_image_path
import json
from werkzeug.security import generate_password_hash, check_password_hash
import os
import feed

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


@app.route('/user/me', methods=['GET'])
@auth.login_required(role='user')
def get_me():
    data = driver.get_user(auth.current_user().username).__dict__
    data['password'] = None
    return data


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


@app.route('/podcast/image/<name>', methods=['GET'])
def image(name):
    filenames = next(os.walk('Podcasts/Images/'), (None, None, []))[2]
    if name in filenames:
        return send_file(get_image_path(name))
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


# delete episode
@app.route('/episode/delete', methods=['DELETE'])
@auth.login_required(role='user')
def delete_episode():
    try:
        data = request.json
        if driver.delete_episode(auth.current_user().username, data.get('pod_title'), data.get('ep_title')):
            return {"status": "successful", "message": "episode was deleted"}
        return {"status": "failed", "message": "episode doesn't exist"}, 404
    except KeyError:
        return {"error": "400", "message": "missing required data (title)"}, 400


@app.route('/podcast/delete', methods=['DELETE'])
@auth.login_required(role='user')
def delete_podcast():
    try:
        data = request.json
        status = driver.delete_podcast(username=auth.current_user().username, title=data['title'])
        if status:
            return {"status": "successful",
                    "message": "podcast was deleted"}
        return {"status": "failed", "message": "no podcast with this title"}, 404
    except KeyError:
        return {"error": "400", "message": "missing required data (title)"}, 400


@app.route('/podcast/update', methods=['PUT'])
@auth.login_required(role='user')
def update_podcast():
    try:
        data = request.json
        status = driver.update_podcast(auth.current_user().username, data)
        if status:
            return {"status": "successful",
                    "message": "podcast was updated"}
        return {"status": "failed", "message": "no podcast found"}, 404
    except KeyError:
        return {"error": "400", "message": "missing required data"}, 400


@app.route('/episode/update', methods=['PUT'])
@auth.login_required(role='user')
def update_episode():
    try:
        data = request.json
        status = driver.update_episode(auth.current_user().username, data)
        if status:
            return {"status": "successful",
                    "message": "episode was updated"}
        return {"status": "failed", "message": "no episode found"}, 404
    except KeyError:
        return {"error": "400", "message": "missing required data"}, 400


@app.route('/<username>/<podcast>')
def get_feed(username, podcast):
    if username == "" or podcast == "":
        return {"error": "404", "message": "no feed on this url found"}, 404

    if not driver.podcast_exists(username, podcast):
        return {"error": "404", "message": "no podcast with this name found"}, 404
    p = driver.get_podcast(username, podcast)
    res = flask.Response(feed.get_feed(username, p))
    res.headers['Content-Type'] = "text/xml"
    return res


# works not the way I want (is a debug case)
@app.route('/episode/upload/audio', methods=['POST', 'GET'])
@auth.login_required(role='user')
def upload_audio():
    file = request.files['file']
    print(file.__dict__)
    return {"status": "success"}


if __name__ == '__main__':
    config = get_config()
    port = config['port']
    app.run(host="0.0.0.0", port=port, threaded=True)
