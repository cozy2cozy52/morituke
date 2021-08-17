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
]
