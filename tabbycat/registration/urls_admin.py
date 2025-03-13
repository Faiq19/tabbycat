from django.urls import include, path

from . import views


urlpatterns = [
    path('institutions/', include([
        path('', views.InstitutionRegistrationTableView.as_view(), name='reg-institution-list'),
    ])),
    path('teams/', views.TeamRegistrationTableView.as_view(), name='reg-team-list'),
    path('adjudicators/', views.AdjudicatorRegistrationTableView.as_view(), name='reg-adjudicator-list'),
]
