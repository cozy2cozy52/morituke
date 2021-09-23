from django.urls import path
from . import views

urlpatterns = [
    path('', views.resultsView.as_view(), name='predict_results'),
    path('sum', views.sum_resultsView.as_view(), name='sum_results'),
    path('graph', views.graph_resultsView.as_view(), name='graph'),
]
