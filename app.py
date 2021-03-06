import os
from urlparse import urlsplit
from pymongo import Connection, ASCENDING, DESCENDING
from bson.code import Code
from bson.objectid import ObjectId
# from flask.ext.olinauth import OlinAuth, auth_required, current_user, get_current_user
from flask.ext.jsonpify import jsonify
import requests

MONGO_URL = os.getenv('MONGOLAB_URI', "mongodb://localhost:27017/maumap")
parsed_mongo = urlsplit(MONGO_URL)
db_name = parsed_mongo.path[1:]
# Get your DB
print('Connecting to %s [db %s]' % (MONGO_URL, db_name))
db = Connection(MONGO_URL)[db_name]
# Authenticate
if '@' in MONGO_URL:
    user_pass = parsed_mongo.netloc.split('@')[0].split(':')
    db.authenticate(user_pass[0], user_pass[1])

# Shortcuts for collections.
users = db.users
binds = db.binds
places = db.places
positions = db.positions

"""
binds.drop()
users.drop()
places.drop()
positions.drop()

users.create_index("username", unique=True)
"""

# Intermediate API
# ----------------

import re
import numpy
import copy
import datetime
import os
from operator import itemgetter


# Users

def get_current_username():
    user = get_current_user()
    if user:
        return user['id']
    return None

# post_user('tryan', 'Tim Ryan')
def __format_user(user):
    return {"username": user['username'], "email": user['email'], "alias": user['alias']}


def get_users(**crit):
    return [__format_user(user) for user in users.find(crit)]


def get_user(username):
    user = users.find_one({"username": username})
    if user:
        return __format_user(user)
    return None


def get_user_by_email(email):
    user = users.find_one({"email": email})
    if user:
        return __format_user(user)
    return None


def put_user(username, email, alias=''):
    if not re.compile('^[a-zA-Z\.]+$').match(username):
        raise Exception("Invalid username: %s" % username)
    if get_user(username):
        delete_user(username)
    users.insert({"username": username, "email": email, "alias": alias})
    return username


def delete_user(username):
    users.remove({"username": username})


# Places
# post_place('EH4', 'Room 419', 'The Sky Fortress')
def __format_place(loc):
    return {"id": str(loc['_id']), "floor": loc['floor'], "name": loc['name'], "alias": loc['alias']}


def get_places(**crit):
    return [__format_place(place) for place in places.find(crit)]


def get_place(id):
    loc = places.find_one(id)
    if loc:
        return __format_place(loc)
    return None


def put_place(id, floor, name, alias=''):
    return places.update({"_id": id}, {
        "floor": floor,
        "name": name,
        "alias": alias
        })


def post_place(floor, name, alias=''):
    return places.insert({
        "floor": floor,
        "name": name,
        "alias": alias
        })


def delete_place(id):
    places.remove(id)


# Binds
def __format_bind(bind):
    return {"id": str(bind['_id']),
        "username": bind['username'],
        "place": get_place(bind['place']),
        "x": bind['x'],
        "y": bind['y'],
        "signals": bind['signals']
        }


def get_binds(**crit):
    return [__format_bind(bind) for bind in binds.find(crit)]


def get_bind(id):
    bind = binds.find_one(id)
    if bind:
        return __format_bind(bind)
    return None


def post_bind(username, place, x, y, signals):
    return binds.insert({"username": username,
        "place": place,
        "x": float(x),
        "y": float(y),
        "signals": {k.lower(): v for k,v in signals.items()}
        })

def delete_bind(id):
    binds.remove(id)

# Dot product between two signal vectors (union of routers)
def nearest_binds(signals, limit = 10, **crit):
    signalsA = {k.lower(): v for k, v in signals.items()}
    crit['$or'] = []
    for k, v in signalsA.items():
        crit['$or'].append({('signals.%s' % k): {"$exists": True}})

    matches = []
    for bind in binds.find(crit):
        signalsB = bind['signals']

        macs = set(signalsA.keys()).union(signalsB.keys())
        pt1 = numpy.array([float(signalsA.get(k, 0)) for k in macs])
        pt2 = numpy.array([float(signalsB.get(k, 0)) for k in macs])

        dist = numpy.dot(
            pt1/ numpy.linalg.norm(pt1),
            pt2/ numpy.linalg.norm(pt2))
        matches.append((dist, bind))

    return [__format_bind(x[1]) for x in sorted(matches, key=itemgetter(0), reverse=True)[0:limit]]

# Positions
# post_position('tryan', loc_id)

