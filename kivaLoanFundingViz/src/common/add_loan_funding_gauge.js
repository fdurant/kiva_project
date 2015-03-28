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
    addLoanFundingGaugeContainer();
    fillLoanFundingGaugeContainer();
}

function addLoanFundingGaugeContainer() {

    var loanSummary = $( "#loanSummary" ).prepend('<div id="container" style="font-size:25px;border-width:1px;border-style:solid;border-color:black;margin-bottom:10px;padding:3px;">A priori funding probability:  </div>');

    kango.console.log("loanSummary =");
    kango.console.log(loanSummary);

    kango.console.log("container =");
    kango.console.log($( "#container" ));

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



function fillLoanFundingGaugeContainer() {
    
    var prob = 0.5;
    //    var gauge = $( "div#container" ).text(": " + prob);
    var loanId = getLoanId();
    var gauge = $.get("http://104.236.210.43/kivapredictor/api/v1.0/loanprediction?loanid=" + loanId,
					 {},
					 function(data) {
					     kango.console.log("data received from server = ");
					     kango.console.log(data);
					     $( "div#container" ).text("A priori funding probability: " + 
								       Math.round(data['loanFundingScore']*100) +
								       "%");
					 },
					 'json'
					 ).fail(function() {
						 kango.console.log( "error in retrieving probability score from server" );
					     }
					     )
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