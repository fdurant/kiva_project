// ==UserScript==
// @name KivaLoanFundingViz
// @require jquery.min.js
// @require jquery-ui.min.js
// @require parse_query_string.js
// @require jquery.dynameter.js
// @include http://www.kiva.org/lend/*
// ==/UserScript==

// Inspired by: https://code.google.com/p/kango-examples/source/browse/trunk/jQueryDemo/src/common/tree.js?spec=svn3&r=3
// jQuery initialization
var $ = null;
(function (callback) {
    try {
	if(window != window.top) {
	    return;
	}
    }
    catch(e) {
	return;
    }
    kango.xhr.send({
	    url:'http://ajax.googleapis.com/ajax/libs/jquery/1.6/jquery.min.js',
                contentType: 'text'
		}, function(data) {
	    eval(data.response.toString());
	    callback(window.$.noConflict(true));
        });
})(function(obj) {
        $ = obj;
        init();
    });

// ---------------------------------------------------------------------------

function init() {
    // Your code here
    addContainers();
    var loanId = getLoanId();
    var res = $.get("http://104.236.210.43/kivapredictor/api/v1.0/loanprediction?loanid=" + loanId,
		    {},
		    function(data) {
		        // Loan funding probability
			$( "div#container" ).text("A priori funding probability: " + 
						  Math.round(data['loanFundingScore']*100) +
						  "%");
			prediction = data['prediction'];
			imgFileName = (prediction == 1) ? 'thumbs_up.png' : 'thumbs_down.png';
			imgUrl = 'http://104.236.210.43/images/' + imgFileName;
			$( "div#container" ).prepend('<img width="46" height="60" src="'+imgUrl+'" style="float:right;"/>');
		        // Three most prominent topics
			var nrWordsPerTopics = 10;
			var topicScores = data['topicScores'];
			$( "div#topicsContainer" ).append('<div style="font-size:18px;padding-bottom:2px;">Major topics</div>');
			for (i = 0; i < 3; i++) {
			    var elem = topicScores[i];
			    var wordList = elem[0];
			    var topicName = elem[1][0];
			    var topicWeight = elem[1][1];
			    var topicText = "[" + wordList.slice(1,nrWordsPerTopics).join(" ") + "]";
			    var fontSize = 14 + Math.floor(Math.log2(topicWeight) * 2);
			    $( "div#topicsContainer" ).append('<div id="'+ topicName +'" style="font-size:'+ fontSize +'px;margin:3px;">' + topicText + '</div>');
			}
			$( "div#topicsContainer" ).append('<a href="http://104.236.210.43/kivapredictor/api/v1.0/loanprediction?loanid=' + data['loanId']+ '" style="font-size:8px;padding-bottom:2px;clear:both;float:right;" target="_blank">[API source]</a>');
		    },
		    'json'
		    ).fail(function() {
			    kango.console.log( "error in retrieving probability score from server" );
			}
			)
}

function addContainers() {

    var loanSummary = $( "#loanSummary" ).prepend('<div id="container" style="font-size:25px;background-color:lightblue;border-width:1px;border-style:solid;border-color:black;margin-bottom:10px;padding-left:10px;">A priori funding probability:  </div>');

    kango.console.log("loanSummary =");
    kango.console.log(loanSummary);

    kango.console.log("container =");
    kango.console.log($( "#container" ));

    var businessOverview = $( "#businessOverview" ).prepend('<div id="topicsContainer" style="background-color:lightblue;border-width:1px;border-style:solid;border-color:black;margin-bottom:10px;padding:10px;"></div>');

    kango.console.log("businessOverview =");
    kango.console.log(businessOverview);

    kango.console.log("topicsContainer =");
    kango.console.log($( "#topicsContainer" ));

}

// From http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
function getLoanId() {
    //    kango.console.log("window.location.href = ");
    //    kango.console.log(window.location.href);
    var match = RegExp(/^.*lend\/(\d+)$/).exec(window.location.href);
    //    kango.console.log("match =");
    //    kango.console.log(match);
    return match && decodeURIComponent(match[1]);
}



/*

	$( "#container" ).dynameter({
		width: 200,
		    label: 'funding probability',
		    value: 0.7,
		    min: 0.0,
		    max: 1.0,
		    unit: 'percent',
		    regions: { // Value-keys and color-refs
		    0: 'not funded',
			.5: 'partially funded',
			1.5: 'fully funded'
			}
	    })
	    
	    });
*/