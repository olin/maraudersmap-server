$(function () {

  var queryDict = parseQuery(window.location.search);
  console.log(queryDict);

  // Get the image height as soon as the image loads
  var imgWidth;
  var imgHeight;
  $('#map-img').on('load', function () {
    imgWidth = $('#map-img').width();
    imgHeight = $('#map-img').height();

    $('#size').text(imgWidth + " X " + imgHeight);
  })

  // Put user icons at the locations of mouse clicks on mouseclick on the map image
  $('#map-img').mousedown(function(eventObject) {
    var mouseX = eventObject.pageX - $('#map-img').offset().left;
    var mouseY = eventObject.pageY - $('#map-img').offset().top;
    addUserIcon(mouseX, mouseY);
  });

  Api.getPositions(function (err, json) {
    var positions = json.positions;
    console.log(positions);
    for (var i=0; i < positions.length; i++) {
      Api.getBind(positions[i].bind, function (err, json) {
        var bind = json.bind;
        addUserIcon(bind.x*imgWidth, bind.y*imgHeight);
      });
    }
  });


})

function addUserIcon(x, y) {
  var user = document.createElement('img');
  $(user).prop({'class': 'user', 'alt': 'Julian', 'src': 'Feet Raster.png'});
  $(user).on('load', function () {
      var userPosX = x - user.width/2.0;
      var userPosY = y - user.height/2.0;
      $(user).css({'left': userPosX, 'top': userPosY}).appendTo($('#map'));
  });
}

// Function from https://github.com/voituk/Misc/blob/master/js/hash.js
function parseQuery(str, separator) {
		separator = separator || '&'
		var obj = {}
		if (str.length == 0)
			return obj
		var c = str.substr(0,1)
		var s = c=='?' || c=='#'  ? str.substr(1) : str;

		var a = s.split(separator)
		for (var i=0; i<a.length; i++) {
			var p = a[i].indexOf('=')
			if (p < 0) {
				obj[a[i]] = ''
				continue
			}
			var k = decodeURIComponent(a[i].substr(0,p)),
				v = decodeURIComponent(a[i].substr(p+1))

			var bps = k.indexOf('[')
			if (bps < 0) {
				obj[k] = v
				continue;
			}

			var bpe = k.substr(bps+1).indexOf(']')
			if (bpe < 0) {
				obj[k] = v
				continue;
			}

			var bpv = k.substr(bps+1, bps+bpe-1)
			var k = k.substr(0,bps)
			if (bpv.length <= 0) {
				if (typeof(obj[k]) != 'object') obj[k] = []
				obj[k].push(v)
			} else {
				if (typeof(obj[k]) != 'object') obj[k] = {}
				obj[k][bpv] = v
			}
		}
		return obj;

}

