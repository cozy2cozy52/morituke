from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
import pandas as pd

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
        df = results.make_predict_results(day1,db,menu_name)
        #print(df_predict_results)
        
        df_res = pd.DataFrame()
        
        df_p = df[df['予想数']==0]
        df_p.loc['合計',:] = df_p.sum()
        df_res.loc[1,'注文のみ'] = df_p.loc['合計','差']
        
        
        df_m = df[df['注文数']==0]
        df_m.loc['合計',:] = df_m.sum()
        df_res.loc[1,'予想のみ'] = df_m.loc['合計','差']
        
        df_pm = df[~((df['注文数']==0) | (df['予想数']==0))]
        df_pm.loc['合計',:] = df_pm.sum()
        df_res.loc[1,'予想差'] = df_pm.loc['合計','差']
        
        df_res['合計'] = df_res.sum(axis=1)
        
        self.params = {
            'title': '予想結果',
            'db':db,
            'day1':day1,
            'hinmei':request.POST['hinmei'],
            'df_res' : df_res.to_html(),
            'df_p'   : df_p.to_html(),
            'df_m'   : df_m.to_html(),
            'df_pm'  : df_pm.to_html(),
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
            'form' : forms.sum_InputForm(),
        }
        return render(request, 'results/sum_index.html', self.params)
    
    def post(self,request):
        datetime1 = datetime.datetime.strptime(request.POST['day1'], '%Y-%m-%d')
        day1 = datetime.date(datetime1.year,datetime1.month,datetime1.day)
        
        # print(request.POST['c_week'])
        if request.POST['c_week']=='1':
            c_week = 7
        else:
            c_week = 1
        print(c_week)
        df_sum_results = results.make_sum_results(
                            day1,int(request.POST['term']),c_week)
        
        self.params = {
            'title': '予想結果',
            'df_sum_results' : df_sum_results.to_html(),
        }
        return render(request, 'results/sum.html', self.params)


class graph_resultsView(TemplateView):
        
    def __init__(self):
        self.params = {
            'title': 'グラフ',
            }
    
    def get(self,request):
        self.params = {
            'title': 'グラフ',
            'form' : forms.graph_InputForm(),
        }
        return render(request, 'results/graph_index.html', self.params)
    
    def post(self,request):
        datetime1 = datetime.datetime.strptime(request.POST['day1'], '%Y-%m-%d')
        day1 = datetime.date(datetime1.year,datetime1.month,datetime1.day)
        
        datetime2 = datetime.datetime.strptime(request.POST['day2'], '%Y-%m-%d')
        day2 = datetime.date(datetime2.year,datetime2.month,datetime2.day)

        obj = results.results_graph_class(day1,day2,
                                  request.POST['num_type'],
                                  request.POST['hinmei'])
        print(request.POST.getlist("num_type"))
        if '製造数' in request.POST.getlist("num_type"):
            df_seizou = obj.read_seizou_data()
            df_seizou = df_seizou.reindex(columns = gv.predict_products)
            x_list = df_seizou[request.POST['hinmei']].to_list()
            t_list = df_seizou.index.to_list()
            obj.create_graph(x_list,t_list,'製造数')
        if '注文数' in request.POST.getlist("num_type"):
            df_order = obj.read_order_data()
            df_order = df_order.reindex(columns = gv.predict_products)
            x_list = df_order[request.POST['hinmei']].to_list()
            t_list = df_order.index.to_list()
            obj.create_graph(x_list,t_list,'注文数')
        if '差' in request.POST.getlist("num_type"):
            df_seizou_sum = obj.read_seizou_data()
            df_order_sum = obj.read_order_data()
            df_sa = df_seizou_sum-df_order_sum
            df_sa = df_sa.reindex(columns = gv.predict_products)
            x_list = df_sa[request.POST['hinmei']].to_list()
            t_list = df_sa.index.to_list()
            obj.create_graph(x_list,t_list,'差')
        
        graph = obj.get_graph()
        
        self.params = {
            'title': 'グラフ',
            #'df' : df.to_html(),
            'graph' : graph,
        }
        return render(request, 'results/graph.html', self.params)
