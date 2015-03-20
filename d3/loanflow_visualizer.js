// Adapted from https://apps.carleton.edu/global_stock/js/pathways_visualizer.js

var width;
var height;

var layoutValue=0;
var canDescend=false;

$(document).ready(function() {

	$.getJSON('data.json', function(JSON) {
 
	var units = "USD";
	
	var chartElement = $("#loanFlowChart");
	
	var margin = {top: 10, right: 10, bottom: 10, left: 10};
	   
	width = chartElement.width();
	height = chartElement.height();
	
	var formatNumber = d3.format(",.0f"),    // zero decimal places
	    format = function(d) { return formatNumber(d) + " " + units; },
	    color = d3.scale.category20();
	    
	var url = window.location.protocol + "//" + window.location.host + window.location.pathname;
	
	drawChart();
	
	function handleResize()
	{
		if (width != chartElement.width())
		{
			width = chartElement.width();
			drawChart(true);
		}
	}
	
	setInterval(handleResize, 500);
	
	function drawChart(redraw)
	{
		if (redraw)
		{
			d3.selectAll(".link").remove();
			d3.selectAll(".node").remove();
			d3.selectAll("#loanFlowChart svg").remove();
		}
		
		var sankey = d3.sankey()
			.size([width, height - margin.bottom])
			.nodes(JSON.nodes)
			.links(JSON.links)
			.nodeWidth(20)
			.nodePadding(10);
		
		// If layoutValue is non-zero, we're not looking at the whole map, so 
		// we want to optimize the height of the display. To do that, we set the
		// sankey height to something small (100) and call layoutTest to get a
		// new optimal height.
		if (layoutValue)
		{
			sankey.size([width, 100]);
			height = sankey.layoutTest(1);
			chartElement.height((height + margin.bottom) + "px"); 
			sankey.size([width, height])
		}
	
		// append the svg canvas to the page
		var svg = d3.select("#loanFlowChart").append("svg")
			.attr("width", (width + margin.right)+"px")
			.attr("height", (height + margin.bottom)+"px")
			.attr("id", "loanFlowSVG")
			.append("g")
			.attr("transform", "translate(1,1)");
		
		// Set the sankey layout property (0 means don't sort the nodes; higher values will
		// sort the nodes by size.
		sankey.layout(layoutValue); // layoutValue is a global set by the module
		
		var path = sankey.link();
	
		// add in the links
		var link = svg.append("g")
			.attr("class", "links")
			.selectAll(".link")
			.data(JSON.links)
			.enter().append("path")
			.attr("class", function(d) {
				if (canDescend) {
					return "link clickable";
				} else {
					return "link";
				}	
			})
			.attr("d", path)
			.style("stroke-width", function(d) { return Math.max(1, d.dy); })
			.style("stroke", function(d) { return d.color = color(d.source.name.replace(/ .*/, "")); })
			.sort(function(a, b) { return b.dy - a.dy; });
	      
		// add the link titles
		link.append("title")
			.text(function(d) {
				return d.source.name + " → " + 
				d.target.name + "\n" + format(d.value); 
			});
	
		// set the action for clicking on links
		if (canDescend)
		{
			link.on("click", function() {
				var major = d3.select(this).datum().source.name;
				var career = d3.select(this).datum().target.name;
				window.location = url + "?major=" + major + "&career=" + career;
			})	
		}
		
		// add in the nodes
		var node = svg.append("g")
			.attr("class", "nodes")	
			.selectAll(".node")
			.data(JSON.nodes)
			.enter().append("g")
			.attr("class", function(d) {
				if (canDescend) {
					return "node clickable";
				} else {
					return "node";
				}	
			})
			.attr("transform", function(d) { 
				return "translate(" + d.x + "," + d.y + ")"; 
			});
	
		// add the rectangles for the nodes
		node.append("rect")
			.attr("height", function(d) { return d.dy; })
			.attr("width", sankey.nodeWidth())
			.style("fill", function(d) { 
				return d.color = color(d.name.replace(/ .*/, "")); 
			})
			.style("stroke", function(d) { 
				return d3.rgb(d.color).darker(2); 
			})
			.append("title")
			.text(function(d) { 
				return d.name + "\n" + format(d.value); 
			});
	
		// add in the title for the nodes
		node.append("text")
			.attr("x", -6)
			.attr("y", function(d) { return d.dy / 2; })
			.attr("dy", ".35em")
			.attr("text-anchor", "end")
			.attr("transform", null)
			.text(function(d) { return d.name; })
			.filter(function(d) { return d.x < width / 2; })
			.attr("x", 6 + sankey.nodeWidth())
			.attr("text-anchor", "start");
		
		// set the action for clicking on nodes
		node.on("click", function() {
			// Left node
			if (d3.select(this).datum().x == 0) {
				var major = d3.select(this).datum().name;
				window.location = url + "?major=" + major;
			}
			// Right node
			else if (canDescend) {
				var career = d3.select(this).datum().name;
				window.location = url + "?career=" + career;
			}
		});
		
		drawCareerResources(sankey, redraw);
	};

	// Add the links on the right side of each career
	function drawCareerResources(sankey, redraw) {
		if (redraw)
		{
			document.getElementById("careerLink").innerHTML = "";
		}
		
		sankey.nodes().forEach(function(node) {
			if (node.link) {
				var firstDiv = document.createElement('div');
				var xPos = node.x + sankey.nodeWidth() + 5;
				var yPos = node.y;
				var height = node.dy;
				
				firstDiv.setAttribute('style', 'margin-top:'+yPos+'px; margin-left:'+xPos+'px; height:'+height+'px');
				
				firstDiv.innerHTML = node.link;
				document.getElementById('careerLink').appendChild(firstDiv);     
			}
		});
	}	
	
});

	    });
