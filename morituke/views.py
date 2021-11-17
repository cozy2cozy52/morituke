from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
import 弁当数予想.SQL2DF as SQL2DF
import 弁当数予想.launch_web as web
import 弁当数予想.shidashi as shidashi
import 弁当数予想.Write_DB as Write_DB
import pandas as pd
import datetime
import morituke.forms as forms
import global_values as gv

predict_products = gv.predict_products

# 仕出しを定番に追加する品目
shidashi2teiban = \
    ['昼食弁当_並','昼食弁当_大','お魚弁当_並','お魚弁当_大']
    
display_name = \
    ['並','大','魚並','魚大','から並','から大',
     'ハン並','ハン大','野菜','彩','ライス',
     '温うどん','鶏照丼']
    
form_name_dict = {predict_products[0]:'nami',
                  predict_products[1]:'oomori',
                  predict_products[2]:'sakana_nami',
                  predict_products[3]:'sakana_oomori',
                  predict_products[4]:'kara_nami',
                  predict_products[5]:'kara_oomori',
                  predict_products[6]:'han_nami',
                  predict_products[7]:'han_oomori',
                  predict_products[8]:'yasai',
                  predict_products[9]:'irodori',
                  predict_products[10]:'rice',
                  predict_products[11]:'udon',
                  predict_products[12]:'toriteri'
                  } #form.pyで使用する名前

shikomi_dict = \
    {'肉':['昼食弁当_並','昼食弁当_大','昼食弁当_彩'],
     '魚':['お魚弁当_並','お魚弁当_大'],
     '副菜':['ミニ弁当','からあげ弁当_並','からあげ弁当_大',
             'ハンバーグ弁当_並','ハンバーグ弁当_大',
             'から揚げ弁当ＣＯ','ハンバーグ弁当ＣＯ',
             '和風ハンバーグ弁当ＣＯ','海老フライ弁当ＣＯ']} 
    
cus_name_list = ['店頭用','夕方店舗用','鈴鹿市役所　売店']
city_append_list = \
    ['昼食弁当_並ＣＯ','昼食弁当_大ＣＯ',
     'お魚弁当_並CO','お魚弁当_大ＣＯ']
shidashi_name_list = \
    ['松御膳','竹御膳','葵御膳','梅御膳','桜御膳','橘御膳',
     '鈴の音弁当','ボリューム弁当（洋)','ボリューム弁当(和)','味わい弁当(洋)','味わい弁当(和）',
     'オードブル1人前','オードブル2人前','オードブル4人前','オードブル6人前',
     'キッズオードブル1人前','キッズオードブル2人前','キッズオードブル4人前','キッズオードブル6人前',
     '寿司オードブル1人前','寿司オードブル2人前','寿司オードブル4人前','寿司オードブル6人前',
     'サンドイッチ','サンドイッチバスケット',
     '季節のお弁当','お野菜弁当',]
youbi_list = ['月','火','水','木','金','土','日']

def _tyousei_WriteDB(date,num,product_name):
    if num:
        nami = int(num)
        Write_DB.write_seizou(date, product_name, nami, '調整数')
    else:
        nami = ''
    return nami

