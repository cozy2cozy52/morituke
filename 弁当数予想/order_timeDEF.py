# -*- coding: utf-8 -*-
import pyodbc
import pandas as pd
import 弁当数予想.SQL2DF
import copy

    #%%

def order_time(instance,db,df_cus,str_startday,str_lastday,\
               lunch_diner,dead_line,pre_products): 
        
    startday = str_startday
    lastday = str_lastday
    
    split_start = startday.split('-')
    split_last = lastday.split('-')
    
    start_year  = split_start[0]
    start_month = split_start[1]
    start_day   = split_start[2]
    last_year   = split_last[0]
    last_month  = split_last[1]
    last_day    = split_last[2]
    
    youbi = [0,1,2,3,4,5,6]#[0,1,2,3,4,5,6]
    
    
    #%% 指定期間の日付
    from datetime import datetime
    from datetime import timedelta
    start = datetime.strptime('20' + startday, '%Y-%m-%d')
    end   = datetime.strptime('20' + lastday, '%Y-%m-%d')
    
    def daterange(_start, _end):
        for n in range((_end - _start).days):
            yield _start + timedelta(n)
    
    d = daterange(start, end+timedelta(days=1))
    
    import datetime
    range_days = []
    for i in d:
        range_days.append(datetime.date(int(i.year),int(i.month),int(i.day)))
        
    df_days = pd.DataFrame({'date':[],'week':[],'holiday':[]})
    df_days['date'] = range_days
    df_days = df_days.set_index('date')
    
    for d in df_days.index:
        df_days.loc[d,'week'] = d.weekday()
    
#    youbi_num =  len(df_days[df_days['week'].isin(youbi)]) #指定期間中に指定曜日が何日あるか
    
    #%%
    
    def login(instance,db):
        # ユーザー
        user = "sa"
        #パスワード
        pasword = "ofu"
        connection = "DRIVER={SQL Server};SERVER=" + instance + ";uid=" + user + \
                     ";pwd=" + pasword + ";DATABASE=" + db
        return pyodbc.connect(connection)
    
    
    #%% 祝日を抽出
    con = login(instance,'配達共通')
    cursor = con.cursor()
    cursor.execute('select 祝日 \
                   from 祝日 \
                   WHERE 祝日 >= ? AND 祝日 <= ?',(startday,lastday) \
                   )
    rows = cursor.fetchall()
    cursor.close()
    
    holidays = []
    for r in rows:
        holidays.append(datetime.date(int(r[0].year),int(r[0].month),int(r[0].day)))
        
    for d in holidays:
        df_days.loc[d,'holiday'] = 1
    df_days = df_days.fillna(0)
    df_days.index = df_days.index.astype('datetime64')
    
    #%%
    
    dict_col_list = { '顧客ID':df_cus['顧客ID'].to_list(),
                     '商品名':pre_products}
    
    query_select_list = ['日付', '顧客名','顧客ID', '商品名', '個数', '登録時刻', 'コース']
    query_select_list_str = SQL2DF.query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from 販売データ ' + \
               'INNER JOIN 販売明細 ON 販売データ.伝票番号 = 販売明細.伝票番号 ' + \
               'WHERE キャンセル = 0' + \
               ' AND 時間帯 = ' + lunch_diner + \
               ' AND 日付>='+ start_year + start_month + start_day + \
               ' AND 日付<='+ last_year + last_month + last_day
               
    [query,tupls] = SQL2DF.query_for_IN(query,dict_col_list)
    
    #print(query)
    #print(tupls)
    
    #%%
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = SQL2DF.sql2df(query,tupls,instance,db,df_columns)
    df_rows = obj.make_df()
    
    #%%
    dfres = pd.DataFrame({'date':[],'曜日':[],'祝日':[],'コース':[],'顧客名':[],'顧客ID':[],
                          '商品名':[] ,'個数':[],'登録時刻':[],'時間(min)':[]})
    n=0
    for j in range(len(df_rows)):
        year1 = '20'+df_rows.loc[j,'日付'][0:2]
        mon1 = df_rows.loc[j,'日付'][2:4]
        day1 = df_rows.loc[j,'日付'][4:6]
        d = datetime.date(int(year1),int(mon1),int(day1))
        if d.weekday() in youbi: #　曜日を指定して絞る
            holiday = df_days.loc[d,'holiday']
            
            dfres.loc[n] = [d,d.weekday(),holiday, \
                     df_rows.loc[j,'コース'],df_rows.loc[j,'顧客名'],df_rows.loc[j,'顧客ID'], \
                     df_rows.loc[j,'商品名'],df_rows.loc[j,'個数'], \
                     df_rows.loc[j,'登録時刻'],0]
                
            n=n+1
    dfres['date'] = dfres['date'].astype('datetime64')
    dfres['登録時刻'] = dfres['登録時刻'].astype('datetime64')
    #dfres['登録時刻'] = dfres['登録時刻'].dt.time
    #%%　お届け日と注文日の時刻の差を出す
        
    for j in dfres.index:
        tmp_t = dfres.loc[j,'登録時刻']-dfres.loc[j,'date']
        if tmp_t < dead_line:
            dfres.loc[j,'注文時刻差'] = dfres.loc[j,'登録時刻']-dfres.loc[j,'date']
        else:
            dfres = dfres.drop(j, axis=0) # 締切時間行こうの注文はなしとする
        
    #%%
    
    dfagri = pd.DataFrame({'顧客名':[],'顧客ID':[],'平均時刻':[],'最終時刻':[]})
    
    n=0
    for c in dfres['顧客ID'].unique():
        df_tmp = dfres[dfres['顧客ID']==c]
        
        if len(df_tmp)>1:
            i = df_tmp.index[0]
            dfagri.loc[n,'顧客名'] = df_tmp.loc[i,'顧客名']
            dfagri.loc[n,'顧客ID'] = c
            dfagri.loc[n,'平均時刻'] = df_tmp['注文時刻差'].mean()
            dfagri.loc[n,'最終時刻'] = df_tmp['注文時刻差'].max()
            
            n=n+1
        
    #print(dfagri)
    return [dfagri,dfres,df_rows]


#%% 読み込みはなし

def order_time_df(df_past_data,dead_line):
    dfres = copy.copy(df_past_data)        
    for j in dfres.index:
        tmp_t = dfres.loc[j,'登録時刻']-dfres.loc[j,'日付']
        if tmp_t < dead_line:
            dfres.loc[j,'注文時刻差'] = dfres.loc[j,'登録時刻']-dfres.loc[j,'日付']-dead_line
        else:
            dfres = dfres.drop(j, axis=0) # 締切時間以降の注文はなしとする

    #%%
    
    dfagri = pd.DataFrame({'顧客名':[],'顧客ID':[],'3/4時刻':[],'1/2時刻':[]})
    
    n=0
    for c in dfres['顧客ID'].unique():
        df_tmp = dfres[dfres['顧客ID']==c]
        
        if len(df_tmp)>0:
            i = df_tmp.index[0]
            dfagri.loc[n,'顧客名'] = df_tmp.loc[i,'顧客名']
            dfagri.loc[n,'顧客ID'] = c
            dfagri.loc[n,'3/4時刻'] = df_tmp.注文時刻差.quantile(0.75)
            dfagri.loc[n,'1/2時刻'] = df_tmp.注文時刻差.quantile(0.5)
            
            n=n+1
        
    #print(dfagri)
    return dfagri