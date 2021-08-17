from django.urls import path
from . import views

urlpatterns = [
    path('', views.shidashiView.as_view(), name='one_week'),
]
