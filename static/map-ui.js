
$(function () {
  
  // Parse the url in the address bar (the resulting dictionary might contain a request to create a new location)
  var queryDict = parseQuery(window.location.search);

  var visibleUsers = {}; // Will keep track of users and their positions

  $('#search-box').keydown(function (e) {
    if (e.keyCode == 27) {
        this.blur();
      } else {
        updateSearchFocus(); 
      }
  });

  $('#search-box').blur(function () {$('.user').popover('hide')});

  $('#search-box').focus(updateSearchFocus);

  function updateSearchFocus() {
window.setTimeout( function () {
            $('.user').popover('hide');       
        for (var uname in visibleUsers) {
            if (visibleUsers.hasOwnProperty(uname)) {
              // Ideally, this function would be a more advanced search function
              if (uname.toLowerCase().indexOf($('#search-box').prop('value').toLowerCase()) != -1) {
                $('#'+uname).popover('show');
              }  
          }
      } 
  }, 0);
  }

  
  var postedPlace; //Keeps track of the place the user will post from the dialog (if the user decides to create a custom bind)
  // If the page was launched from the client in order to create a new bind
  if (queryDict.action == 'place' && queryDict.signals != null) {
  createLocationDialog(function (place) { //When the place is specified in the dialog, this callback will be executed
                       postedPlace = place;
                       placementIndicator(); // Let the user know that they can click somewhere to place a marker there for the finalized bind
                       });
  }
  
  // Get the image height as soon as the image loads
  var imgWidth;
  var imgHeight;
  $('#map-img').on('load', function () {
                   imgWidth = $('#map-img').width();
                   imgHeight = $('#map-img').height();
                   
                   updateUsers(visibleUsers, imgWidth, imgHeight, function () {

                               setInterval(function() {
                                           // Update user positions every second; may need to increase this delay to deal with server load
                                           updateUsers(visibleUsers, imgWidth, imgHeight, function () {})
                                           }, 1000);
                               });
                   
                   });
  
  // If the user clicks on the map and the map is in placement mode, post the user's location on click
  $('#map-img').mousedown(function(eventObject) {
                          if (queryDict.action == 'place' && queryDict.signals != null && postedPlace != null) {
                          var mouseX = eventObject.pageX - $('#map-img').offset().left;
                          var mouseY = eventObject.pageY - $('#map-img').offset().top;

                          Api.getActiveUser(function (err, json) {
                            console.log(err);
                            var username = json.user.id;
                            Api.postBind(username, postedPlace.id, mouseX/imgWidth, mouseY/imgHeight, queryDict.signals, function (err, json) {
                                       console.log(err);          
                                       //addPositionMarker(username, mouseX, mouseY);
                                       var bind = json.bind;
                                       
                                       Api.postPosition(username, bind.id, function (err, json) {
                                                        reloadMapRoot();
                                                        });
                                       });
                          });
                          

                          
                          }
                          
                          });
  
  })

// Call this to redirect to the root map url (without a query in the address bar)
function reloadMapRoot() {
    window.location.href = window.location.origin + window.location.pathname;
}

