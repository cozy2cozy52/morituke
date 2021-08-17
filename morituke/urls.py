# -*- coding: utf-8 -*-
"""
Created on Tue Apr 20 19:28:44 2021

@author: user
"""

#from django.urls import path
#from . import views

from django.urls import path
from . import views

urlpatterns = [
    path('', views.moritukeView.as_view(), name='index'),
    path('img/', views.imgView.as_view(), name='img'),
    path('dinner/', views.dinnerView.as_view(), name='dinner'),
    path('seizou/', views.seizouView.as_view(), name='seizou'),
    path('seizou_submit/', views.seizou_submitView.as_view(), name='seizou_submit'),
    path('tyousei/', views.tyouseiView.as_view(), name='tyousei'),
    path('tyousei_submit/', views.tyousei_submitView.as_view(), name='tyousei_submit'),
    path('nokori_yosou/', views.nokori_yosou_View.as_view(), name='nokori_yosou'),
]
