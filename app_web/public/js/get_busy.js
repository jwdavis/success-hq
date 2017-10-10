$( document ).ready(function() {
	var b1 = $("#low");
	var b2 = $("#med");
	var b3 = $("#high");
	console.log('ready to roll');

	b1.click(function(){
		startLoad('low');
		console.log('starting low load');
	});
	b2.click(function(){
		startLoad('med');
		console.log('starting med load');
	});

	b3.click(function(){
		startLoad('high');
		console.log('starting high load');
	});

	function startLoad(level){
		$.ajax({
			url: '/load_gen',
			data: {"level":level},
			type: "GET",
			dataType: "json",
			success: function(result) {
				console.log(result);
			},
		    error: function( xhr, status, errorThrown ) {
		        console.log( "Error: " + errorThrown );
		        console.log( "Status: " + status );
		        console.dir( xhr );
		    }
		});
	}
});