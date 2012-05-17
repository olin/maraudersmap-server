from pymongo import Connection, ASCENDING, DESCENDING
from bson.code import Code
from bson.objectid import ObjectId

#mongodb_uri = "mongodb://localhost:27017/"
#db_name = 'maumap'
#mongodb_uri = "mongodb://:31867"
#db_name = 'heroku_app3954850'

connection = Connection("ds031867.mongolab.com", 31867)
db = connection["heroku_app3954850"]
db.authenticate("heroku_app3954850", "2o4lqlsq3mac57qj608kk8gbsp")

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
#"""

# Intermediate API
# ----------------

import json, re, numpy, copy, datetime, os
from operator import itemgetter
#from jsonpatch import JsonPatch, JsonPatchException

# Users
# post_user('tryan', 'Tim Ryan')

def __format_user(user):
	return {"username": user['username'], "alias": user['alias']}

def get_users(**crit):
	return [__format_user(user) for user in users.find(crit)]

def get_user(username):
	user = users.find_one({"username": username})
	if user:
		return __format_user(user)
	return None

def put_user(username, alias = ''):
	if not re.compile('^[a-zA-Z\.]+$').match(username):
		raise Exception("Invalid username: %s" % username)
	if get_user(username):
		delete_user(username)
	users.insert({"username": username, "alias": alias})
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

def put_place(id, floor, name, alias = ''):
	return places.update({"_id": id}, {
		"floor": floor,
		"name": name,
		"alias": alias
		})

def post_place(floor, name, alias = ''):
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
		"place": str(bind['place']),
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
		"signals": {k.lower(): v for k, v in signals.items()}})

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
                dist = numpy.dot(
			numpy.array([float(signalsA.get(k, 0)) for k in macs]),
			numpy.array([float(signalsB.get(k, 0)) for k in macs]))
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

from flask import Flask, jsonify, make_response, request, redirect, url_for
import fwolin, cgi
app = Flask(__name__, '/ui')

# Use fwol.in's unified authentication mechanism.
# This requires us to set an environment variable for this application
# to encrypt the user's session.
fwolin.enable_auth(app)
Flask.secret_key = os.environ.get('FLASK_SESSION_KEY', 'test-key-please-ignore')

@app.route("/")
def route_root():
	return redirect('/ui/index.html')

@app.route("/local/")
def route_local():
	try:
		port = str(int(request.args.get('port', '')))
	except Exception, e:
		return """<h1>Invalid port.</h1>"""

	return """
<h1>Authorizing local client...</h1>
<form id="auth" method="post" action="http://localhost:%s/">
<input type="hidden" name="browserid" value="%s">
<input type="hidden" name="session" value="%s">
<button type="submit">I'm impatient! Manually authorize me!</button>
</form>
<script>
document.getElementById('auth').submit()
</script>
""" % (cgi.escape(port),
	cgi.escape(request.cookies.get('browserid', '')),
	cgi.escape(request.cookies.get('session', '')))

# REST API
# --------

def json_error(code, msg):
	response = make_response(json.dumps({"error": 404, "message": msg}), 404)
	response.headers['Content-Type'] = 'application/json'
	return response

def json_content(code = 200, **kargs):
	response = make_response(json.dumps(kargs), code)
	response.headers['Content-Type'] = 'application/json'
	return response

@app.route("/api/")
def route_index():
	return jsonify(binds='/binds/', users='/users', places='/places/', positions='/positions/')

# Users

@app.route("/api/users/", methods=['GET'])
def route_users():
	if request.method == 'GET':
		return jsonify(users=get_users())

@app.route("/api/users/<username>", methods=['GET', 'PUT', 'DELETE'])
def route_user(username):
	if request.method == 'PUT':
		username = request.form['username']
		alias = request.form.get('alias', '')
		put_user(username, alias)
		return jsonify(user=get_user(username))

	user = get_user(username)
	if not user:
		return json_error(404, 'User with name %s not found.' % username)

	if request.method == 'GET':
		return jsonify(user=user)

	#if request.method == 'PATCH':
	#	patch = JsonPatch(request.json)
	#	obj = patch.apply(get_user(username))
	#	put_user(obj['username'], obj.get('alias', ''))
	#	return jsonify(user=get_user(obj['username']))

	if request.method == "DELETE":
		delete_user(username)
		return '', 204

# Places

@app.route("/api/places/", methods=['GET', 'POST'])
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
		return json_content(201, place=get_place(id))

@app.route("/api/places/<id>", methods=['GET', 'PUT', 'DELETE'])
def route_place(id):
	place = get_place(ObjectId(id))
	if not place:
		return json_error(404, 'Place with id %s not found.' % id)

	if request.method == 'GET':
		return jsonify(place=place)

	if request.method == 'PUT':
		put_place(ObjectId(id),
			request.form['floor'],
			request.form['name'],
			request.form.get('alias', ''))
		return json_content(200, place=get_place(ObjectId(id)))

	#if request.method == 'PATCH':
	#	patch = JsonPatch(request.json)
	#	obj = patch.apply(get_place(ObjectId(id)))
	#	put_place(ObjectId(id), obj['name'], obj['floor'], obj.get('alias', ''))
	#	return jsonify(place=get_place(ObjectId(id)))

	if request.method == "DELETE":
		delete_place(ObjectId(id))
		return '', 204

# Binds

@app.route("/api/binds/", methods=['GET', 'POST'])
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
		username = request.form['username']
		place = request.form['place']
		x = float(request.form['x'])
		y = float(request.form['y'])
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
		return json_content(201, bind=get_bind(id))

@app.route("/api/binds/<id>", methods=['GET', 'DELETE'])
def route_bind(id):
	bind = get_bind(ObjectId(id))
	if not bind:
		return json_error(404, 'Bind with id %s not found.' % id)

	if request.method == 'GET':
		return jsonify(bind=bind)

	if request.method == "DELETE":
		delete_bind(ObjectId(id))
		return '', 204

# Positions

@app.route("/api/positions/", methods=['GET', 'POST'])
def route_positions():
	if request.method == 'GET':
		critkeys = ['username', 'bind']
		crit = {key: request.args[key] for key in list(set(critkeys) & set(request.args.keys()))}
		return jsonify(positions=get_positions(request.args.has_key('history'), request.args.has_key('extended'), **crit))

	if request.method == 'POST':
		username = request.form['username']
		bind = request.form['bind']
		if not get_user(username):
			return json_error(400, 'User with name %s does not exist.' % username)
		if not get_bind(ObjectId(bind)):
			return json_error(400, 'Bind with id %s does not exist.' % bind)
		id = post_position(username, ObjectId(bind))
		return json_content(201, position=get_position(id))

@app.route("/api/positions/<id>", methods=['GET', 'DELETE'])
def route_position(id):
	position = get_position(ObjectId(id))
	if not position:
		return json_error(404, 'Position with id %s not found.' % id)

	if request.method == 'GET':
		return jsonify(position=position)

	if request.method == "DELETE":
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
