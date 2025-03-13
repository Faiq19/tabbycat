from django.contrib import admin

from utils.admin import ModelAdmin

from .models import Answer, Invitation, Question


@admin.register(Answer)
class AnswerAdmin(ModelAdmin):
    list_display = ('question', 'answer', 'content_object')


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    pass


@admin.register(Invitation)
class InvitationAdmin(ModelAdmin):
    pass
