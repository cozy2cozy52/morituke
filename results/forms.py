# -*- coding: utf-8 -*-
"""
Created on Wed Apr 21 14:53:07 2021

@author: user
"""

from django import forms
import global_values as gv
import datetime

class InputForm(forms.Form):
    db = forms.ChoiceField(widget=forms.Select, 
                                 choices=[("鈴鹿店","鈴鹿店"),("四日市店","四日市店")], # 定数リストを指定する
                                 label="店名")
    
    date1 = forms.DateField(
        widget=forms.DateInput(attrs={"type":"date"})
        ,label='日付',initial=datetime.date.today()
    )
    
    hinmei = forms.ChoiceField(widget=forms.Select, 
                                 choices=gv.predict_products_tuple, # 定数リストを指定する
                                 label="品名")
    
class sum_InputForm(forms.Form):
    
    day1 = forms.DateField(
        widget=forms.DateInput(attrs={"type":"date"})
        ,label='日付',initial=datetime.date.today()
    )
    
    term = forms.IntegerField(label='日数',min_value=1,max_value=31,initial=7)
    
    c_week = forms.ChoiceField(widget=forms.Select, 
                                 choices=[(0,"連続"),(1,"曜日")], # 定数リストを指定する
                                 label="曜日毎")

class graph_InputForm(forms.Form):
    
    day1 = forms.DateField(
        widget=forms.DateInput(attrs={"type":"date"})
        ,label='始め',initial=datetime.date.today()
    )
    
    day2 = forms.DateField(
        widget=forms.DateInput(attrs={"type":"date"})
        ,label='終わり',initial=datetime.date.today()
    )
        
    num_type = forms.MultipleChoiceField(widget=forms.SelectMultiple, 
                                 choices=[("製造数","製造数"),
                                          ("注文数","注文数"),
                                          ("差","差")], 
                                 label="種類")
    
    hinmei = forms.ChoiceField(widget=forms.Select, 
                                 choices=gv.predict_products_tuple, # 定数リストを指定する
                                 label="品名")