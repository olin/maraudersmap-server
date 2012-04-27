;(function () {

function callback(call, cb) {
	call.success(function (json) { cb(0, json); }).error(function (err) { cb(err, null); });
}

var Api = {
	getPositions: function (cb) {
		callback($.get('/api/positions/'), cb)
	},

	getUser: function (username, cb) {
		callback($.get('/api/users/' + username), cb)
	},

	getBind: function (id, cb) {
		callback($.get('/api/binds/' + id), cb)
	}
};

this.Api = Api;

})();