// Create a dialog for creating a new location
function createLocationDialog(cb) {
    // cb is a function with one parameter: the place that was posted
    var dialog = document.createElement('div');
    $(dialog).prop({'id': 'location-dialog', 'class': 'modal'});
    
    var dialogHeader = document.createElement('div');
    $(dialogHeader).prop({'class': 'modal-header'});
    $(dialogHeader).appendTo(dialog);
   
    var dialogTitle = document.createElement('h3');
    $(dialogTitle).html("Select your Location (1/2)");
    $(dialogTitle).appendTo(dialogHeader);
    
    var dialogBody = document.createElement('div');
    $(dialogBody).prop({'class': 'modal-body'});    
    $(dialogBody).appendTo(dialog);
    
    var form = document.createElement('form');
    $(form).prop({'class': 'form-horizontal', 'id': 'location-form', 'action':"/api/places", 'method':"post"});
    $(form).appendTo(dialogBody);
    
    var buildingInput = document.createElement('select');
    $(buildingInput).prop({'class': "span2", 'id': 'building-input', 'name': 'floor'}); 
    var opt;
    
    opt = document.createElement('option');
    $(opt).html("Building/Floor");    
    $(opt).appendTo(buildingInput); 
    
    opt = document.createElement('option');
    $(opt).html("Outside");
    $(opt).appendTo(buildingInput);    
    
    for (var i=1; i<=4; i++) {
        opt = document.createElement('option');
        $(opt).html("West Hall " + i);    
        $(opt).appendTo(buildingInput);    
    }
    
    for (var i=1; i<=4; i++) {
        opt = document.createElement('option');
        $(opt).html("East Hall " + i);    
        $(opt).appendTo(buildingInput);    
    }
    
    for (var i=1; i<=4; i++) {
        opt = document.createElement('option');
        $(opt).html("Academic Center " + i);    
        $(opt).appendTo(buildingInput);    
    }
    
    for (var i=1; i<=4; i++) {
        opt = document.createElement('option');
        $(opt).html("Campus Center " + i);    
        $(opt).appendTo(buildingInput);    
    }
    
    for (var i=1; i<=4; i++) {
        opt = document.createElement('option');
        $(opt).html("Milas Hall " + i);    
        $(opt).appendTo(buildingInput);    
    }
    
    $(buildingInput).appendTo(form);
    
    var nameInput = document.createElement('input');
    $(nameInput).prop({'type': "text", 'class': "span3", 'id': 'name-input', 'name': 'name', 'placeholder': "Common Name (Ex: lounge)", 'data-provide': "typeahead", "autocomplete": 'off'});
    $(nameInput).appendTo(form);
    
    var aliasInput = document.createElement('input');
    $(aliasInput).prop({'type': "text", 'class': "span3", 'id': 'alias-input', 'name': 'alias', 'placeholder': "Nickname (Ex: The SLAC Realm)", 'data-provide': "typeahead", "autocomplete": 'off'});
    $(aliasInput).appendTo(form);
    
    var dialogFooter = document.createElement('div');
    $(dialogFooter).prop({'class': 'modal-footer'});
    $(dialogFooter).appendTo(dialog);
    
    var doneButton = document.createElement('button');
    $(doneButton).prop({'class': 'btn btn-primary', 'disabled': true, 'id': 'create-location-button'});
    $(doneButton).html("Next");
    $(doneButton).appendTo(dialogFooter);
    
    
    function enableIfFormFilled() {
        if ($('#building-input').prop('selectedIndex') != 0 &&
            $('#name-input').prop('value') != "" &&
            $('#alias-input').prop('value') != "") {
            $('#create-location-button').prop('disabled', false);
        } else {
            $('#create-location-button').prop('disabled', true); 
        } 
    }
    
    $(buildingInput).change(function () {
                            enableIfFormFilled();
                            
                            var floor = $('#building-input').prop('value'); 
                            Api.getPlaces({'floor': floor}, function (err, json) {
                                          console.log(err);
                                          $('#name-input').typeahead({'source': json.places.map(function (place) {return place.name})});
                                          });
                            });
    $(nameInput).change(enableIfFormFilled);
    $(nameInput).keydown(enableIfFormFilled);
    $(aliasInput).change(enableIfFormFilled);
    $(aliasInput).keydown(enableIfFormFilled);
    
    $(doneButton).click(function() {
                        $('#building-input').prop('disabled', true);
                        $('#name-input').prop('disabled', true);
                        $('#alias-input').prop('disabled', true);
                        $('#create-location-button').prop('disabled', true);
                        
                        var floor = $('#building-input').prop('value');
                        var name = $('#name-input').prop('value');
                        var alias = $('#alias-input').prop('value');
                        
                        Api.getPlaces({'floor': floor, 'name': name}, function (err, json) {
                                      console.log(err);
                                      
                                      if (json.places.length > 0) {
                                      // Place already exists.
                                      // TODO: Replace alias/do alias voting thing?
                                      cb(json.places[0]);
                                      } else {
                                      // Place doesn't exist; needs to be created
                                      Api.postPlace(floor, name, alias, function (err, json) {
                                                    console.log(err);
                                                    var place = json.place;
                                                    cb(place);            
                                                    });         
                                      }
                                      $(dialog).modal('hide'); 
                                      
                                      });
                        
                        
                        
                        });
    
    $(dialog).appendTo($('body'));
    
    // Actually present the modal dialog 
    $('#location-dialog').modal({'keyboard': false, 'backdrop': 'static'});  
}

function placementIndicator() {
    var guide = document.createElement('div');
    $(guide).prop({'id': 'position-guide'});    
    
    var title = document.createElement('h3');
    $(title).html("Click on Your Position (2/2)");
    $(title).appendTo($(guide));
    
    $(guide).appendTo($('#map'));
}



function updateUsers(usersObject, boundsWidth, boundsHeight, cb) {
    
                     var newUsers = {};

                     Api.getPositions(true, function (err, json) {
                                      console.log(err);
                                      var extendedPositions = json.positions;

                                      for (var i=0; i < extendedPositions.length; i++) {
                                        associatePositionMarkerWithBind(usersObject, extendedPositions[i], boundsWidth, boundsHeight);

                                        newUsers[extendedPositions[i].username] = true;

                                      }

                                         for (var uname in usersObject) {
                                           if (usersObject.hasOwnProperty(uname)) { // Make sure that the attribute belongs to the instance and not to the prototype
                                             if (newUsers[uname] != true) {
                                                delete usersObject[uname]; 
                                                $('#'+uname).remove();
                                             }
                                           }  
                                         }

                                         cb();
                       
                     });

}

