# -*- coding: utf-8 -*-
"""
Created on Wed Apr 21 14:53:07 2021

@author: user
"""

from django import forms

class seizouInputForm(forms.Form):
    date            = forms.DateField(label='日付')
    nami            = forms.IntegerField(label='並')
    oomori          = forms.IntegerField(label='大')
    sakana_nami     = forms.IntegerField(label='魚並')
    sakana_oomori   = forms.IntegerField(label='魚大')
    kara_nami       = forms.IntegerField(label='から並')
    kara_oomori     = forms.IntegerField(label='から大')
    han_nami        = forms.IntegerField(label='ハン並')
    han_oomori      = forms.IntegerField(label='ハン大')
    yasai           = forms.IntegerField(label='野菜')
    irodori         = forms.IntegerField(label='彩')
    curry_nami      = forms.IntegerField(label='カレ並')
    curry_oomori      = forms.IntegerField(label='カレ大')
    udon_nami          = forms.IntegerField(label='うどん並')
    udon_oomori          = forms.IntegerField(label='うどん大')
    soba_nami          = forms.IntegerField(label='そば並')
    soba_oomori          = forms.IntegerField(label='そば大')
    nori      = forms.IntegerField(label='のり弁')
    kisetu      = forms.IntegerField(label='季節')
    
class tyouseiInputForm(forms.Form):
    date            = forms.DateField(label='日付')
    nami            = forms.IntegerField(label='並', required=False)
    oomori          = forms.IntegerField(label='大', required=False)
    sakana_nami     = forms.IntegerField(label='魚並', required=False)
    sakana_oomori   = forms.IntegerField(label='魚大', required=False)
    kara_nami       = forms.IntegerField(label='から並', required=False)
    kara_oomori     = forms.IntegerField(label='から大', required=False)
    han_nami        = forms.IntegerField(label='ハン並', required=False)
    han_oomori      = forms.IntegerField(label='ハン大', required=False)
    yasai            = forms.IntegerField(label='野菜', required=False)
    irodori         = forms.IntegerField(label='彩', required=False)
    curry_nami      = forms.IntegerField(label='カレ並', required=False)
    curry_oomori      = forms.IntegerField(label='カレ大', required=False)
    udon_nami          = forms.IntegerField(label='うどん並', required=False)
    udon_oomori          = forms.IntegerField(label='うどん大', required=False)
    soba_nami          = forms.IntegerField(label='そば並', required=False)
    soba_oomori          = forms.IntegerField(label='そば大', required=False)
    nori      = forms.IntegerField(label='のり弁', required=False)
    kisetu      = forms.IntegerField(label='季節', required=False)