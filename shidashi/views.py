from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView
import 弁当数予想.SQL2DF as SQL2DF
import datetime
import pandas as pd

def _df_youbi_henkan(df_shidashi,str_youbi):
    df_shidashi_mon = df_shidashi[df_shidashi['曜日']==str_youbi]
    if len(df_shidashi_mon)<1:
        df_shidashi_mon = pd.DataFrame()
    
    return df_shidashi_mon

class shidashiView(TemplateView):
        
    def __init__(self):
        self.params = {
            'title': '仕出し',
            }
    
    def get(self,request):
        
        #読み込み
        from_day = datetime.date.today()
        end_day  = from_day+datetime.timedelta(days=6)
        df_shidashi = SQL2DF.get_shidashi_period(from_day,end_day)
        
        #絞り込み
        df_shidashi = df_shidashi[~(df_shidashi['顧客名']=='店頭用')]
        df_shidashi = df_shidashi[~(df_shidashi['顧客名']=='夕方店舗用')]
        df_shidashi = df_shidashi[~(df_shidashi['顧客名']=='アズワンネットワーク')]
        df_shidashi = df_shidashi[~(df_shidashi['顧客名']=='ＳＵＺＵＫＡＦＡＲＭ')]
        df_shidashi = df_shidashi[~(df_shidashi['顧客名']=='鈴鹿市役所　売店')]
        df_shidashi = df_shidashi[~(df_shidashi['顧客名']=='サイエンズスクール　第１研修所')]
        df_shidashi = df_shidashi[~(df_shidashi['顧客名']=='サイエンズスクール　第２研修所')]
        df_shidashi = df_shidashi[~(df_shidashi['顧客名']=='お届け')]

        
        df_shidashi = df_shidashi[df_shidashi['キャンセル']==0]
        df_shidashi = df_shidashi[df_shidashi['単価']>100]

        youbi_list = ['月','火','水','木','金','土','日']
        for i in df_shidashi.index:
            df_shidashi.loc[i,'曜日'] = youbi_list[df_shidashi.loc[i,'注文日'].weekday()]
            if df_shidashi.loc[i,'時間帯'] == 1.0:
                df_shidashi.loc[i,'昼夕'] = '昼'
            else:
                df_shidashi.loc[i,'昼夕'] = '夕'
                
        
        df_shidashi = df_shidashi.sort_values(['注文日','時間帯'],
                                              ascending=[True,True])
        
        df_shidashi = df_shidashi.drop('キャンセル', axis=1)
        df_shidashi = df_shidashi.drop('時間帯', axis=1)
        df_shidashi = df_shidashi.fillna('')
        
        df_shidashi = df_shidashi.reindex(columns=
                                ['注文日', '曜日','昼夕','配達方面',
                                 '品名','数量', '単価','顧客名','配達時間',
                                '店頭引取時間','メモ','備考'])
        
        df_shidashi_mon = _df_youbi_henkan(df_shidashi,'月')
        df_shidashi_tue = _df_youbi_henkan(df_shidashi,'火')
        df_shidashi_wed = _df_youbi_henkan(df_shidashi,'水')
        df_shidashi_thu = _df_youbi_henkan(df_shidashi,'木')
        df_shidashi_fri = _df_youbi_henkan(df_shidashi,'金')
        df_shidashi_sat = _df_youbi_henkan(df_shidashi,'土')
        df_shidashi_sun = _df_youbi_henkan(df_shidashi,'日')
        
        self.params = {
            'title'        : '仕出し',
            'df_shidashi_mon'  : df_shidashi_mon.to_html(index = False),
            'df_shidashi_tue'  : df_shidashi_tue.to_html(index = False),
            'df_shidashi_wed'  : df_shidashi_wed.to_html(index = False),
            'df_shidashi_thu'  : df_shidashi_thu.to_html(index = False),
            'df_shidashi_fri'  : df_shidashi_fri.to_html(index = False),
            'df_shidashi_sat'  : df_shidashi_sat.to_html(index = False),
            'df_shidashi_sun'  : df_shidashi_sun.to_html(index = False)
            }
        return render(request, 'shidashi/one_week.html', self.params)

    def post(self,request):
        return render(request, 'shidashi/one_week.html', self.params)
