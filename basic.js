$(function () {

  $('#map-img').on('load', function () {
    var imgWidth = $('#map-img').width();
    var imgHeight = $('#map-img').height();

    $('#size').text(imgWidth + " X " + imgHeight);
  })

  $('#map-img').mousedown(function(eventObject) {
    var mouseX = eventObject.pageX - $('#map-img').offset().left;
    var mouseY = eventObject.pageY - $('#map-img').offset().top;

    var user = document.createElement('img');
    $(user).prop({'class': 'user', 'alt': 'Julian', 'src': 'Feet Raster.png'});

    $(user).on('load', function () {
      var userPosX = mouseX - user.width/2.0;
      var userPosY = mouseY - user.height/2.0;      
      $(user).css({'left': userPosX, 'top': userPosY}).appendTo($('#map'));
    });
    

  });


})