// Create a user marker if necessary. Otherwise, move existing user marker
function associatePositionMarkerWithBind(usersObject, extendedPosition, boundsWidth, boundsHeight) {
                            var uname = extendedPosition.username;
                            var bind = extendedPosition.extended.bind;
                             // Note that bind.x and bind.y are relative numbers rather than absolute pixel locations
                             // We correct for this by multiplying by boundsWidth and boundsHeight.
                             if (usersObject[uname] == undefined) {
                               addPositionMarker(extendedPosition, boundsWidth, boundsHeight);
                               usersObject[uname] = {'x': bind.x, 'y':bind.y};
                             } else {
                               movePositionMarker(extendedPosition, boundsWidth, boundsHeight);
                               usersObject[uname] = {'x': bind.x, 'y':bind.y}; 
                             }   
}

function parseTimeDiff(now, then) {
  var msAgo = now-then;
  if(msAgo < 1000*60) {
    return "Updated less than a minute ago.";  
  } else if (msAgo < 1000*60*60) {
    var minutes = Math.floor(msAgo/1000/60);
    if (minutes == 1) {
      return "Updated about a minute ago.";
    } else {
      return "Updated about "+minutes+" minutes ago.";
    }
  } else if (msAgo < 1000*60*60*24) {
    var hours = Math.floor(msAgo/1000/60/60);
     if (hours == 1) {
      return "Updated about an hour ago.";
    } else {
      return "Updated about "+hours+" hours ago.";
    }   
  } else {
    return "Last updated "+then+".";
  }
}

function getInfoFromExtendedPosition(extendedPosition) {
               var timeAgo = parseTimeDiff(new Date, new Date(extendedPosition.date));
               //TODO: Clean this up:
               return "<p>"+extendedPosition.extended.place.name + "</p><p>"+extendedPosition.extended.place.floor+"</p><p>(" + timeAgo + ")</p>";
}

// Add an icon to represent a user with username at a specified x,y position in pixels
function addPositionMarker(extendedPosition, boundsWidth, boundsHeight) {
    var bind = extendedPosition.extended.bind;      
    var x = bind.x;
    var y = bind.y;
    var username = extendedPosition.username;
    var marker = document.createElement('img');
    $(marker).prop({'class': 'user', 'id': username, 'alt': username, 'src': 'Feet Raster.png'});
    $(marker).on('load', function () {
               var markerPosX = (x*boundsWidth - marker.width/2.0)/boundsWidth*100;
               var markerPosY = (y*boundsHeight - marker.height/2.0)/boundsHeight*100;
               // While you hover over a marker, the marker's username is displayed
               // If you click on the marker, an info box appears with more information about them.
               // This info box disappears when you stop hovering over the icon.
               $(marker).tooltip({'title': username});
               $(marker).popover({'trigger': 'manual', 'title': username+" - "+extendedPosition.extended.place.alias, 'content': getInfoFromExtendedPosition(extendedPosition)});
               $(marker).click(function () {
                 $(marker).tooltip('hide');                 
                 $(marker).popover('show');
                 });
               $(marker).hover(function () {}, 
               function () {
                 $(marker).popover('hide');
                 });
               $(marker).css({'left': markerPosX+'%', 'top': markerPosY+'%'}).appendTo($('#map'));
               });
}

// Move a user marker with username to a specified x,y position in pixels
function movePositionMarker(extendedPosition, boundsWidth, boundsHeight) {
    var bind = extendedPosition.extended.bind;  
    var x = bind.x;
    var y = bind.y;
    var username = extendedPosition.username;
    var marker = $('#'+username);
    var popup = marker.data('popover');
    popup.options.title = username+" - "+extendedPosition.extended.place.alias;
    popup.options.content = getInfoFromExtendedPosition(extendedPosition);

    // width is a function since JQuery returns a list of things (in this case with one element)
    var markerPosX = (x*boundsWidth - marker.width()/2.0)/boundsWidth*100;
    var markerPosY = (y*boundsHeight - marker.height()/2.0)/boundsHeight*100;
    marker.css({'left': markerPosX+'%', 'top': markerPosY+'%'});
}

// Function adapted from https://github.com/voituk/Misc/blob/master/js/hash.js
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
        
        var bpv = k.substr(bps+1, bpe) // Julian Ceipek changed this because it didn't work properly
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