def __format_position(pos, extended=False):
    if extended:
        bind = binds.find_one(pos['bind'])
        place = places.find_one(bind['place'])
        return {
            "id": str(pos['_id']), 'username': pos['username'], "date": pos['date'].isoformat(), "bind": str(pos['bind']),
            "extended": {
                "bind": __format_bind(bind),
                "place": __format_place(place)
            }
        }
    else:
        return {"id": str(pos['_id']), 'username': pos['username'], "bind": str(pos['bind']), "date": pos['date'].isoformat()}

def get_positions(history=False, extended=False, **crit):
    if history:
        return [__format_position(pos) for pos in positions.find(crit)]
    else:
        try:
            map = Code("""
function () {
    emit(this.username, this)
}
""")
            reduce = Code("""
function (key, values) {
    var newest;
    for (var i = 0; i < values.length; i++) {
        if (!newest || values[i].date > newest.date)
            newest = values[i]
    }
    return newest
}
""")
            col = positions.map_reduce(map, reduce, 'current_positions', query=crit)
            return [__format_position(v['value'], extended) for v in col.find()]
        except Exception as e:
            print 'Error: %s' % e
            return []

def get_position(id):
    pos = positions.find_one(id)
    if pos:
        return __format_position(pos)
    return None

def put_position(id, username, bind):
    return positions.update({"_id": id}, {
        "date": datetime.datetime.now(),
        "username": username,
        "bind": bind
        })

def post_position(username, bind):
    return positions.insert({
        "username": username,
        "bind": bind,
        "date": datetime.datetime.now()
        })

def delete_position(username):
    positions.remove({"username": username})

# Server
# ------

if 'PORT' in os.environ:
    HOSTNAME = 'map.olinapps.com'
    HOST = 'map.olinapps.com'
else:
    HOSTNAME = 'localhost'
    HOST = 'localhost:5000'

from flask import Flask, make_response, request, redirect, url_for, escape, Response, session
app = Flask(__name__, '/ui')

Flask.secret_key = os.environ.get('FLASK_SESSION_KEY', 'test-key-please-ignore')

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper


def is_authorized_for(username):
    return (get_current_user().get('id') == username) or (get_current_user().get('id') in get_admin_users())


@app.route("/")
def route_root():
    return redirect('/ui/index.html')

# Authentication temporarily
# --------------------

from urlparse import urlparse

def load_session(sessionid):
    r = requests.get('http://olinapps.com/api/me', params={"sessionid": sessionid})
    try:
        js = r.json()
        if r.status_code == 200 and 'user' in js:
            session['sessionid'] = sessionid
            session['user'] = js['user']
            return True
    except:
        print "Error: Json could not be decoded from api/me."
    return False

def get_current_user():
    return session.get('user')

def get_session_email():
    userinfo = get_current_user()
    if not userinfo:
        return None
    return str(userinfo['id']) + '@' + str(userinfo['domain'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # External login.
        if request.form.has_key('sessionid') and load_session(request.form.get('sessionid')):
            return redirect('/')
        else:
            session.pop('sessionid', None)
            return "Invalid session token: %s" % sessionid
    return "Please authenticate with Olin Apps to view Directory."

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('sessionid', None)
    session.pop('user', None)
    return redirect('/')

# All pages are accessible, but enable user accounts.
@app.before_request
def before_request():
    if urlparse(request.url).path == '/login':
        return
    if not get_current_user():
        if request.args.has_key('sessionid') and load_session(request.args.get('sessionid')):
            return
        if urlparse(request.url).path.startswith('/api/'):
            return Response(json.dumps({"error": "Not authorized"}), 401, {"Content-Type": "application/json"})
        return redirect('http://olinapps.com/external?callback=http://%s/login' % HOST)

@app.after_request
def after_request(response):
    if urlparse(request.url).path.startswith('/api/') and request.headers.get('Origin'):
        remotehost = urlparse(request.headers.get('Origin')).netloc
        if re.match(r'^localhost:[0-9]+$', remotehost) or re.match(r'^[^.]+\.olinapps\.com', remotehost):
            response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin'))
        response.headers.add('Access-Control-Allow-Methods', 'POST, GET, PUT, PATCH, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-Requested-With, Cookie')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '1728000')
    return response


# REST API
# --------

def json_error(code, msg):
    return jsonify(error=code, message=msg), code


# Login
def get_admin_users():
    # TODO: XXX: This should be a legitimate database lookup
    return ['julian.ceipek', 'timothy.ryan', 'william.dolphin']


@app.route("/api/me/", methods=['GET', 'OPTIONS'])
#@auth_required
def route_me():
    # TODO: XXX: fwolin/api/me returns an object now, this should too really.
    return jsonify(user=get_current_user()), 200


# Entry point
@app.route("/api/")
def route_index():
    return jsonify(binds='/binds/', users='/users', places='/places/', positions='/positions/')


# Users
@app.route("/api/users/", methods=['GET', 'OPTIONS'])
#@auth_required
def route_users():
    if request.method == 'GET':
        return jsonify(users=get_users())


@app.route("/api/users/<username>/", methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])
#@auth_required
def route_user(username):
    if request.method == 'PUT':
        if not is_authorized_for(username):
            return json_error(401, "Only %s and admins can add a new user with the username %s. You are %s." % (username, username, get_current_username()))
        alias = request.form.get('alias', '')
        email = request.form.get('email', '')
        put_user(username, email, alias)
        return jsonify(user=get_user(username))

    user = get_user(username)
    if not user:
        return json_error(404, 'User with name %s not found.' % username)

    if request.method == 'GET':
        return jsonify(user=user)

    #if request.method == 'PATCH':
    #   patch = JsonPatch(request.json)
    #   obj = patch.apply(get_user(username))
    #   put_user(obj['username'], obj.get('alias', ''))
    #   return jsonify(user=get_user(obj['username']))

    if request.method == "DELETE":
        # XXX: There may be a more efficient way to do this
        existing_user = get_user(username)
        if existing_user and not is_authorized_for(username):
            return json_error(401, "Only %s and admins can delete a user with the username %s. You are %s." % (username, username, get_current_username()))

        delete_user(username)
        return '', 204


