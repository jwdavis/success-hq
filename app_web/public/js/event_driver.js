write_event({"type": "load", "id": "bubba@jwdavis.me"});

function write_event (eventData) {
  var url = $("#api_server_url").attr('url');
  var now = new Date();
  $.ajax({
      url: url,
      data: {"event_data":JSON.stringify(eventData, null, '\t')},
      type: "POST",
      dataType: "json",
      success: function(result){
      	console.log(result);
      },
      error: function( xhr, status, errorThrown ) {
          console.log( "Error: " + errorThrown );
          console.log( "Status: " + status );
          console.dir( xhr );
      }
  });
}