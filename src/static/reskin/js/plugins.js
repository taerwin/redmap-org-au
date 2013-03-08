/**
 * Field functionality
 */
(function($) {
	$.fn.field = function() {
		return this.each(function() {
			var $field = $(this);
			var $inputs = $field.find('input, select, textarea');
			
			$inputs.bind({
				focus: function() {
					$field.addClass('field-focus');
				},
				blur: function() {
					$field.removeClass('field-focus');
				}
			});
			
			$inputs.placeholder();
		});
	};
})(jQuery);

/**
 * Information tooltips
 */
(function($) {
	$.fn.info = function(options) {
	
		var defaults = {
			tooltipId: 'info',
			showOnFocus: true // A field to fire info toggle on
		};
		
		var settings = $.extend({}, defaults, options);
        var $tooltip;
	
		if ($('#' + settings.tooltipId).length) {
			$tooltip = $('#' + options.selector);
		} else {
			$tooltip = $('<div />');
			$tooltip.attr('id', settings.tooltipId).hide().appendTo('body');
		}
		
		return this.each(function() {
			var $elem = $(this);
			var title = $elem.attr('title');	
			
			if (!title) {
				return;
			}
			
			$elem.removeAttr('title').data('tooltip', title);
			
			$elem.bind({
				mouseover: function(e) {
					showTooltip($elem);
				},
				mouseleave: function() {
					hideTooltip();
				}
			});
			
			if (settings.showOnFocus) {
				$parent = $elem.parents('.control-group');
				$fields = $parent.find('input, textarea, select');
				
				$fields.bind({
					focus: function() {
						showTooltip($elem);
					},
					blur: function() {
						hideTooltip();
					}
				});
			}
			
			if (settings.field) {
				settings.field.each(function() {
					$field = $(this);
					$field.bind({
						focus: function() {
							showTooltip($elem);
						},
						blur: function() {
							hideTooltip();
						}
					});
				});
			}
		});
		
		function showTooltip($elem) {
			$tooltip.text($elem.data('tooltip')).show();					
			positionTooltip($elem);
			
		}
		
		function hideTooltip() {
			$tooltip.hide();			
		}
		
		
		
		function positionTooltip($elem) {
			var top = $elem.offset().top - $tooltip.outerHeight() -5;
			var left = $elem.offset().left;
			
			$tooltip.css({
				top: top,
				left: left
			});
		}
	};
})(jQuery);

/**
 * Placeholders (for IE)
 */
(function($) {
	var placeholder = Modernizr.input.placeholder || false;	
	$.fn.placeholder = function() {	
		return this.each(function() {
			if ($placeholder) return;
			if ($(this).attr('placeholder') != 'undefined') {
				$(this).data('placeholder', $(this).attr('placeholder'));
				$(this).bind({
					focus: function() {
						if ($(this).val() == $(this).data('placeholder')) {
							$(this).removeClass('placeholder').val('');
						}
					},
					blur: function() {
						if ($(this).val() === '') {
							$(this).addClass('placeholder').val($(this).data('placeholder'));
						}
					}	
				});
								
				if ($(this).val() === '') {
					$(this).trigger('blur');
				}
			}
		});
	};
})(jQuery);

/**
 * Faux date pickers
 */
