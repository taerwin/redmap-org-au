String.prototype.slugify = function() {
	var s = this;
	s = s.toLowerCase();
	s = s.replace(/\t+|\s+|\r+|\n+/g, '-');
	s = s.replace(/[^a-z0-9-]/g, '');
	return s;
}

$(function() {
	$('.lightbox-image').fancybox({
		type: 'image',
		autoScale: false,
		padding: 0,
		border: 0,
		width: 'auto',
		height: 'auto',
		autoScale: false,
		autoDimensions: true
	});
});