class moritukeView(TemplateView):
        
    def __init__(self):
        self.params = {
            'title': '弁当予想数',
            }
    
    def get(self,request):
        return render(request, 'morituke/index.html', self.params)

    def post(self,request):
        
        plus_day = int(request.POST['plus_day'])
        predict_daytime = datetime.datetime.now() + \
                          datetime.timedelta(days=plus_day,hours=9)
        predict_day = datetime.date(
            predict_daytime.year,predict_daytime.month,predict_daytime.day)
        
        lunch_diner = '01' # 昼：01  夕:02
        
        #弁当数予測
        [df_predict,df_cus_prob,df_cus_youkaku] = \
            web.predict_num(predict_daytime,lunch_diner)
        # if len(df_cus_Ex) > 0:
        #     df_cus_Ex    = df_cus_Ex.set_index('顧客名')
        #     df_cus_Ex    = df_cus_Ex.sort_values(predict_products[0],ascending=False)
        #     df_time_over = df_time_over.set_index('顧客名')
    
        #print(df_cus_Ex)
        
        # #仕出し
        obj_shidashi = shidashi.shidashi_class(predict_day)
        df_list = []
        for cn in cus_name_list:
            df_list.append(obj_shidashi.slice_store_city(cn))
        
        [df_shidashi,df_shidashi_cancel] = \
                    obj_shidashi.make_df_shidashi(cus_name_list)
        
        # 仕出しに以下の弁当が入っていたらdf_predictに追加する
        append_list = shidashi2teiban
        df_append = df_shidashi[df_shidashi['品名'].isin(append_list)]
        if len(df_append)>0:
            for j in df_append.index:
                name = df_append.loc[j,'品名']
                df_predict.loc[name,'予想'] += df_append.loc[j,'数量']
                df_predict.loc[name,'注文'] += df_append.loc[j,'数量']
        df_shidashi = df_shidashi[~df_shidashi['品名'].isin(append_list)]
        
        #市役所の弁当でdf_predictに追加する
        df_append_c = df_list[2][df_list[2][cus_name_list[2]].isin(city_append_list)]
        if len(df_append_c)>0:
            for j in df_append_c.index:
                name = df_append_c.loc[j,cus_name_list[2]][:-2]
                df_predict.loc[name,'予想'] += df_append_c.loc[j,'数量']
                df_predict.loc[name,'注文'] += df_append_c.loc[j,'数量']
        df_list[2] = df_list[2][~df_list[2][cus_name_list[2]].isin(city_append_list)]
        
        #仕出しに写真のハイパーリンクを追加
        # df_shidashi_html = df_shidashi.to_html(index = False).replace(\
        #     '<td>桜御膳</td>','''<td><a href="{% url 'img'%}">仕出D</a></td>''')

        #製造数読込
        df_seizou = SQL2DF.get_seizou_num( predict_day,'製造数')
        for p in predict_products:
            df_predict.loc[p,'製造'] = df_seizou[df_seizou['商品名']==p]['製造数'].sum()
        print('=================================')
        print(df_predict['製造'])
        df_predict['製造'] = df_predict['製造'].astype(int)
        df_predict['余り'] = df_predict['製造']-df_predict['注文']
        df_predict = df_predict.reindex(columns=['予想', '製造','注文','余り'])
        
        #製造数読込
        df_tyousei = SQL2DF.get_seizou_num( predict_day,'調整数')
        for p in predict_products:
            df_predict.loc[p,'予想'] += df_tyousei[df_tyousei['商品名']==p]['調整数'].sum()
            
        #仕込み        
        df_shikomi = pd.DataFrame(index=['肉','魚','副菜'],columns=['数量'])
        df_shikomi.loc['肉','数量'] = df_predict.loc[shikomi_dict['肉'][0],'製造'] + \
                                df_predict.loc[shikomi_dict['肉'][1],'製造'] + \
                                df_predict.loc[shikomi_dict['肉'][2],'製造'] + \
                                df_list[0][df_list[0][cus_name_list[0]].isin(shikomi_dict['肉'])]['数量'].sum()
                                
        df_shikomi.loc['魚','数量'] = df_predict.loc[shikomi_dict['魚'][0],'製造'] + \
                                df_predict.loc[shikomi_dict['魚'][1],'製造'] + \
                                df_list[0][df_list[0][cus_name_list[0]].isin(shikomi_dict['魚'])]['数量'].sum()
        df_shikomi = df_shikomi.fillna(0)
        for d in range(len(cus_name_list)):
            tmp_df = df_list[d]
            cus_name = cus_name_list[d]
            for p in shikomi_dict['副菜']:
                num = tmp_df[tmp_df[cus_name]==p]['数量'].sum()
                df_shikomi.loc['副菜','数量'] += num
        df_shikomi.loc['副菜','数量'] += \
            df_shikomi.loc['肉','数量'] + df_shikomi.loc['魚','数量'] + \
            df_predict.loc[shikomi_dict['副菜'][1],'製造'] + \
            df_predict.loc[shikomi_dict['副菜'][2],'製造'] + \
            df_predict.loc[shikomi_dict['副菜'][3],'製造'] + \
            df_predict.loc[shikomi_dict['副菜'][4],'製造']
        
        #定番弁当の名前を短いものにする
        for i in range(len(predict_products)):
            df_predict = df_predict.rename(index={predict_products[i]: display_name[i]})
        
        # 総数
        sousuu = df_predict['予想'].sum() + df_list[0]['数量'].sum() + df_shidashi['数量'].sum()
        shidashi_sousuu = df_shidashi[df_shidashi['品名'].isin(shidashi_name_list)]['数量'].sum() + \
                            df_list[0][df_list[0][cus_name_list[0]].isin(shidashi_name_list)]['数量'].sum()
        
        #print(df_predict.dtypes)
        self.params = {
            'title': predict_day,
            'youbi': youbi_list[predict_day.weekday()],
            'df_predict'        : df_predict.to_html(),
            'df_store_noon'     : df_list[0].to_html(index = False),
            #'df_store_dinner'   : df_list[1].to_html(index = False),
            'df_city'           : df_list[2].to_html(index = False),
            'df_shidashi'       : df_shidashi.to_html(index = False),
            'df_shidashi_cancel': df_shidashi_cancel.to_html(index = False),
            'df_append'         : df_append.to_html(index = False),
            'plus_day'          : plus_day,
            'sousuu'            : sousuu,
            'shidashi_sousuu'   : shidashi_sousuu,
            'df_shikomi'        : df_shikomi,
            'df_cus_Ex'         : df_cus_prob.to_html(index = False),
            'df_time_over'      : df_cus_youkaku.to_html(index = False)
            }
        
        response = render(request, 'morituke/predict.html', self.params)
        
        return response