# Places
@app.route("/api/places/", methods=['GET', 'POST', 'OPTIONS'])
#@auth_required
def route_places():
    if request.method == 'GET':
        critkeys = ['alias', 'floor', 'name', 'alias']
        crit = {key: request.args[key] for key in list(set(critkeys) & set(request.args.keys()))}
        return jsonify(places=get_places(**crit))

    if request.method == 'POST':
        floor = request.form['floor']
        name = request.form['name']
        alias = request.form.get('alias', '')
        id = post_place(floor, name, alias)
        return jsonify(place=get_place(id)), 201


@app.route("/api/places/<id>", methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])
#@auth_required
def route_place(id):
    place = get_place(ObjectId(id))
    if not place:
        return json_error(404, 'Place with id %s not found.' % id)

    if request.method == 'GET':
        return jsonify(place=place)

    if request.method == 'PUT':
        # TODO: Tim, should places also be associated with the person who created them (so that he/she can delete them as well?)
        put_place(ObjectId(id),
            request.form['floor'],
            request.form['name'],
            request.form.get('alias', ''))
        return jsonify(place=get_place(ObjectId(id))), 200

    #TODO:
    #if request.method == 'PATCH':
    #   patch = JsonPatch(request.json)
    #   obj = patch.apply(get_place(ObjectId(id)))
    #   put_place(ObjectId(id), obj['name'], obj['floor'], obj.get('alias', ''))
    #   return jsonify(place=get_place(ObjectId(id)))

    if request.method == "DELETE":
        if get_current_username() in get_admin_users():
            # TODO: Tim, should places also be associated with the person who created them (so that he/she can delete them as well?)
            delete_place(ObjectId(id))
            return '', 204


# Binds
@app.route("/api/binds/", methods=['GET', 'POST', 'OPTIONS'])
#@auth_required
def route_binds():
    if request.method == 'GET':
        critkeys = ['username', 'place', 'x', 'y']
        crit = {key: request.args[key] for key in list(set(critkeys) & set(request.args.keys()))}
        signals = {}
        for k, v in request.args.items():
            grp = re.match(r'^nearest\[(([a-f0-9]{2}:){5}[a-f0-9]{2})\]$', k.lower())
            if grp:
                signals[grp.group(1)] = float(v)

        if len(signals.keys()):
            return jsonify(binds=nearest_binds(signals, **crit))
        else:
            return jsonify(binds=get_binds(**crit))

    if request.method == 'POST':
        # The only reason you would want to set username explicitly is if you are an admin and want to post as a user
        username = None
        if not 'username' in request.form:
            username = get_current_username()
        else:
            username = request.form['username']

        # XXX: There may be a more efficient way to do this
        existing_user = get_user(username)
        if existing_user and not is_authorized_for(username):
            return json_error(401, "Only %s and admins can bind %s to a place. You are %s." % (username, username, get_current_username()))
        place = request.form['place']
        x = float(request.form['x'])
        y = float(request.form['y'])
        if x != x or y != y:
            return json_error(400, "Invalid (X,Y) coordinate.")
        signals = {}
        for k, v in request.form.items():
            grp = re.match(r'^signals\[(([a-f0-9]{2}:){5}[a-f0-9]{2})\]$', k.lower())
            if grp:
                signals[grp.group(1)] = float(v)
        if not get_user(username):
            return json_error(400, 'User with name %s does not exist.' % username)
        if not get_place(ObjectId(place)):
            return json_error(400, 'Place with id %s does not exist.' % place)
        id = post_bind(username, ObjectId(place), x, y, signals)
        return jsonify(bind=get_bind(id)), 201


