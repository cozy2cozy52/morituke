# -*- coding: utf-8 -*-

import datetime
import SQL2DF
import pandas as pd


#%%

lunch_diner = '01' # 昼：01  夕:02
from_day = datetime.datetime(2021,4,5,0,0)
end_day = datetime.datetime(2022,2,20,0,0)
syurui = '昼お魚' #'昼お魚' 昼日替

df_date_menu = SQL2DF.get_menu(lunch_diner,from_day,end_day,"献立",[syurui])

#%%

if syurui == '昼日替':
    n = '昼食弁当_並'
else:
    n = 'お魚弁当_並'

dict_col_list = {'商品名':[n]}

str_start_day = SQL2DF.datetime2otodokeday(from_day)
str_last_day = SQL2DF.datetime2otodokeday(end_day)

df_order_s = SQL2DF.read_delivery_data_chose_day(dict_col_list,'鈴鹿店',
                                 str_start_day,str_last_day,lunch_diner)
df_order_y = SQL2DF.read_delivery_data_chose_day(dict_col_list,'四日市店',
                                 str_start_day,str_last_day,lunch_diner)

df_order_s = SQL2DF.otodoke_date(df_order_s,'日付')
df_order_y = SQL2DF.otodoke_date(df_order_y,'日付')

#%%

for d in df_order_s['日付'].unique():
    df_date_menu.loc[d,'個数'] = df_order_s[df_order_s['日付']==d]['個数'].sum() + \
                                    df_order_s[df_order_s['日付']==d]['個数'].sum()
                                  
#df_date_menu = df_date_menu.drop('ID_昼日替',axis=1)
#%%

df_date_menu = df_date_menu[df_date_menu['曜日']<5]
#df_date_menu = df_date_menu[df_date_menu['個数']>220]
df_date_menu = df_date_menu[df_date_menu['個数']>35] #魚

for d in df_date_menu.index:
    n = 0
    if d - datetime.timedelta(days=14) in df_date_menu.index:
        b2w = df_date_menu.loc[d - datetime.timedelta(days=14),'個数']
        n += 1
    else:
        b2w = 0
        
    if d - datetime.timedelta(days=7) in df_date_menu.index:
        b1w = df_date_menu.loc[d - datetime.timedelta(days=7),'個数']
        n += 1
    else:
        b1w = 0
        
    if d + datetime.timedelta(days=7) in df_date_menu.index:
        a1w = df_date_menu.loc[d + datetime.timedelta(days=7),'個数']
        n += 1
    else:
        a1w = 0
        
    if d + datetime.timedelta(days=14) in df_date_menu.index:
        a2w = df_date_menu.loc[d + datetime.timedelta(days=14),'個数']
        n += 1
    else:
        a2w = 0
    avg1 = (b2w + b1w + a1w + a2w) / n
    
    df_date_menu.loc[d,'周辺平均'] = avg1
    df_date_menu.loc[d,'人気度'] = df_date_menu.loc[d,'個数']/avg1

#%%

df_date_menu.人気度[df_date_menu.人気度>1.1]=1.1
df_date_menu.人気度[df_date_menu.人気度<0.9]=0.9
for d in df_date_menu.index:
    df_date_menu.loc[d,'基本数'] = df_date_menu.loc[d,'個数'] / \
                                        df_date_menu.loc[d,'人気度']

#%%
for d in df_date_menu.index:
    n = 0
    if d - datetime.timedelta(days=14) in df_date_menu.index:
        b2w = df_date_menu.loc[d - datetime.timedelta(days=14),'基本数']
        n += 1
    else:
        b2w = 0
        
    if d - datetime.timedelta(days=7) in df_date_menu.index:
        b1w = df_date_menu.loc[d - datetime.timedelta(days=7),'基本数']
        n += 1
    else:
        b1w = 0
        
    if d + datetime.timedelta(days=7) in df_date_menu.index:
        a1w = df_date_menu.loc[d + datetime.timedelta(days=7),'基本数']
        n += 1
    else:
        a1w = 0
        
    if d + datetime.timedelta(days=14) in df_date_menu.index:
        a2w = df_date_menu.loc[d + datetime.timedelta(days=14),'基本数']
        n += 1
    else:
        a2w = 0
    avg1 = (b2w + b1w + a1w + a2w) / n
    
    df_date_menu.loc[d,'周辺平均'] = avg1
    df_date_menu.loc[d,'人気度'] = df_date_menu.loc[d,'個数']/avg1

#%%

df_date_menu.人気度[df_date_menu.人気度>1.1]=1.1
df_date_menu.人気度[df_date_menu.人気度<0.9]=0.9

df_pop = pd.DataFrame()
for m in df_date_menu['name_' + syurui].unique():
    df_tmp = df_date_menu[df_date_menu['name_' + syurui]==m]
    df_pop.loc[m,'平均人気度'] = df_tmp['人気度'].mean()
    df_pop.loc[m,'回数'] = len(df_tmp['人気度'])

df_pop = df_pop.sort_values(by='平均人気度',ascending=False)

df_date_menu.to_csv('df_date_menu.csv',encoding='utf_8_sig')
df_pop.to_csv('df_pop.csv',encoding='utf_8_sig')