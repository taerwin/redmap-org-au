from django.contrib import admin
from models import *


class RuleConditionTestInline(admin.TabularInline):
    model = RuleConditionTest


class SightingValidationRuleAdmin(admin.ModelAdmin):
    inlines = [
        RuleConditionTestInline,
    ]


class ValidationResponseAdmin(admin.ModelAdmin):
    list_display = [
        'tracking_date', 'person', 'sighting_tracking',
        'sighting_validation_condition', 'answer']
    list_filter = ('sighting_tracking__tracking_date',)
    search_fields = [
        'sighting_tracking__sighting__pk',
        'sighting_tracking__person__username',
    ]

admin.site.register(ConditionSection)
admin.site.register(SightingValidationCondition)
admin.site.register(SightingValidationRule, SightingValidationRuleAdmin)
admin.site.register(ValidationMessageTemplate)
admin.site.register(ValidationResponse, ValidationResponseAdmin)
