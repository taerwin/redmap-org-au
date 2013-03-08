
/*
 * Take an object of format {fieldname:[error_msg...]}
 * and update the associated html .errorlist
 * 
 * Assumes each field has wrapper with .field
 * Assumes .errorlist can be appended to .field tag
 */
function formjs_update_errors(field_errors) {
    console.log("formjs_update_errors", field_errors);
	
	$(".errorlist .js_error").remove();
	$(".errorlist:empty").remove();

	for (var field_name in field_errors) {

		var field = $("*[name='"+field_name+"']");
		var error_msgs = field_errors[field_name];

		$wrapper = $(field).parents(".field");
		$errorlist = $wrapper.find(".errorlist");

		if ($errorlist.length == 0) {
			$errorlist = $("<ul class='errorlist'></ul>");
			$wrapper.append($errorlist);
		};

		for (var i=0; i<error_msgs.length; i++) {
			var error_msg = error_msgs[i];
			$errorlist.append("<li class='error js_error'>"+error_msg+"!</li>");
		}
	}

};
