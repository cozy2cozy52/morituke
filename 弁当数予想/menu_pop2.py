# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 21:39:37 2020

@author: user
"""

import datetime
import SQL2DF
import pandas as pd
import copy

#%% ##################################################################

def caluculate_Ex_pop(customID,instance,db,lunch_diner,predict_daytime,
                       now_daytime,df_date_menu,holidays,predict_day,
                       df_products,df_order_menu_for_Ex):
    
    #%% 日付と商品、個数をまとめたｄｆを作成
        
    df_order_date = pd.DataFrame(columns = df_products['メイン分類'].unique())
    for i in df_order_menu_for_Ex.index:
        d = df_order_menu_for_Ex.loc[i,'日付']
        p = df_order_menu_for_Ex.loc[i,'商品名']
        ps = df_products.loc[p,'メイン分類']
        if (d in df_order_date.index) & (ps in df_order_date.columns):
            df_order_date.loc[d,ps] += df_order_menu_for_Ex.loc[i,'個数']
        else:
            df_order_date.loc[d,ps] = df_order_menu_for_Ex.loc[i,'個数']
        for m in df_products['メイン分類'].unique():
            str_ID = 'ID_' + m
            str_name = 'name_' + m
            df_order_date.loc[d,str_ID] = df_order_menu_for_Ex.loc[i,str_ID]
            df_order_date.loc[d,str_name] = df_order_menu_for_Ex.loc[i,str_name]
        df_order_date.loc[d,'曜日'] = d.weekday()
    df_order_date = df_order_date.fillna(0)
    
    #%%　各日付のメニューの人気度を差し引いた基本の数を計算　その基本の数から人気度を計算
    for y in range(7):
        df_tmp = df_order_date[df_order_date['曜日']==y]
        for i in df_tmp.index:
            fd = i - datetime.timedelta(days=14)
            ld = i + datetime.timedelta(days=14)
            df_around = df_tmp[(df_tmp.index>=fd) & (df_tmp.index<=ld)]
            df_around = df_around.drop(i)
            
            if len(df_around)>0:
                for m in df_products['メイン分類'].unique():
                    base = df_around[m].mean()
                    df_order_date.loc[i,m+'_base'] = base
#                    if base == 0:
#                        df_order_date.loc[i,m+'_pop'] = 0
#                    else:
                    df_order_date.loc[i,m+'_pop'] = df_order_date.loc[i,m] - base
            else:
                for m in df_products['メイン分類'].unique():
                    df_order_date.loc[i,m+'_base'] = 0
                    df_order_date.loc[i,m+'_pop'] = 0
                    
    df_order_date['sum_pop'] = 0
    for m in df_products['メイン分類'].unique():
        df_order_date['sum_pop'] += df_order_date[m+'_pop']
    
#    print(df_order_date)
    #%%　人気度の計算
    df_menu_pop = pd.DataFrame()
    for m in df_products['メイン分類'].unique():
        for mid in df_order_date['ID_'+m].unique():
            df_tmp = df_order_date[df_order_date['ID_'+m]==mid]
            n = len(df_tmp)
            if n > 1:
                df_menu_pop.loc[mid,'num'] = n
                df_menu_pop.loc[mid,'pop'] = df_tmp[m+'_pop'].mean()
                df_menu_pop.loc[mid,'name'] = df_tmp['name_'+m][df_tmp['name_'+m].index[0]]
                df_menu_pop.loc[mid,'sum_pop'] = df_tmp['sum_pop'].mean()
            
#    df_menu_pop = df_menu_pop[df_menu_pop['pop']!=1]
#    df_menu_pop = df_menu_pop.sort_values('pop',ascending=False)
    
#    print(df_menu_pop)
    
    #%%　各日付のメニューの人気度を差し引いた基本の数を計算　その基本の数から人気度を計算 ２回目
    for y in range(7):
        df_tmp = df_order_date[df_order_date['曜日']==y]
        for i in df_tmp.index:
            fd = i - datetime.timedelta(days=14)
            ld = i + datetime.timedelta(days=14)
            df_around = df_tmp[(df_tmp.index>=fd) & (df_tmp.index<=ld)]
            df_around = df_around.drop(i)
            
            if len(df_around)>0:
                for k in df_around.index:
                    for m in df_products['メイン分類'].unique():
                        tmp_ID = df_around.loc[k,'ID_'+m]
                        if tmp_ID in df_menu_pop.index:
                            tmp_pop = df_menu_pop.loc[tmp_ID,'pop']
                        else:
                            tmp_pop = 0
                        df_around.loc[k,m+'_base'] = df_around.loc[k,m]+tmp_pop
                            
            if len(df_around)>0:
                for m in df_products['メイン分類'].unique():
                    base = df_around[m+'_base'].mean()
#                    if base == 0:
#                        df_order_date.loc[i,m+'_pop'] = 0
#                    else:
                    df_order_date.loc[i,m+'_pop'] = df_order_date.loc[i,m] - base
            else:
                for m in df_products['メイン分類'].unique():
                    df_order_date.loc[i,m+'_base'] = 0
                    df_order_date.loc[i,m+'_pop'] = 0
                    
#    df_order_date['sum_pop'] = 0
#    for m in df_products['メイン分類'].unique():
#        df_order_date['sum_pop'] += df_order_date[m+'_pop']
    df_order_date.to_csv('df_order_date.csv',encoding='utf_8_sig')
#    print(df_order_date)
    
    #%%　予想日のメニューの人気度の計算
    results_pop = pd.DataFrame()
    for m in df_products['メイン分類']:
        tmp_index = df_products[df_products['メイン分類']==m].index[0]
        tmp_ID = df_products.loc[tmp_index,'メニュー_ID']
        df_tmp = df_order_date[df_order_date['ID_'+m]==tmp_ID]
        if len(df_tmp)>0:
            results_pop.loc['pop',m] = df_tmp[m+'_pop'].mean()
            results_pop.loc['sum_pop',m] = df_tmp['sum_pop'].mean()
            results_pop.loc['num',m] = len(df_tmp)
        else:
            results_pop.loc['pop',m] = 0
            results_pop.loc['sum_pop',m] = 0
            results_pop.loc['num',m] = 0
#    print(results_pop)
    
    return results_pop
    
#%%
def df_products_lunch_diner(lunch_diner):
    if lunch_diner == '01':
        df_products = pd.DataFrame(index = ['昼食弁当_並','昼食弁当_大','昼食弁当_ヘルシー'],
                               columns = ['商品_ID','メイン分類','メニュー_ID',
                                          'メニュー_名','同メニュー過去回数','pop',
                                          'メニューNG変更先'])
        df_products.loc['昼食弁当_並',     '商品_ID'] = 18
        df_products.loc['昼食弁当_大',     '商品_ID'] = 17
        df_products.loc['昼食弁当_ヘルシー','商品_ID'] = 12
        df_products.loc['昼食弁当_並',    'メイン分類'] = 'メイン'
        df_products.loc['昼食弁当_大',    'メイン分類'] = 'メイン'
        df_products.loc['昼食弁当_ヘルシー','メイン分類'] = 'ヘルシー'
        
        # 食べれないメニューがあった時の弁当をどれに変更するか
        df_products.loc['昼食弁当_並','メニューNG変更先'] = '昼食弁当_ヘルシー'
        df_products.loc['昼食弁当_大','メニューNG変更先'] = '昼食弁当_ヘルシー'
        df_products.loc['昼食弁当_ヘルシー','メニューNG変更先'] = '昼食弁当_並'
    else:
        df_products = pd.DataFrame(index = ['夕食弁当_並','夕食惣菜セット',
                                            '夕食弁当_幕の内','夕食惣菜_幕の内'],
                               columns = ['商品_ID','メイン分類','メニュー_ID',
                                          'メニュー_名','同メニュー過去回数','pop'])
        df_products.loc['夕食弁当_並',     '商品_ID'] = 34
        df_products.loc['夕食惣菜セット',     '商品_ID'] = 24
        df_products.loc['夕食弁当_幕の内','商品_ID'] = 35
        df_products.loc['夕食惣菜_幕の内','商品_ID'] = 22
        df_products.loc['夕食弁当_並',    'メイン分類'] = 'A'
        df_products.loc['夕食惣菜セット',    'メイン分類'] = 'A'
        df_products.loc['夕食弁当_幕の内','メイン分類'] = 'B'
        df_products.loc['夕食惣菜_幕の内','メイン分類'] = 'B'
        
        # 食べれないメニューがあった時の弁当をどれに変更するか
        df_products.loc['夕食弁当_並','メニューNG変更先'] = '夕食弁当_幕の内'
        df_products.loc['夕食惣菜セット','メニューNG変更先'] = '夕食惣菜_幕の内'
        df_products.loc['夕食弁当_幕の内','メニューNG変更先'] = '夕食弁当_並'
        df_products.loc['夕食惣菜_幕の内','メニューNG変更先'] = '夕食惣菜セット'

    return df_products

#%%
def main(instance,db,lunch_diner,df_products,predict_daytime,predict_day,
         now_daytime,term_menu,holidays,df_date_menu,df_cus_Ex_base):
    
    df_cus_Ex = copy.copy(df_cus_Ex_base)
    
    from_day = now_daytime - datetime.timedelta(days=term_menu)
    end_day = now_daytime - datetime.timedelta(days=2)
    
    dict_col_list = {'商品名':df_products.index,
                     '顧客ID':df_cus_Ex.index
                     }
    
    df_orderd = SQL2DF.read_products_data_chose_day_time(dict_col_list,instance,db,
                                     now_daytime,from_day,end_day,lunch_diner)
    df_orderd = df_orderd.set_index('日付')
    
    # 祝日は除く
    df_orderd_NH = df_orderd[~df_orderd.index.isin(holidays)]
    
    # 結合
    df_order_menu = df_orderd_NH.join(df_date_menu)
    
    # df_order_menuの日付をインデックスから外す
    df_order_menu_for_Ex = copy.copy(df_order_menu)
    df_order_menu_for_Ex['日付'] = df_order_menu_for_Ex.index
    df_order_menu_for_Ex.index = range(len(df_order_menu_for_Ex))
    
    
    for customID in df_cus_Ex.index:
        df_tmp = df_order_menu_for_Ex[df_order_menu_for_Ex['顧客ID']==customID]
        # データ数が少ないまたは予想日のメニューを以前に頼んでいない顧客は除く
        if len(df_tmp) > 5:
            df_products_for_Ex = copy.copy(df_products)
            for m in df_products['メイン分類'].unique():
                tmp_index = df_products[df_products['メイン分類']==m].index[0]
                tmp_menuID = df_products.loc[tmp_index,'メニュー_ID']
                if not tmp_menuID in df_tmp['ID_'+m].to_list():
                    df_products_for_Ex = df_products_for_Ex[df_products_for_Ex['メイン分類']!=m]
            df_cus = pd.DataFrame(columns = df_tmp.columns)
            for p in df_products_for_Ex.index:
                df_cus = pd.concat([df_cus,df_tmp[df_tmp['商品名']==p]])
            
            if len(df_cus)>0:
                results_pop = caluculate_Ex_pop(
                                customID,instance,db,lunch_diner,predict_daytime,
                                now_daytime,df_date_menu,holidays,predict_day,
                                df_products_for_Ex,df_cus)
#                print(results_pop)
                
                for m in results_pop.columns:
                    if results_pop.loc['num',m] > 1:
                        t_pop = results_pop.loc['pop',m]
                        t_sum_pop = results_pop.loc['sum_pop',m]
                        if t_pop * t_sum_pop > 0: # 同符号の場合
                            if abs(t_sum_pop) > abs(t_pop):
                                t_sum_pop = t_pop
                            m_index = df_products_for_Ex[df_products_for_Ex['メイン分類']==m].index
                            df_tmp = df_cus_Ex.loc[customID,m_index]
                            bosuu = df_tmp.sum()
                            
#                            print('-------元データ-------')
#                            print(df_cus_Ex.loc[customID,:])
                            
                            # 数変動分
                            df_tmp_s = df_tmp/bosuu*t_sum_pop 
                            df_cus_Ex.loc[customID,m_index] += df_tmp_s
#                            print('-------数変動分-------')
#                            print(df_cus_Ex.loc[customID,:])
                            
                            # メニュー間変動分
                            not_m_index = df_products_for_Ex[df_products_for_Ex['メイン分類']!=m].index
                            df_tmp_not = df_cus_Ex.loc[customID,not_m_index]
                            bosuu_not = df_tmp_not.sum()+0.0000000001
                            tmp_m_num = t_pop-t_sum_pop
                            if tmp_m_num > bosuu_not:
                                tmp_m_num = bosuu_not
                            df_tmp_not = df_tmp_not/bosuu_not*tmp_m_num
                            if df_tmp_not.sum() == 0:
                                df_tmp_not = tmp_m_num / len(df_tmp_not)
                            df_cus_Ex.loc[customID,not_m_index] -= df_tmp_not #メニュー変動マイナス分
#                            print('-------メニュー変動マイナス分-------')
#                            print(df_cus_Ex.loc[customID,:])
                            
                            df_tmp_m = df_tmp/bosuu*tmp_m_num
                            df_cus_Ex.loc[customID,m_index] += df_tmp_m #メニュー変動プラス分
#                            print('-------メニュー変動プラス分-------')
#                            print(df_cus_Ex.loc[customID,:])
                            
    return df_cus_Ex

#%%  テスト用
#instance = "OFUKURO-SERVER" #DEVELOP OFUKURO-SERVER  A561C
#db = "鈴鹿店" # 鈴鹿店 四日市店
#lunch_diner = '01' # 昼：01  夕:02
#df_products = df_products_lunch_diner(lunch_diner)
#customID = 2770
#predict_daytime = datetime.datetime(2021,2,3,0,0)
#predict_day = datetime.date(predict_daytime.year
#                        ,predict_daytime.month
#                        ,predict_daytime.day)
#now_daytime = datetime.datetime(2021,2,2,0,0)
#term_menu = 120
#term_holi_closed_menu_days = 180
#holi_closed_menu_from_day = predict_daytime \
#                        - datetime.timedelta(days=term_holi_closed_menu_days)
#holidays = SQL2DF.get_holiday(instance,holi_closed_menu_from_day
#                                      ,predict_daytime)
#df_date_menu = SQL2DF.get_menu(lunch_diner,holi_closed_menu_from_day,\
#                                   predict_daytime,instance,"献立",df_products['メイン分類'].unique())
##　予想日のメニュー情報
#for p in df_products.index:
#    main_bunrui = df_products.loc[p,'メイン分類']
#    df_products.loc[p,'メニュー_ID'] = \
#                        df_date_menu.loc[predict_day,'ID_' + main_bunrui]
#    df_products.loc[p,'メニュー_名'] = \
#                        df_date_menu.loc[predict_day,'name_' + main_bunrui]
#    df_products.loc[p,'同メニュー過去回数'] = \
#                    len(df_date_menu[df_date_menu['ID_' + main_bunrui]==
#                     df_products.loc[p,'メニュー_ID']])-1
#
#df_cus_Ex3 = main(instance,db,lunch_diner,df_products,predict_daytime,predict_day,
#         now_daytime,term_menu,holidays,df_date_menu,df_cus_Ex2)

    
