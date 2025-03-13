from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _, gettext_lazy
from django.views.generic.edit import FormView
from formtools.wizard.views import SessionWizardView

from participants.models import Speaker, TournamentInstitution
from tournaments.mixins import TournamentMixin
from utils.mixins import AdministratorMixin
from utils.tables import TabbycatTableBuilder
from utils.views import VueTableTemplateView

from .forms import AdjudicatorForm, InstitutionCoachForm, SpeakerForm, TeamForm, TournamentInstitutionForm


class CustomQuestionFormMixin:

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs()
        kwargs['tournament'] = self.tournament
        return kwargs


class InstitutionalRegistrationMixin:

    def get_institution(self):
        ti = TournamentInstitution.objects.filter(tournament=self.tournament, coach_set__url_key=self.kwargs['url_key']).select_related('institution')
        return get_object_or_404(ti).institution

    def get_form_kwargs(self, step):
        kwargs = super().get_form_kwargs()
        kwargs['institution'] = self.kwargs['institution']
        return kwargs


class CreateInstitutionFormView(TournamentMixin, CustomQuestionFormMixin, SessionWizardView):
    form_list = [
        ('institution', TournamentInstitutionForm),
        ('coach', InstitutionCoachForm),
    ]

    def done(self, form_list, form_dict, **kwargs):
        t_inst = form_dict['institution'].save()

        coach_form = form_dict['coach']
        coach_form.instance.tournament_institution = t_inst
        coach_form.save()


class BaseCreateTeamFormView(TournamentMixin, CustomQuestionFormMixin, SessionWizardView):
    form_list = [
        ('team', TeamForm),
        ('speaker', SpeakerForm),
    ]

    def get_form(self, step=None, data=None, files=None):
        form = super().get_form(step, data, files)

        # determine the step if not given
        if step is None:
            step = self.steps.current

        if step == 'speaker':
            form = modelformset_factory(Speaker, form=SpeakerForm, extra=self.tournament.pref('speakers_in_team'))(queryset=Speaker.objects.none(), form_kwargs=self.get_form_kwargs(step))
        return form

    def done(self, form_list, form_dict, **kwargs):
        pass


class BaseCreateAdjudicatorFormView(TournamentMixin, CustomQuestionFormMixin, FormView):
    form_class = AdjudicatorForm


class CreateSpeakerFormView(TournamentMixin, CustomQuestionFormMixin, FormView):
    pass


class InstitutionalCreateTeamFormView(InstitutionalRegistrationMixin, BaseCreateTeamFormView):
    pass


class InstitutionalCreateAdjudicatorFormView(InstitutionalRegistrationMixin, BaseCreateAdjudicatorFormView):
    pass


def handle_question_columns(table: TabbycatTableBuilder, objects, questions=None, suffix=0) -> None:
    if questions is None:
        questions = table.tournament.question_set.filter(for_content_type=ContentType.objects.get_for_model(objects.model)).order_by('seq')
    question_columns = {q: [] for q in questions}

    for obj in objects:
        obj_answers = {answer.question: answer.answer for answer in obj.answers.all()}
        for question, answers in question_columns.items():
            answers.append(obj_answers.get(question, ''))

    for question, answers in question_columns.items():
        table.add_column({'key': f'cq-{question.pk}-{suffix}', 'title': question.name}, answers)


class InstitutionRegistrationTableView(TournamentMixin, AdministratorMixin, VueTableTemplateView):

    page_title = gettext_lazy("Institutional Registration")

    def get_table(self):
        t_institutions = self.tournament.tournamentinstitution_set.select_related('institution').prefetch_related(
            'answers__question',
        ).all()

        table = TabbycatTableBuilder(view=self, title=_('Responses'), sort_key='name')
        table.add_column({'key': 'name', 'title': _("Name")}, [t_inst.institution.name for t_inst in t_institutions])
        table.add_column({'key': 'teams_requested', 'title': _("Teams Requested")}, [
            {'text': t_inst.teams_requested, 'sort': t_inst.teams_requested} for t_inst in t_institutions
        ])
        table.add_column({'key': 'teams_allocated', 'title': _("Teams Allocated")}, [
            {'text': t_inst.teams_allocated, 'sort': t_inst.teams_allocated} for t_inst in t_institutions
        ])
        table.add_column({'key': 'adjudicators_requested', 'title': _("Adjudicators Requested")}, [
            {'text': t_inst.adjudicators_requested, 'sort': t_inst.adjudicators_requested} for t_inst in t_institutions
        ])
        table.add_column({'key': 'adjudicators_allocated', 'title': _("Adjudicators Allocated")}, [
            {'text': t_inst.adjudicators_allocated, 'sort': t_inst.adjudicators_allocated} for t_inst in t_institutions
        ])

        handle_question_columns(table, t_institutions)

        return table


class TeamRegistrationTableView(TournamentMixin, AdministratorMixin, VueTableTemplateView):

    page_title = gettext_lazy("Team Registration")

    def get_table(self):
        def get_speaker(team, i):
            try:
                return team.speakers[i]
            except IndexError:
                return Speaker()

        teams = self.tournament.team_set.select_related('institution').prefetch_related(
            'answers__question',
            Prefetch('speaker_set', queryset=Speaker.objects.prefetch_related('answers__question')),
        ).all()
        spk_questions = self.tournament.question_set.filter(for_content_type=ContentType.objects.get_for_model(Speaker)).order_by('seq')

        table = TabbycatTableBuilder(view=self, title=_('Responses'), sort_key='name')
        table.add_team_columns(teams)

        handle_question_columns(table, teams)

        for i in range(self.tournament.pref('speakers_in_team')):
            table.add_column({'key': 'spk-%d' % i, 'title': _("Speaker %d") % (i+1,)}, [get_speaker(team, i).name for team in teams])
            table.add_column({'key': 'email-%d' % i, 'title': _("Email")}, [get_speaker(team, i).email for team in teams])

            handle_question_columns(table, [get_speaker(team, i) for team in teams], questions=spk_questions, suffix=i)

        return table


class AdjudicatorRegistrationTableView(TournamentMixin, AdministratorMixin, VueTableTemplateView):

    page_title = gettext_lazy("Adjudicator Registration")

    def get_table(self):
        adjudicators = self.tournament.adjudicator_set.select_related('institution').prefetch_related('answers__question').all()

        table = TabbycatTableBuilder(view=self, title=_('Responses'), sort_key='name')
        table.add_adjudicator_columns(adjudicators, show_metadata=False)
        table.add_column({'key': 'email', 'title': _("Email")}, [adj.email for adj in adjudicators])

        handle_question_columns(table, adjudicators)

        return table
