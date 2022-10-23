__author__ = "Mikail Gündüz"
__version__ = "0.0.1"

from flask import Flask, request, send_file, jsonify, abort
from flask_httpauth import HTTPBasicAuth
from db_driver import Driver
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
auth = HTTPBasicAuth()
driver = Driver(path="./users.json")


# ------------ Auth ------------
@auth.get_user_roles
def get_user_roles(user):
    return user['roles']

@auth.verify_password
def verify_password(username, password):
    user = driver.getUser(username)
    if user != None and check_password_hash(user['password'], password):
        return user

# ----------- ROUTES -----------
@app.route('/', methods=['GET'])
@auth.login_required(role='user')
def home():
    return 'logged in as {}'.format(auth.current_user()['username'])
    #return send_file('./YKWIM.mp3')

@app.route('/admin', methods=['GET'])
@auth.login_required(role='admin')
def admin():
    return driver.allUsers()

@app.route('/podcast/<name>')
def podcast(name):
    filenames = next(os.walk('Podcasts'), (None, None, []))[2]
    if name in filenames:
        return send_file(driver.getPodcastPath(name))
    return jsonify({"error": 204, "message": "no file found"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, threaded=True)
