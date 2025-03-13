from django import forms
from django.utils.text import capfirst

from participants.models import Adjudicator, Coach, Institution, Speaker, Team, TournamentInstitution

from .form_utils import CustomQuestionsFormMixin


class TournamentInstitutionForm(CustomQuestionsFormMixin, forms.ModelForm):

    institution_name = Institution._meta.get_field('name')
    institution_code = Institution._meta.get_field('code')

    name = forms.CharField(max_length=institution_name.max_length, label=capfirst(institution_name.verbose_name), help_text=institution_name.help_text)
    code = forms.CharField(max_length=institution_code.max_length, label=capfirst(institution_code.verbose_name), help_text=institution_code.help_text)

    field_order = ('name', 'code', 'teams_requested', 'adjudicators_requested')

    def __init__(self, tournament, *args, **kwargs):
        self.tournament = tournament
        super().__init__(*args, **kwargs)
        self.add_question_fields()

    class Meta:
        model = TournamentInstitution
        exclude = ('tournament', 'institution', 'teams_allocated', 'adjudicators_allocated')

    def save(self):
        inst, created = Institution.objects.get_or_create(name=self.cleaned_data.pop('name'), code=self.cleaned_data.pop('code'))

        obj = super().save(commit=False)
        obj.institution = inst
        obj.tournament = self.tournament
        obj.save()
        self.save_answers(obj)

        return obj


class InstitutionCoachForm(CustomQuestionsFormMixin, forms.ModelForm):

    def __init__(self, tournament, *args, **kwargs):
        self.tournament = tournament
        super().__init__(*args, **kwargs)
        self.add_question_fields()

    class Meta:
        model = Coach
        fields = ('name', 'email')

    def save(self):
        obj = super().save()
        self.save_answers(obj)
        return obj


class TeamForm(CustomQuestionsFormMixin, forms.ModelForm):

    def __init__(self, tournament, *args, institution=None, **kwargs):
        self.tournament = tournament
        self.institution = institution
        super().__init__(*args, **kwargs)
        self.add_question_fields()

        if self.institution is not None:
            self.fields.pop('institution')

    class Meta:
        model = Team
        fields = ('reference', 'institution', 'use_institution_prefix', 'seed', 'emoji')


class SpeakerForm(CustomQuestionsFormMixin, forms.ModelForm):

    def __init__(self, tournament, *args, **kwargs):
        self.tournament = tournament
        super().__init__(*args, **kwargs)
        self.add_question_fields()

    class Meta:
        model = Speaker
        fields = ('name', 'email', 'phone', 'gender', 'categories')


class AdjudicatorForm(CustomQuestionsFormMixin, forms.ModelForm):

    def __init__(self, tournament, *args, institution=None, **kwargs):
        self.tournament = tournament
        self.institution = institution
        super().__init__(*args, **kwargs)
        self.add_question_fields()

        if self.institution is not None:
            self.fields.pop('institution')

    class Meta:
        model = Adjudicator
        fields = ('name', 'email', 'institution', 'gender')