class imgView(TemplateView):
    def __init__(self):
        self.params = {
            'title': '弁当予想数',
            }
    def get(self,request):
        return render(request, 'morituke/img.html', self.params)
    
    def post(self,request):
        return render(request, 'morituke/img.html', self.params)


class dinnerView(TemplateView):
    
    def __init__(self):
        self.params = {
            'title': '弁当予想数',
            }
    
    def get(self,request):
        return render(request, 'morituke/index.html', self.params)

    def post(self,request):
        plus_day = int(request.POST['plus_day'])
        #predict_daytime = datetime.datetime(2021,5,6+plus_day,0,0)
        today1 = datetime.datetime.now()+datetime.timedelta(hours=9)
        predict_daytime = today1 + datetime.timedelta(days=plus_day)
        predict_day = datetime.date(predict_daytime.year
                            ,predict_daytime.month
                            ,predict_daytime.day)
        
        lunch_diner = '02' # 昼：01  夕:02
        
        #弁当数予測
        if predict_day.weekday() < 5:
            [df_predict,df_cus_Ex,df_time_over] = web.predict_num(predict_daytime,lunch_diner)
            df_cus_Ex    = df_cus_Ex.set_index('顧客名')
            df_time_over = df_time_over.set_index('顧客名')
        else:
            df_predict = pd.DataFrame()
            df_cus_Ex = pd.DataFrame()
            df_time_over = pd.DataFrame()
        
        # #仕出し
        obj_shidashi = shidashi.shidashi_class(predict_day)
        cus_name_list = ['夕方店舗用']
        df_list = []
        for cn in cus_name_list:
            df_list.append(obj_shidashi.slice_store_city(cn))
        
        [df_shidashi,df_shidashi_cancel] = \
                    obj_shidashi.make_df_shidashi(cus_name_list)
        
        df_shidashi = df_shidashi[df_shidashi['仕出']=='夕']
        
        self.params = {
            'title': predict_day,
            'youbi': youbi_list[predict_day.weekday()],
            'df_predict'        : df_predict.to_html(),
            'df_store_dinner'   : df_list[0].to_html(index = False),
            'df_shidashi'       : df_shidashi.to_html(index = False),
            'df_cus_Ex'         : df_cus_Ex.to_html(),
            'df_time_over'      : df_time_over.to_html()
            }
            
        return render(request, 'morituke/dinner.html', self.params)

