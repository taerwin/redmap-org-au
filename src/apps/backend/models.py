import positions

from django.utils.translation import ugettext as _
from django.db import models
from django.conf import settings

from redmapdb.models import SightingTracking, PHOTO_MATCHES_SPECIES_CHOICES

SIGHTING_RESULT_TYPES = (
    (True, _('Sighting is valid')),
    (False, _('Sighting is invalid'))
)
PHOTO_RESULT_TYPES = ((True, _('Present')), (False, _('Not present')))

RESPONSES = ((True, _('Yes')), (False, _('No')))


class ValidationMessageTemplate(models.Model):

    name = models.CharField(max_length=128, unique=True)
    template = models.TextField()
    public_assessment = models.TextField(null=True)

    def __unicode__(self):
        return self.name


class ConditionSection(models.Model):

    name = models.CharField(max_length=255)

    @property
    def is_radiogroup(self):
        return "_radiogroup" in self.name

    @property
    def radiogroup_label(self):
        if self.conditions.exists():
            return self.conditions.all()[0].radiogroup_label + "?"

    def __unicode__(self):
        return self.name


class SightingValidationConditionManager(models.Manager):

    def get_sighting_matches_species_yes(self):
        return self.get(
            name="%s - Yes" % settings.PHOTO_MATCHES_SPECIES_QUESTION)

    def get_sighting_matches_species_no(self):
        return self.get(
            name="%s - No" % settings.PHOTO_MATCHES_SPECIES_QUESTION)

    def get_sighting_matches_species_maybe(self):
        return self.get(
            name="%s - Maybe" % settings.PHOTO_MATCHES_SPECIES_QUESTION)


class SightingValidationCondition(models.Model):

    name = models.CharField(max_length=255)
    section = models.ForeignKey(
        ConditionSection, null=True, blank=True, related_name="conditions")

    objects = SightingValidationConditionManager()

    @property
    def is_radiogroup(self):
        return self.section.is_radiogroup

    @property
    def radiogroup_label(self):
        if self.is_radiogroup:
            return self.name.split(" - ")[0]

    @property
    def radiogroup_value(self):
        if self.is_radiogroup:
            return self.name.split(" - ")[1]

    def __unicode__(self):
        if self.is_radiogroup:
            return self.radiogroup_value
        else:
            return self.name


class SightingValidationRuleManager(positions.PositionManager):

    def find_matching_rule(self, conditions, has_photo):
        """
        Search through rules looking for one which matches the reported
        conditions.
        """
        for rule in self.filter(valid_photo=has_photo):
            if rule.is_match(conditions):
                return rule


class SightingValidationRule(models.Model):

    name = models.CharField(max_length=255)
    rank = positions.PositionField()

    valid_photo = models.BooleanField("Photo is", choices=PHOTO_RESULT_TYPES)

    valid_sighting = models.BooleanField(
        "Is sighting valid?",
        choices=SIGHTING_RESULT_TYPES
    )
    validation_message_template = models.ForeignKey(ValidationMessageTemplate)

    objects = SightingValidationRuleManager()

    def is_match(self, conditions):
        fails = [
            not ct.is_match(conditions) for ct in self.condition_tests.all()
        ]
        return not any(fails)

    class Meta:
        ordering = ['rank']

    def __unicode__(self):
        return self.name


RULE_CONDITION_TEST_CHOICES = (
    ("Y", "True"),
    ("N", "False"),
    ("-", "Don't care"),
)


class RuleConditionTestManager(models.Manager):

    def tests_for_rule(self, rule):
        for condition in SightingValidationCondition.objects.all():
            RuleConditionTest.objects.get_or_create(
                condition=condition,
                rule=rule
            )
        return rule.condition_tests


class RuleConditionTest(models.Model):

    rule = models.ForeignKey(
        SightingValidationRule,
        related_name="condition_tests"
    )
    condition = models.ForeignKey(SightingValidationCondition)
    test = models.CharField(
        max_length="1",
        default="-",
        choices=RULE_CONDITION_TEST_CHOICES
    )

    objects = RuleConditionTestManager()

    def is_match(self, conditions):
        """
        Does this test pass based on the conditions provided
        """
        return ((self.test == "-") or
                ((self.test == "Y") and (self.condition in conditions)) or
                ((self.test == "N") and (self.condition not in conditions)))

    def __unicode__(self):
        return "%s = %s" % (self.condition, self.test)


class ValidationResponseManager(models.Manager):

    def record_responses(self, sighting, checked_conditions):
        """
        Record all responses provided as part of an validation
        assessment report.

        Responses should be recorded before reporting the sighting valid or
        invalid.
        """
        tracker = sighting.tracker
        for condition in SightingValidationCondition.objects.all():
            ValidationResponse.objects.create(
                sighting_tracking=tracker,
                sighting_validation_condition=condition.name,
                answer=(condition in checked_conditions))

    def get_photo_matches_species_response(self, sighting):
        tracker = SightingTracking.objects.get_latest_tracker(sighting)
        try:
            response = self.get(
                sighting_tracking=tracker,
                answer=True,
                sighting_validation_condition__startswith=
                settings.PHOTO_MATCHES_SPECIES_QUESTION)
            key = response.condition.radiogroup_value
            for cval, ckey in PHOTO_MATCHES_SPECIES_CHOICES:
                if key == ckey:
                    return cval

            raise Exception(
                "Unable to find match for '%s' in %s" % (
                    key, PHOTO_MATCHES_SPECIES_CHOICES))

        except ValidationResponse.DoesNotExist:
            return None


class ValidationResponse(models.Model):

    sighting_tracking = models.ForeignKey(SightingTracking)
    sighting_validation_condition = models.CharField(max_length=255)
    answer = models.BooleanField(choices=RESPONSES)

    objects = ValidationResponseManager()

    @property
    def sighting(self):
        return self.sighting_tracking.sighting

    @property
    def tracking_date(self):
        return self.sighting_tracking.tracking_date

    @property
    def person(self):
        return self.sighting_tracking.person

    @property
    def condition(self):
        return SightingValidationCondition.objects.get(
            name=self.sighting_validation_condition)
