$(document).ready(function()
{
	// Add js class
	$('body').addClass('js');
	
	/* Lettering	if(jQuery().lettering)
	{
		$("h1.siteName a span").lettering('words').children('span').lettering();
	} */

	
	// Show/hide menu for responsive layout 
	$('#careerBanner h1.siteName').after('<h3 id="menuToggle"><a href="#">Menu</a></h3>');
	$('#careerBanner h3').each(function()
	{
		$(this).click(function(e)
		{
			
			if($(this).hasClass('menuActive'))
			{
				$('body').removeClass('responsiveMenuActive');
				$(this).removeClass('menuActive');
			}
			else
			{
				$('body').addClass('responsiveMenuActive');
				$(this).addClass('menuActive');
				return false;			
			}
		});
	});
	
	// Wraps object tag with a div for css responsive design styling 
	$('object').wrap('<div class="objectWrap" />');
	
	// Clears email form text area on focus, reiserts on blur
	
	$('#emailUs textarea').focus(function(){
		if($(this).text() == "How can we help you?")
		{
			$(this).text('');
		}
	});
	$('#emailUs textarea').blur(function()
	{
		if($(this).text() == "") {
			$(this).text('How can we help you?');
		}
	});
	// Clears input email text area on focus, reiserts on blur
	$('#emailUs input:text[name="your_email"]').focus(function()
	{
		if($(this).val() == "Your email:") {
			$(this).val('');
		}
	});	
	$('#emailUs input:text[name="your_email"]').blur(function()
	{
		if($(this).val() == "") {
			$(this).val('Your email:');
		}
	});
});