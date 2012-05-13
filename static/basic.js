
$(function () {
  
  // Parse the url in the address bar (the resulting dictionary might contain a request to create a new location)
  var queryDict = parseQuery(window.location.search);
  console.log(queryDict);

  var visibleUsers = {}; // Will keep track of users and their positions
  var allBinds = {}; // Will keep track of all binds to reduce request count
  
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
                   
                   
                   Api.getBinds(function (err, json) {

                     for (var i=0; i < json.binds.length; i++) {
                          allBinds[json.binds[i].id] = json.binds[i];
                     }


                   updateUsers(visibleUsers, allBinds, imgWidth, imgHeight, function () {

                               setInterval(function() {
                                           // Update user positions every second; may need to increase this delay to deal with server load
                                           updateUsers(visibleUsers, allBinds, imgWidth, imgHeight, function () {})
                                           }, 1000);
                               });
                   });
                   });
  
  // If the user clicks on the map and the map is in placement mode, post the user's location on click
  $('#map-img').mousedown(function(eventObject) {
                          if (queryDict.action == 'place' && queryDict.signals != null && postedPlace != null) {
                          var mouseX = eventObject.pageX - $('#map-img').offset().left;
                          var mouseY = eventObject.pageY - $('#map-img').offset().top;
                          
                          Api.postBind(queryDict.username, postedPlace.id, mouseX/imgWidth, mouseY/imgHeight, queryDict.signals, function (err, json) {
                                       console.log(err);          
                                       addUserMarker(queryDict.username, mouseX, mouseY);
                                       var bind = json.bind;
                                       
                                       Api.postPosition(queryDict.username, bind.id, function (err, json) {
                                                        reloadMapRoot();
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
                                          console.log(json);
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
                                      console.log(json);
                                      
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




function updateUsers(usersObject, existingBinds, boundsWidth, boundsHeight, cb) {
    
                     var newUsers = {};

                     Api.getPositions(function (err, json) {
                                      var positions = json.positions;
                                      console.log(positions);
        
                                      for (var i=0; i < positions.length; i++) {

                                      var bindID = positions[i].bind;
                                      var username = positions[i].username;

                                      if (existingBinds[bindID] != undefined) {
                                                  var bind = existingBinds[bindID];
                                                  associateUserMarkerWithBind(usersObject, username, bind, boundsWidth, boundsHeight);
                                      } else {

                                      //Anonymous function to create a local scope for the variables the callback needs to operate.
                                      (function (bindID, uname) {
                                       Api.getBind(bindID, function (err, json) {
                                                   var bind = json.bind;
                                                   existingBinds[bindID] = bind;
                                                   associateUserMarkerWithBind(usersObject, uname, bind, boundsWidth, boundsHeight);                                                   
                                                   });
                                       })(bindID, username);

                                      }

                                       newUsers[positions[i].username] = true;
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
function associateUserMarkerWithBind(usersObject, uname, bind, boundsWidth, boundsHeight) {
                                                     // Note that bind.x and bind.y are relative numbers rather than absolute pixel locations
                                                   // We correct for this by multiplying by boundsWidth and boundsHeight.
                             if (usersObject[uname] == undefined) {
                               addUserMarker(uname, bind.x*boundsWidth, bind.y*boundsHeight);
                               usersObject[uname] = {'x': bind.x, 'y':bind.y};    
                             } else {
                               moveUserMarkerTo(uname, bind.x*boundsWidth, bind.y*boundsHeight);
                               usersObject[uname] = {'x': bind.x, 'y':bind.y}; 
                             }   
}

// Add an icon to represent a user with username at a specified x,y position in pixels
function addUserMarker(username, x, y) {
    var user = document.createElement('img');
    $(user).prop({'class': 'user', 'id': username, 'alt': username, 'src': 'Feet Raster.png'});
    $(user).on('load', function () {
               var userPosX = x - user.width/2.0;
               var userPosY = y - user.height/2.0;
               $(user).tooltip({'title': username});
               $(user).css({'left': userPosX, 'top': userPosY}).appendTo($('#map'));
               });
}

// Move a user marker with username to a specified x,y position in pixels
function moveUserMarkerTo(username, x, y) {
    var user = $('#'+username);
    var userPosX = x - user.width/2.0;
    var userPosY = y - user.height/2.0;
    $('#'+username).css({'left': userPosX, 'top': userPosY});
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


