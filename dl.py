from pathlib import Path
from functools import wraps

from flask import Flask, send_from_directory, request, abort, redirect, url_for, Response
from flask_sslify import SSLify
from werkzeug.utils import secure_filename

from datetime import datetime, timedelta
import os
import uuid
import redis
import jwt
import uuid
import json
import pika

app = Flask(__name__)
app.config.from_pyfile('config.cfg', silent=True)

if not app.debug:
    sslify = SSLify(app)
    app.config['SESSION_COOKIE_SECURE'] = True

app.config.from_pyfile('config.cfg', silent=True)

app.upload_path = Path('./uploads').resolve()

r = redis.StrictRedis(charset="utf-8", decode_responses=True)
redis_f = "dryjah:files:{}"
redis_shared = "dryjah:shared"

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.exchange_declare(exchange="direct-dryjah", exchange_type="direct")


def generate_jwt():
    iat = datetime.utcnow()
    exp = iat + timedelta(seconds=300)
    payload = {'exp': exp, 'iat': iat, 'id': request.user['id']}
    return jwt.encode(
        payload, app.secret_key, algorithm='HS256').decode('utf8')


def jwt_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'jwt_token' in request.form:
            token = request.form['jwt_token']
        else:
            if 'jwt' in kwargs:
                token = kwargs['jwt']
            else:
                abort(401)

        try:
            payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            abort(401, "Signature has expired")
        if 'id' in payload:
            id = payload['id']
        else:
            abort(401, "Id not found in token.")
        setattr(request, 'user', {})

        request.user['id'] = id

        files = r.lrange(redis_f.format(id), 0, -1)
        request.user['files'] = [
            single_file.split(';', maxsplit=1) for single_file in files
        ]

        return f(*args, **kwargs)

    return wrapper


@app.route("/status/<string:jwt>")
@jwt_required
def status_update(jwt):
    out = []
    for single_f in request.user['files']:
        d = {
            'id': single_f[0],
            'name': single_f[1],
            'shared': r.hexists(redis_shared, single_f[0])
        }
        out.append(d)
    return json.dumps({'new_jwt': generate_jwt(), 'files': out})


@app.route("/storage", methods=['POST'])
@jwt_required
def upload():
    files = request.user['files']
    if len(files) >= 5:
        return "You cannon upload more than 5 files.", 403
    if 'file' not in request.files:
        return "File field is required", 400

    f = request.files['file']
    filename = secure_filename(f.filename)
    file_hash = str(uuid.uuid4())
    q = app.upload_path / file_hash
    while q.exists():
        file_hash = str(uuid.uuid4())
        q = app.upload_path / file_hash
    q = str(q)
    f.save(q)
    filepair = file_hash + ";" + filename
    r.lpush(redis_f.format(request.user['id']), filepair)

    if filename.rsplit('.', 1)[1].lower() in ['jpg', 'jpeg', 'png']:
        channel.queue_declare(queue='dryjah-pictures', durable=True)
        channel.basic_publish(
            exchange="direct-dryjah", routing_key='pictures', body=q)

    request.user['files'].append((file_hash, filename))
    return redirect('/dryjah/app/files')


@app.route("/storage/<uuid:filehash>/<string:jwt>")
@jwt_required
def download(filehash, jwt):
    files = request.user['files']
    filehash = str(filehash)

    for file_obj in files:
        if filehash == file_obj[0]:
            q = app.upload_path / filehash
            if q.exists():
                return send_from_directory(
                    str(app.upload_path),
                    filehash,
                    as_attachment=True,
                    attachment_filename=file_obj[1])
            else:
                abort(404, "File not found")
    abort(404, "File not found")


@app.route("/share/<uuid:filehash>/<string:jwt>")
@jwt_required
def share(filehash, jwt):
    files = request.user['files']
    filehash = str(filehash)

    for file_obj in files:
        if filehash == file_obj[0]:
            q = app.upload_path / filehash
            if q.exists():
                r.hset(redis_shared, filehash, file_obj[1])
                return redirect('/dryjah/app/files')
            else:
                abort(404, "File not found")
    abort(404, "File not found")


@app.route("/shared/<uuid:filehash>")
def download_shared(filehash):
    filehash = str(filehash)
    is_shared = r.hexists(redis_shared, filehash)
    if is_shared:
        name = r.hget(redis_shared, filehash)
        q = app.upload_path / filehash
        if q.exists():
            return send_from_directory(
                str(app.upload_path),
                filehash,
                as_attachment=True,
                attachment_filename=name)
    abort(404, "File not found")


if __name__ == "__main__":
    app.run(host='0.0.0.0')
