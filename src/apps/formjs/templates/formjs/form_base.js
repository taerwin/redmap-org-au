
function {% spaceless %}{% block form_name %}{% endblock %}{% endspaceless %} (form_ele_or_sel) {

    this.$form = $(form_ele_or_sel);

    this.msgs = {
        {% block msgs %}{% endblock %}
    };

    this.fields = {
        {% for field in form %}
        {{ field.name }}: {
            name: '{{ field.name }}',
            input_name: '{{ form.prefix }}-{{ field.name }}',
            input_id: "{{ field.auto_id }}",
            required: {{ field.required|yesno:"true,false"}},
            element: $("#{{ field.auto_id }}")
        },
        {% endfor %}
    }

    this.find_field_callback = function(callback) {
        for (var idx in this.fields) {
            var field = this.fields[idx];
            if (callback(field)) 
                return field;
        }
        return null;
    };
    
    this.find_field = function(key, val) {
        return this.find_field_callback(
            function(field) {
                return field[key] === val;
            }
        );
    };

    this._errors = {};

    this.cleaned_data = null;

    this.init = function() {
        var fields = this.fields;
        {% block init %}
        {% endblock %}
    }

    this.is_valid = function() {
        var data_list = $form.serializeArray();
        this.cleaned_data = {};
        this._errors = {};
        for (var i=0; i<data_list.length; i++) {
            var data_item = data_list[i];
            var name = data_item.name;
            var field = this.find_field("input_name", name);
            if (field !== null) {
                this.cleaned_data[field.name] = data_item.value;
            }
        }
        // Manually add file values for "is_set" tests
        for (var idx in this.fields) {
            var field = this.fields[idx];
            if (field.element.attr("type")==="file") {
                this.cleaned_data[field.name] = field.element.val();
            }
        }
        this.cleaned_data = this.clean();
        return Object.keys(this._errors).length === 0;
    };

    this._report_error = function (field, msg) {
        var input_name = this.fields[field].input_name;
        if (this._errors[input_name] === undefined)
            this._errors[input_name] = [];
        this._errors[input_name].push(msg)
    }

    this.clean = function() {
        var report_error = this._report_error;
        var data = this.cleaned_data;
        {% block clean %}
        {% endblock %}
        return data;
    }

    this.init();

    return this;

}