@app.route("/api/binds/<id>", methods=['GET', 'DELETE', 'OPTIONS'])
#@auth_required
def route_bind(id):
    bind = get_bind(ObjectId(id))
    if not bind:
        return json_error(404, 'Bind with id %s not found.' % id)

    if request.method == 'GET':
        return jsonify(bind=bind)

    if request.method == "DELETE":
        # XXX: There may be a more efficient way to do this
        username = bind['username']
        existing_user = get_user(username)
        if existing_user and not is_authorized_for(username):
            return json_error(401, "Only %s and admins can add delete binds by %s! You are %s." % (username, username, get_current_username()))

        delete_bind(ObjectId(id))
        return '', 204


# Positions
@app.route("/api/positions/", methods=['GET', 'POST', 'OPTIONS'])
#@auth_required
def route_positions():
    if request.method == 'GET':
        critkeys = ['username', 'bind']
        crit = {key: request.args[key] for key in list(set(critkeys) & set(request.args.keys()))}
        return jsonify(positions=get_positions('history' in request.args, 'extended' in request.args, **crit))

    if request.method == 'POST':
        # The only reason you would want to set username explicitly is if you are an admin and want to post as a user
        username = None
        if not 'username' in request.form:
            username = get_current_username()
        else:
            username = request.form['username']
        bindid = request.form['bind']
        bind = get_bind(ObjectId(bindid))
        # XXX: There may be a more efficient way to do this
        existing_user = get_user(bind['username'])
        if existing_user and not is_authorized_for(username):
            return json_error(401, "Only %s and admins can add %s at a position! You are %s." % (username, username, get_current_username()))

        if not get_user(username):
            return json_error(400, 'User with name %s does not exist.' % username)
        if not bind:
            return json_error(400, 'Bind with id %s does not exist.' % bind)
        id = post_position(username, ObjectId(bindid))
        return jsonify(position=get_position(id)), 201


@app.route("/api/positions/<id>", methods=['GET', 'DELETE', 'OPTIONS'])
#@auth_required
def route_position(id):
    position = get_position(ObjectId(id))
    if not position:
        return json_error(404, 'Position with id %s not found.' % id)

    if request.method == 'GET':
        return jsonify(position=position)

    if request.method == "DELETE":
        # XXX: There may be a more efficient way to do this
        username = position['username']
        existing_user = get_user(username)
        if existing_user and not is_authorized_for(username):
            return json_error(401, "Only %s and admins can delete a position owned by %s! You are %s." % (username, username, get_current_username()))

        delete_position(username)
        return '', 204

# Testing
# -------

"""
p1 = post_place('AC4', 'Room 419', 'Sky Fortress')
p2 = post_place('AC2', 'Room 219', 'The Aqualab')

u1 = put_user('tryan', 'Tim Ryan')
u2 = put_user('kpletcher', 'Kendall Pletcher')

b1 = post_bind('tryan', p1, 0, 0, {"AA:AA:AA:AA:AA:AA": 10, "BB:BB:BB:BB:BB:BB": 5, "CC:CC:CC:CC:CC:CC": 0, "DD:DD:DD:DD:DD:DD": 0})
b2 = post_bind('tryan', p1, 0, 0, {"AA:AA:AA:AA:AA:AA": 5, "BB:BB:BB:BB:BB:BB": 10, "CC:CC:CC:CC:CC:CC": 5})
b3 = post_bind('tryan', p1, 0, 0, {"AA:AA:AA:AA:AA:AA": 0, "BB:BB:BB:BB:BB:BB": 5, "CC:CC:CC:CC:CC:CC": 10, "EE:EE:EE:EE:EE:EE": 0})

print "Closest bind matching:"
print json.dumps(nearest_binds({"AA:AA:AA:AA:AA:AA": 9, "BB:BB:BB:BB:BB:BB": 6, "CC:CC:CC:CC:CC:CC": 1})[0])

post_position('tryan', b1)
post_position('tryan', b2)
post_position('kpletcher', b2)

print "Current user location:"
print json.dumps(get_positions(True, username='tryan'))
print json.dumps(get_positions())
"""

# Launch

if __name__ == "__main__":

    
    app.debug = True
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
