from pymongo import Connection, ASCENDING, DESCENDING
from bson.objectid import ObjectId

connection = Connection('localhost', 27017)
db = connection.maumap

users = db.users
binds = db.binds
places = db.places
positions = db.position

users.create_index("username", unique=True)
positions.create_index("username", unique=True)

# Intermediate API
# ----------------

import json, re, numpy, copy
from operator import itemgetter

# Users
# post_user('tryan', 'Tim Ryan')

def __format_user(user):
	return {"username": user['username'], "alias": user['alias']}

def get_users(crit = {}):
	return [__format_user(user) for user in users.find()]

def get_user(username):
	user = users.find_one({"username": username})
	if user:
		return __format_place(user)
	return None

def post_user(username, alias = ''):
	if not re.compile('^[a-z]+$').match(username):
		raise Exception("Invalid username: %s" % username)
	users.insert({"username": username, "alias": alias})
	return username

def delete_user(username):
	users.remove({"username": username})

# Places
# post_place('EH4', 'Room 419', 'The Sky Fortress')

def __format_place(loc):
	return {"id": str(loc['_id'])}

def get_places(crit = {}):
	return [__format_place(loc) for loc in places.find()]

def get_place(id):
	loc = places.find_one(id)
	if loc:
		return __format_place(loc)
	return None

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

def get_binds(crit = {}):
	return [str(bind['_id']) for bind in binds.find(crit)]

def get_bind(id):
	bind = binds.find_one(id)
	if bind:
		return __format_bind(bind)
	return None

def post_bind(username, place, x, y, signals):
	return binds.insert({"username": username,
		"place": place,
		"x": x,
		"y": y,
		"signals": signals})

def match_bind(signalsA, limit = 10):
	qu = {}
	for k, v in signalsA.items():
		qu['signals.' + k] = {"$exists": True}

	matches = []
	for bind in binds.find(qu):
		signalsB = bind['signals']

		macs = set(signalsA.keys())
		macs.update(signalsB.keys())
		dist = numpy.linalg.norm(numpy.array([signalsA.get(k, 0) for k in macs]) -
			numpy.array([signalsB.get(k, 0) for k in macs]))
		matches.append((dist, bind))

	return [__format_bind(x[1]) for x in sorted(matches, key=itemgetter(0))[0:limit]]

# Positions
# post_position('tryan', loc_id)

def __format_position(pos):
	return {'username': pos['username'], "location": str(pos['location'])}

def get_positions(crit = {}):
	return [__format_position(pos) for pos in positions.find()]

def get_position(username):
	pos = positions.find_one({"username": username})
	if pos:
		return __format_position(pos)
	return None

def put_position(username, location):
	if get_position(username):
		delete_position(username)
	return positions.insert({
		"username": username,
		"location": location
		})

def delete_position(username):
	positions.remove({"username": username})

# REST API
# --------

from flask import Flask

# Testing
# -------

binds.drop()
users.drop()
places.drop()
positions.drop()

p1 = post_place('AC4', 'Room 419', 'Sky Fortress')
p2 = post_place('AC2', 'Room 219', 'The Aqualab')

u1 = post_user('tryan', 'Tim Ryan')

b1 = post_bind('tryan', p1, 0, 0, {"A": 10, "B": 5, "C": 0, "D": 0})
b2 = post_bind('tryan', p1, 0, 0, {"A": 5, "B": 10, "C": 5})
b3 = post_bind('tryan', p1, 0, 0, {"A": 0, "B": 5, "C": 10, "E": 0})

print "Closest bind matching:"
print json.dumps(match_bind({"A": 9, "B": 6, "C": 1})[0]['place'])

put_position('tryan', p1)
put_position('tryan', p2)

print "Current user location:"
print json.dumps(get_position('tryan'))
print json.dumps(get_positions())