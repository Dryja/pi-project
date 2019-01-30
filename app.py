import json
import redis
import uuid
import os
import jwt
import urllib

from flask import Flask, Blueprint, redirect, url_for, render_template, session, request, abort, send_from_directory
from flask_sslify import SSLify
from authlib.flask.client import OAuth
from werkzeug.utils import secure_filename
from werkzeug.wsgi import DispatcherMiddleware
from functools import wraps
from pathlib import Path
from datetime import timedelta, datetime

app = Flask(__name__, static_url_path='/static')
app.config.from_pyfile('config.cfg', silent=True)
if not app.debug:
    sslify = SSLify(app)
    app.config['SESSION_COOKIE_SECURE'] = True

app.upload_path = Path('./uploads')

oauth = OAuth(app)
auth0 = oauth.register(
    'auth0',
    client_id=app.config['CLIENT_ID'],
    client_secret=app.config['CLIENT_SECRET'],
    api_base_url=app.config['API_BASE_URL'],
    access_token_url=app.config['ACCESS_TOKEN_URL'],
    authorize_url=app.config['AUTHORIZE_URL'],
    client_kwargs={
        'scope': 'openid profile',
    },
)

r = redis.StrictRedis(charset="utf-8", decode_responses=True)
redis_f = "dryjah:files:{}"
redis_shared = "dryjah:shared"


def session_user_data():
    if 'profile' not in session or 'user_id' not in session['profile']:
        return None
    if 'name' not in session['profile']:
        return None

    setattr(request, 'user', {})

    request.user['id'] = session['profile']['user_id']
    request.user['name'] = session['profile']['name']

    files = r.lrange(redis_f.format(session['profile']['user_id']), 0, -1)
    request.user['files'] = [
        single_file.split(';', maxsplit=1) for single_file in files
    ]

    return request.user


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session_user_data() is None:
            abort(401)
        return f(*args, **kwargs)

    return wrapper


def generate_jwt():
    iat = datetime.utcnow()
    exp = iat + timedelta(seconds=300)
    payload = {'exp': exp, 'iat': iat, 'id': request.user['id']}
    return jwt.encode(
        payload, app.secret_key, algorithm='HS256').decode('utf8')


@app.route("/")
def home():
    session_user_data()
    return render_template('home.html')


@app.route('/callback')
def callback_handling():
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    session['jwt_payload'] = userinfo
    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture']
    }

    return redirect(url_for('files_list'))


@app.route("/login")
def login():
    if 'profile' in session:
        return redirect(url_for('files_list'))
    return auth0.authorize_redirect(
        redirect_uri=url_for('callback_handling', _external=True),
        audience='https://pobieranko.eu.auth0.com/userinfo')


@app.route("/logout")
@login_required
def logout():
    session.clear()

    params = {
        'returnTo': url_for('home', _external=True),
        'client_id': app.config['CLIENT_ID']
    }
    return redirect(auth0.api_base_url + '/v2/logout?' +
                    urllib.parse.urlencode(params))


@app.route("/files")
@login_required
def files_list():
    files = request.user['files']
    shared_keys = r.hkeys(redis_shared)
    files_keys = frozenset(f[0] for f in files)
    return render_template(
        'files_list.html',
        files_len=len(files),
        files=files,
        jwt=generate_jwt(),
        shared_keys=files_keys.intersection(shared_keys))


@app.route("/file", methods=['GET', 'POST'])
@login_required
def file_add():
    files_len = len(request.user['files'])
    return render_template(
        'file.html', files_len=files_len, jwt=generate_jwt())


if __name__ == "__main__":
    app.run(host='0.0.0.0', ssl_context='adhoc')