(function($){
    "use strict";

    var pluginName = 'fauxDatepicker';

    //Show dates in one format, submit in another
    var FauxDatepicker = function(el, options) {
        var _this = this;

        //Defaults:
        this.defaults = {
            sourceFormat: $.datepicker.ISO_8601,
            displayFormat: 'dd/mm/yy'
        };

        //Extending options:
        this.opts = $.extend({}, this.defaults, options);

        //Privates:
        this.$sourceEl = $(el);

        // Make the display element. IE has a bug where you can not change the
        // type of an input after it is made, hence the hack
        var type = this.$sourceEl.attr('type');
        this.$displayEl = $('<input type="' + type + '"/>');

        // Copy the attributes across
        $.each(el.attributes, function(i, attr) {
            var name = attr.name;
            var val = attr.value;

            // We do not want to copy these across
            if (name == 'id') return;
            if (name == 'name') return;
            if (name == 'type') return;

            // Transform the date from the source formate to the display format
            if (name == 'value') {
                val = $.datepicker.parseDate(_this.opts.sourceFormat, val);
                val = $.datepicker.formatDate(_this.opts.displayFormat, val);
            }

            _this.$displayEl.attr(name, val);
        });

        this.$sourceEl.hide();
        this.$displayEl.insertAfter(this.$sourceEl);

        // Make the datepicker options by munging the passed in options
        this.datepickerOpts = $.extend({}, this.opts, {
            dateFormat: this.opts.displayFormat,
            altFormat: this.opts.sourceFormat,
            altField: this.$sourceEl
        });
        delete this.datepickerOpts.displayFormat;
        delete this.datepickerOpts.sourceFormat;

        // Make the date picker
        this.$displayEl.datepicker(this.datepickerOpts);

        // Store a reference to this in the elements
        this.$sourceEl.data(pluginName, this);
        this.$displayEl.data(pluginName, this);
    };

    /**
     * Get the display element
     */
    FauxDatepicker.prototype.displayEl = function() {
        return this.$displayEl;
    };

    /**
     * Take a selector, and get the display element for each FauxDatepicker
     * in it.
     */
    FauxDatepicker.displayEl = function($els) {
        return $els.map(function() {
            return FauxDatepicker.getOrCreate(this).displayEl().toArray();
        });
    };

    /**
     * Get the real, source element
     */
    FauxDatepicker.prototype.sourceEl = function() {
        return this.$sourceEl;
    };

    /**
     * Take a selector, and get the source element for each FauxDatepicker
     * in it.
     */
    FauxDatepicker.sourceEl = function($els) {
        return $els.map(function() {
            return FauxDatepicker.getOrCreate(this).sourceEl().toArray();
        });
    };

    FauxDatepicker.getOrCreate = function(el, options) {
        var rev = $(el).data(pluginName);
        if (!rev) {
            rev = new FauxDatepicker(el, options);
        }

        return rev;
    };

    $.fn.fauxDatepicker = function() {
        var options, fn, args;
        // Create a new FauxDatepicker for each element
        if (arguments.length === 0 || (arguments.length === 1 && $.type(arguments[0]) == 'object')) {
            options = arguments[0];
            return this.each(function() {
                return FauxDatepicker.getOrCreate(this, options);
            });
        }

        // Call a function on each FauxDatepicker in the selector
        fn = arguments[0];
        args = $.makeArray(arguments).slice(1);

        if (fn in FauxDatepicker) {
            // Call the FauxDatepicker class method if it exists
            args.unshift(this);
            return FauxDatepicker[fn].apply(FauxDatepicker, args);
        } else {
            var $displayEls = FauxDatepicker.displayEl(this);
            args.unshift(fn);
            return $displayEls.datepicker.apply($displayEls, args);
        }
    };
})(jQuery);

/**
* Django formset helper
*/
(function($) {
    "use strict";

    var pluginName = 'formset';

    //Show dates in one format, submit in another
    var Formset = function(el, options) {
        var _this = this;

        //Defaults:
        this.defaults = {
            emptyForm: '[data-formset-empty-form]',
            body: '[data-formset-body]',
            add: '[data-formset-add]'
        };
        //Extending options:
        this.opts = $.extend({}, this.defaults, options);

        this.$formset = $(el);
        this.$emptyForm = this.$formset.find(this.opts.emptyForm);
        this.$body = this.$formset.find(this.opts.body);
        this.$add = this.$formset.find(this.opts.add);

        this.addForm = (function(addForm) {
            return function() { return addForm.apply(_this, arguments); };
        })(this.addForm);

        this.$add.click(this.addForm);

        // Store a reference to this in the elements
        this.$formset.data(pluginName, this);
    };

    Formset.prototype.addForm = function() {
        var attrs = ['name', 'id', 'for'];
        var selector = $.map(attrs, function(val) {
            return '[' + val + '*=__prefix__]';
        }).join(',');

        var count = this.formCount();
        this.formCount(count + 1);

        var $newForm = this.$emptyForm.clone();
        var $els = $newForm.find(selector);

        $els.each(function(i, el) {
            var $el = $(el);
            $.each(attrs, function(i, attrName) {
                var attr = $el.attr(attrName);
                if (!attr) return;
                $el.attr(attrName, attr.replace('__prefix__', count));
            });
        });


        this.$body.append($newForm);

        return $newForm;

    };

    Formset.prototype.managementForm = function(name) {
        return this.$formset.find('[name=' + this.$formset.data('formset-prefix') + '-' + name + ']');
    };

    Formset.prototype.formCount = function() {
        var $totalForms = this.managementForm('TOTAL_FORMS');

        if (arguments.length) {
            $totalForms.val(arguments[0]);
            return this;
        } else {
            return parseInt($totalForms.val(), 10) || 0;
        }
    };

    Formset.getOrCreate = function(el, options) {
        var rev = $(el).data(pluginName);
        if (!rev) {
            rev = new Formset(el, options);
        }

        return rev;
    };

    $.fn[pluginName] = function() {
        var options, fn, args;
        // Create a new Formset for each element
        if (arguments.length === 0 || (arguments.length === 1 && $.type(arguments[0]) != 'string')) {
            options = arguments[0];
            return this.each(function() {
                return Formset.getOrCreate(this, options);
            });
        }

        // Call a function on each Formset in the selector
        fn = arguments[0];
        args = $.makeArray(arguments).slice(1);

        if (fn in Formset) {
            // Call the Formset class method if it exists
            args.unshift(this);
            return Formset[fn].apply(Formset, args);
        } else {
            throw new Error("Unknown function call " + fn + " for $.fn.formset");
        }
    };
})(jQuery);