class seizouView(TemplateView):

    def post(self,request):
        
        plus_day = int(request.POST['button'])
        today1 = datetime.datetime.now()+datetime.timedelta(hours=9)
        predict_daytime = today1 + datetime.timedelta(days=plus_day)
        predict_day = datetime.datetime(predict_daytime.year
                            ,predict_daytime.month
                            ,predict_daytime.day)
        
        self.params = {
            'title': '製造数入力',
            'form' : forms.seizouInputForm(initial=dict(date=predict_day))
            }
            
        return render(request, 'morituke/seizou.html', self.params)

class seizou_submitView(TemplateView):

    def post(self,request):
        
        date = datetime.datetime.strptime(request.POST['date'], '%Y-%m-%d')
        
        para_dict = {}
        for p in predict_products:
            fn = form_name_dict[p]
            num = int(request.POST[fn])
            para_dict[fn] = num
            Write_DB.write_seizou( date, p, num, '製造数')
        para_dict['title'] = '製造数入力結果'
            
        return render(request, 'morituke/seizou_submit.html', para_dict)


class tyouseiView(TemplateView):

    def post(self,request):
        
        plus_day = int(request.POST['button'])
        today1 = datetime.datetime.now()+datetime.timedelta(hours=9)
        predict_daytime = today1 + datetime.timedelta(days=plus_day)
        predict_day = datetime.datetime(predict_daytime.year
                            ,predict_daytime.month
                            ,predict_daytime.day)
        
        #製造数読込
        df_tyousei = SQL2DF.get_seizou_num( predict_day,'調整数')
        df_tyousei = df_tyousei.set_index('商品名')
        df_disp = pd.DataFrame(index=predict_products)
        df_disp['調整数'] = df_tyousei['調整数']
            
        self.params = {
            'title': '調整数入力',
            'df_tyousei' : df_disp.to_html(),
            'form' : forms.tyouseiInputForm(initial=dict(date=predict_day))
            }
            
        return render(request, 'morituke/tyousei.html', self.params)

class tyousei_submitView(TemplateView):

    def post(self,request):
        
        date = datetime.datetime.strptime(request.POST['date'], '%Y-%m-%d')
        
        para_dict = {}
        for p in predict_products:
            fn = form_name_dict[p]
            if request.POST[fn]:
                num = int(request.POST[fn])
                para_dict[fn] = num
                Write_DB.write_seizou( date, p, num, '調整数')
        para_dict['title'] = '調整数入力結果'
            
        return render(request, 'morituke/tyousei_submit.html', para_dict)


class nokori_yosou_View(TemplateView):

    def post(self,request):
        
        plus_day = int(request.POST['button'])
        today1 = datetime.datetime.now()+datetime.timedelta(hours=9)
        predict_daytime = today1 + datetime.timedelta(days=plus_day)
        predict_day = datetime.datetime(predict_daytime.year
                            ,predict_daytime.month
                            ,predict_daytime.day + plus_day)
        
        # df_nokori_cus['調整数'] = df_tyousei['調整数']
            
        self.params = {
            'title': '予想顧客残り',
            'df_nokori_cus' : 'nokori',
            }
            
        return render(request, 'morituke/nokori_yosou.html', self.params)