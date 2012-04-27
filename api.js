;(function () {

function callback(call, cb) {
	call.success(function (json) { cb(0, json); }).error(function (err) { cb(err, null); });
}

// API object

var Api = {

	getUser: function (username, cb) {
		callback($.get('/api/users/' + username), cb)
	},

	getBind: function (id, cb) {
		callback($.get('/api/binds/' + id), cb)
	},

	getPlace: function (id, cb) {
		callback($.get('/api/places/' + id), cb)
	},
	
	getPositions: function (cb) {
		callback($.get('/api/positions/'), cb)
	},

	getPlaces: function (cb) {
		callback($.get('/api/places/'), cb)
	}
};

this.Api = Api;

})();