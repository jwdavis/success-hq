google.load("visualization", "1.0", {packages:["corechart",'table']});

getBQData("reg_users_rolling");
getBQData("purchased_boxes_rolling");
getBQData("provisioned_boxes_rolling");
getBQData("calls_sliding_7");
getBQData("active_users_sliding_7");
getBQData("calls");
getBQData("pct_provisioned_rolling");
getBQData("ratings_sliding_7");
getBQData("comments");
getBQData("dialin_sliding_7");
getBQData("support_sliding_7");

function refresh(query,div) {
	console.log($('#' + div).html());
	$('#' + div).html('<div class="center-block" style="width: 70"><img align="center" src="/images/loading.gif" alt="loading.gif" height="64"></div>');
	getBQData(query);
}

function getBQData(card) {
	$.ajax({
		url: app_url,
		data: {"card":card},
		type: "GET",
		dataType: "json",
		success: function(result) {
			if (card == 'dialin_sliding_7') {
				updateWidget('dialins', 'dialinsHistory', result, 'line');
			}
			if (card == 'support_sliding_7') {
				updateWidget('supportTickets', 'supportTicketsHistory', result, 'line');
			}
			if (card == 'comments') {
				var commentDiv = $('#comments');
	  			commentDiv.html('');
	  			comments = result;
	  			for (var index=0; index<comments.length; index++) {
	  				var comment = comments[index];
	  				commentDiv.append('<p>' + comment[0] + ' - ' + comment[1] + '</p>');
	  			}
			}
			if (card == 'ratings_sliding_7') {
				$("#ratings").html(result.value.avg + ' (n=' + result.value.num + ')');
				drawLineChart(result.history, 'ratingsHistory');
			}
			if (card == 'reg_users_rolling') {
				$("#regUsers").html(result.value);
				console.log(result.value);
				updateWidget('regUsers', 'regUsersHistory', result, 'line');
			}
			if (card == 'purchased_boxes_rolling') {
				$("#header_purchased").html(result.value);
				updateWidget('purchasedDevices', 'purchasedDevicesHistory', result, 'line');
			}
			if (card == 'provisioned_boxes_rolling') {
				updateWidget('regDevices', 'regDevicesHistory', result, 'line');
			}
			if (card == 'calls_sliding_7') {
				updateWidget('cpw', 'cpwHistory', result, 'line');
			}
			if (card == 'active_users_sliding_7') {
				updateWidget('sdau', 'sdauHistory', result, 'line');
			}
			if (card == 'pct_provisioned_rolling') {
				updateWidget('prov', 'provHistory', result, 'line');
			}
			if (card == 'calls') {
				updateWidget('', 'cbt', result.cbt, 'donut');
				updateWidget('', 'cbu', result.cbu, 'donut');
				updateWidget('', 'cbo', result.cbo, 'donut');
			}
		},
	    error: function( xhr, status, errorThrown ) {
	        console.log( "Error: " + errorThrown );
	        console.log( "Status: " + status );
	        console.dir( xhr );
	    }
	})
}

function updateWidget(div1, div2, data, chartType) {
	$("#"+div1).html(data.value);
	if (chartType == 'line') {
		drawLineChart(data.history, div2);
	}
	if (chartType == 'donut') {
		drawDonutChart(data, div2);
	}
}

function drawDonutChart(data,div){
	var data = google.visualization.arrayToDataTable(data);
	var options = {
		legend:{position:'top', maxLines: 2},
		fontName: "Proxima Nova",
		titleTextStyle: {color:"#585D60"},
		pieHole: 0.25,
		height: 250,
		chartArea:{left:20,top:20,width:'85%',height:'85%'}
	};
	var chart = new google.visualization.PieChart(document.getElementById(div));
	chart.draw(data, options);
}

function drawLineChart (data, div) {
	var data = google.visualization.arrayToDataTable(data);
	var options = {
		height:200,
		legend: {position:'none'},
		titlePosition:'out',
		title: "30 day trend",
		crosshair: { trigger: 'both', focus: {opacity: 0.3} },
		series: {0:{color:"#00add7"}},
		hAxis: {slantedText:false,showTextEvery: 7},
		fontName: "Proxima Nova",
		titleTextStyle: {color:"#585D60"},
		tooltip: {textStyle: {color:"#585D60"},isHtml:false},
		vAxis: {format:'#',  gridlines: {count:4}, baseline:0}
	};
	var chart = new google.visualization.LineChart(document.getElementById(div));
	chart.draw(data, options);
}