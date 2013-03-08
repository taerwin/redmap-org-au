$(function() {

	(function() {
		$faqs = $('#faqs');
		
		if (!$faqs.length) {
			return;
		}
		
		$questions = $faqs.find('.faq-question');
		
		$questions.bind('click', function() {
			$faq = $(this).parents('.faq');
			$faq.toggleClass('expanded');
		});
	})();

	$('.info').info({'showOnFocus': true});

	// Disable AJAX validation on skip buttons
	$('.skip').click(function(e) {
		var $form = $(this).parents('form');		
		$form.unbind('submit');
	});

	$('.more').click(function(e) {
		var $target = $($(this).attr('href'));		
		if (typeof $target == 'undefined')
			return false;
		$target.show();
		$(this).hide();
		e.preventDefault();
		return false;
	});

	$('#nav').find('.subnav-dropdown').each(function() {
		$(this).click(function(e) {
		});
	});
	
	// Lightbox
	function Lightbox(options, content) {
	
		var self = this;
	
		options = options || {};
	
		if (content) {
			options.content = content;
		}
	
		var defaults = {
			transitionIn: 'none',
			transitionOut: 'none',
			padding: 0,
			border: 0,
			width: 640,
			height: 480,
			autoScale: false,
			centerOnScroll: true,
			enableEscapeButton: true,
			autoDimensions: false
		};
		
		var settings = $.extend({}, defaults, options);
		
		this.lightbox = $.fancybox(settings);		
		this.close = function() {
			$.fancybox.close();
		};
	}

	$('.dropdown-toggle').dropdown();
    
    $('.species-filter').chosen();
	$('.species-filter').change(function(){
		window.location = jQuery.param.querystring( window.location.href, 'species=' + $(this).find(':selected').first().val()+'&page=1' );		
	});
	
	// Lightbox image
	$('.lightbox-image').click(function(e) {	
		var lightbox = new Lightbox({
			href: $(this).attr('href'),
			type: 'image',
			modal: false,
			autoScale: false,
			autoDimensions: true			
		})
		e.preventDefault();
		return false;
	});
	
	$('.row-clickable').each(function() {
		$(this).find('a').click(function(e) {
			e.stopPropagation();
		});
		$(this).click(function(e) {
			var href = $(this).data('href'),
				target = e.target;
			
			if (!href) {
				return;
			}
			
			window.location = href;
		});
	});
	
	/**
	 * Newsletter form
	 * Catch the submit, open lightbox, and enter email into lightbox form
	 */
	(function() {
		var $newsletter = $('#newsletter');
		
		if (!$newsletter.length) {
			return;
		}		
		
		$newsletter.submit(function(e) {
			var $email = $newsletter.find('input[type=text]');
			var lightbox = new Lightbox({
				type: 'ajax',
				autoScale: false,
				href: $newsletter.attr('action'),
				onComplete: function() {
					var $content = $('#lightbox');
					var $form = $content.find('form');					
					$content.find('input[type=email]').val($email.val());					
				}
			});
		
			e.preventDefault();
			return false;
		});
	})();

});

/**
 * Add a map to the page
 * @param string id The ID of the element to render map in
 * @param LatLng latlng A Google Maps LatLng object
 * @param object options Additional options
 */
function add_map(id, latlng, options) {
	var map, defaults = {
		zoom: 4,
		center: latlng,
		mapTypeId: google.maps.MapTypeId.ROADMAP,
		mapTypeControl: false,
		streetViewControl: false,
		panControl: false,
		zoomControl: false
	};
	
	options = options || {};	
	
	var settings = $.extend({}, defaults, options);
	
	map = new google.maps.Map(document.getElementById(id), settings);
	
	return map;
}