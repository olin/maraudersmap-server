var Api = {
	getPositions: function (cb) {
		$.get('/api/positions/')
			.success(function (json) { cb(0, json); }).error(function (err) { cb(err, null); })	
	},

	getUser: function (username, cb) {
		$.get('/api/users/' + username)
			.success(function (json) { cb(0, json); }).error(function (err) { cb(err, null); })	
	}
};