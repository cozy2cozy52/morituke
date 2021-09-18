from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView

import datetime
import 弁当数予想.results as results
import results.forms as forms
import global_values as gv


class resultsView(TemplateView):
        
    def __init__(self):
        self.params = {
            'title': '予想結果',
            }
    
    def get(self,request):
        self.params = {
            'title': '予想結果',
            'form' : forms.InputForm()
        }
        return render(request, 'results/index.html', self.params)

    def post(self,request):
        db = request.POST['db']
        datetime1 = datetime.datetime.strptime(request.POST['date1'], '%Y-%m-%d')
        day1 = datetime.date(datetime1.year,datetime1.month,datetime1.day)
        menu_name = request.POST['hinmei']
        df_predict_results = results.make_predict_results(day1,db,menu_name)
        #print(df_predict_results)
        
        self.params = {
            'title': '予想結果',
            'db':db,
            'day1':day1,
            'hinmei':request.POST['hinmei'],
            'df_predict_results' : df_predict_results.to_html(),
        }
        return render(request, 'results/results.html', self.params)


class sum_resultsView(TemplateView):
        
    def __init__(self):
        self.params = {
            'title': '予想結果',
            }
    
    def get(self,request):
        self.params = {
            'title': '予想結果',
            'form' : forms.sum_InputForm()
        }
        return render(request, 'results/sum_index.html', self.params)
    
    def post(self,request):
        datetime1 = datetime.datetime.strptime(request.POST['day1'], '%Y-%m-%d')
        day1 = datetime.date(datetime1.year,datetime1.month,datetime1.day)
        
        df_sum_results = results.make_sum_results(
                            day1,int(request.POST['term']))
        self.params = {
            'title': '予想結果',
            'df_sum_results' : df_sum_results.to_html(),
        }
        return render(request, 'results/sum.html', self.params)
