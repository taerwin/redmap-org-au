{% extends "formjs/form_base.js" %}

{% block form_name %}
AddStep1
{% endblock %}

{% block msgs %}

    'PHOTO_PERMISSION_REQUIRED': '{{ form.PHOTO_PERMISSION_REQUIRED }}',
    'OTHER_SPECIES_PHOTO_REQUIRED': '{{ form.OTHER_SPECIES_PHOTO_REQUIRED }}',
    'SPECIES_REQUIRED': '{{ form.SPECIES_REQUIRED }}',

{% endblock %}

{% block init %}

    // Clear other_species if species selected
    fields.species.element.change(function() {
        if (fields.species.element.val() !== "")
            fields.other_species.element.val("");
    });

    // TODO: Clear species if other speces is selected

{% endblock %}

{% block clean %}

    // Require photo for other_species
    if (data.other_species) {
        if (!data.photo_url) {
            report_error("photo_url", this.msgs['OTHER_SPECIES_PHOTO_REQUIRED']);
        }
    }

    // Require permission for photos
    if (data.photo_url) {
        if (!data.photo_permission) {
            report_error("photo_permission", this.msgs['PHOTO_PERMISSION_REQUIRED']);
        }
    }

    // Require species or other_species
    if (!data.species && !data.other_species) {
        report_error("species", this.msgs['SPECIES_REQUIRED']);
    }

{% endblock %}
