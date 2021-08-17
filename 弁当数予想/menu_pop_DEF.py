# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 21:39:37 2020

@author: user
"""

import datetime
import SQL2DF
import pandas as pd
import copy

#%%
def agri_menu(df_menu_MH,holidays):
    df_agri_menu_M = pd.DataFrame(index = df_menu_MH['料理ID_M'].unique(),
                              columns = [0,1,2,3,4,5,6])
    df_agri_menu_M = df_agri_menu_M.fillna(0)
    
    df_agri_menu_H = pd.DataFrame(index = df_menu_MH['料理ID_H'].unique(),
                                  columns = [0,1,2,3,4,5,6])
    df_agri_menu_H = df_agri_menu_H.fillna(0)
    
    for d in df_menu_MH.index:
        menu_M = df_menu_MH.loc[d,'料理ID_M']
        menu_H = df_menu_MH.loc[d,'料理ID_H']
        youbi  = df_menu_MH.loc[d,'曜日']
        df_agri_menu_M.loc[menu_M,youbi] = df_agri_menu_M.loc[menu_M,youbi]+1
        df_agri_menu_H.loc[menu_H,youbi] = df_agri_menu_H.loc[menu_H,youbi]+1
        
#        d2 = datetime.date(d.year, d.month, d.day)
#        if d2 in holidays:
#            if youbi < 5: #平日
#                tmpH = 'HW'
#            else: #休日
#                tmpH = 'HE'
#    
#            df_agri_menu_M.loc[menu_M,tmpH] = df_agri_menu_M.loc[menu_M,tmpH]+1
#            df_agri_menu_H.loc[menu_H,tmpH] = df_agri_menu_H.loc[menu_H,tmpH]+1
            
    return [df_agri_menu_M,df_agri_menu_H]

 #%% メニューのデータを取得
def get_menu_data(instance,lunch_diner,predict_day,str_from_day,str_end_day,holidays):
    db = "献立"
    if lunch_diner == '01':
        str_lunch_diner = '昼'
    else:
        str_lunch_diner = '夕'
    
    
    df_menu_MH = INPUT_MENU.input_menu_DB(str_lunch_diner,str_from_day,\
                                       str_end_day,instance,db)
    
    df_menu_MH.loc[datetime.datetime(2020,8,25,0,0,0),'料理名_M'] = '若鶏の柚子胡椒焼き'
    df_menu_MH.loc[datetime.datetime(2020,8,25,0,0,0),'料理ID_M'] = 132
    df_menu_MH.loc[datetime.datetime(2020,8,25,0,0,0),'料理名_H'] = '赤魚の煮付け'
    df_menu_MH.loc[datetime.datetime(2020,8,25,0,0,0),'料理ID_H'] = 270
    df_menu_MH.loc[datetime.datetime(2020,8,25,0,0,0),'曜日'] = 1
    
    df_menu_MH = df_menu_MH.sort_index()
    
    #print(df_menu_MH)
        
    # 祝日は除く
    df_menu_MH = df_menu_MH[~df_menu_MH.index.isin(holidays)]
    
    return df_menu_MH

 
#%%

def menu_MH_holidays(predict_day,term,instance,lunch_diner):
    
    from_day = predict_day - datetime.timedelta(days=term)
    end_day = predict_day - datetime.timedelta(days=1)
    end_day_0 = predict_day - datetime.timedelta(days=0)
    #祝日を抽出
    str_from_day = from_day.strftime('%Y-%m-%d')
    str_end_day = end_day.strftime('%Y-%m-%d')
    str_end_day_0 = end_day_0.strftime('%Y-%m-%d')
    holidays = SQL2DF.get_holiday(instance,str_from_day,str_end_day_0)
    
    df_menu_MH = get_menu_data(instance,lunch_diner,predict_day,str_from_day,str_end_day,holidays)
    
    return [df_menu_MH,holidays]

#%% INPUT
#predict_day = datetime.datetime(2020,9,2,0,0)
#term = 120
#
#pre_products = [ '昼食弁当_並', '昼食弁当_大','昼食弁当_ヘルシー']
#products2main_menu = {'昼食弁当_並':'M','昼食弁当_大':'M','昼食弁当_ヘルシー':'H'}
#
#customID =  4110 # 4110 3848  # 2076
#instance = "DEVELOP" #DEVELOP OFUKURO-SERVER  A561C
#
#db = "鈴鹿店" # 鈴鹿店 四日市店
#lunch_diner = '01' # 昼：01  夕:02
#
#df_menu_pop = main_menu_pop(predict_day,term,pre_products,products2main_menu,customID,
#                  instance,db,lunch_diner)



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
                for m in df_products['メイン分類']:
                    base = df_around[m].mean()
                    df_order_date.loc[i,m+'_base'] = base
                    if base == 0:
                        df_order_date.loc[i,m+'_pop'] = 1
                    else:
                        df_order_date.loc[i,m+'_pop'] = df_order_date.loc[i,m]/base
            else:
                for m in df_products['メイン分類']:
                    df_order_date.loc[i,m+'_base'] = 0
                    df_order_date.loc[i,m+'_pop'] = 1
#    print(df_order_date)
    #%%　人気度の計算
    df_menu_pop = pd.DataFrame()
    for m in df_products['メイン分類']:
        for mid in df_order_date['ID_'+m].unique():
            df_tmp = df_order_date[df_order_date['ID_'+m]==mid]
            n = len(df_tmp)
            if n > 1:
                df_menu_pop.loc[mid,'num'] = n
                tmp_pop = df_tmp[m+'_pop'].mean()
                if tmp_pop > 2:
                    tmp_pop = 2
                if tmp_pop < 0.5:
                    tmp_pop = 0.5
                df_menu_pop.loc[mid,'pop'] = tmp_pop
                df_menu_pop.loc[mid,'name'] = df_tmp['name_'+m][df_tmp['name_'+m].index[0]]
            
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
                    for m in df_products['メイン分類']:
                        tmp_ID = df_around.loc[k,'ID_'+m]
                        if tmp_ID in df_menu_pop.index:
                            tmp_pop = df_menu_pop.loc[tmp_ID,'pop']
                        else:
                            tmp_pop = 1
                        df_around.loc[k,m+'_base'] = df_around.loc[k,m]*tmp_pop
                            
            if len(df_around)>0:
                for m in df_products['メイン分類']:
                    base = df_around[m+'_base'].mean()
                    if base == 0:
                        df_order_date.loc[i,m+'_pop'] = 1
                    else:
                        df_order_date.loc[i,m+'_pop'] = df_order_date.loc[i,m]/base
            else:
                for m in df_products['メイン分類']:
                    df_order_date.loc[i,m+'_base'] = 0
                    df_order_date.loc[i,m+'_pop'] = 1
#    print(df_order_date)
    
    #%%　予想日のメニューの人気度の計算
    results_pop = pd.DataFrame()
    for m in df_products['メイン分類']:
        tmp_index = df_products[df_products['メイン分類']==m].index[0]
        tmp_ID = df_products.loc[tmp_index,'メニュー_ID']
        df_tmp = df_order_date[df_order_date['ID_'+m]==tmp_ID]
        if len(df_tmp)>0:
            results_pop.loc['pop',m] = df_tmp[m+'_pop'].mean()
            results_pop.loc['num',m] = len(df_tmp)
        else:
            results_pop.loc['pop',m] = 1
            results_pop.loc['num',m] = 0
#    print(results_pop)
    
    return results_pop
    

#%%
def caluculate_Ex_pop_main(instance,db,lunch_diner,df_products,now_daytime,
                           term_menu,df_cus_prob,holidays,df_date_menu,
                           predict_daytime,predict_day,df_cus_Ex):
    #顧客ごとの統計
    from_day = now_daytime - datetime.timedelta(days=term_menu)
    end_day = now_daytime - datetime.timedelta(days=2)
    
    dict_col_list = {'商品名':df_products.index,
                     '顧客ID':[2770,8551,3920,9827,3790,3026,3556,7547,4731,9784,8493,9269,9492
                      ,3370,9587,9169,3882,1327,4363,8657,5349,2813,4471,3130,9755,4131]#df_cus_prob.index
                     }

    df_orderd = SQL2DF.read_products_data_chose_day_time(dict_col_list,instance,db,
                                     now_daytime,from_day,end_day,lunch_diner)
    
    df_orderd = df_orderd.set_index('日付')

    # 祝日は除く
    df_orderd_NH = df_orderd[~df_orderd.index.isin(holidays)]
    
    # 結合
    df_order_menu = df_orderd_NH.join(df_date_menu)
    
    #%%
    # df_order_menuの日付をインデックスから外す
    df_order_menu_for_Ex = copy.copy(df_order_menu)
    df_order_menu_for_Ex['日付'] = df_order_menu_for_Ex.index
    df_order_menu_for_Ex.index = range(len(df_order_menu_for_Ex))
    
    #%% メニューを反映させた期待値        
    for customID in df_cus_prob.index:
#        print(customID)
        # データ数が少ないまたは予想日のメニューを以前に頼んでいない顧客は除く
        df_tmp = df_order_menu_for_Ex[df_order_menu_for_Ex['顧客ID']==customID]
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
                
                df_cus_Ex_menu = pd.DataFrame()
                for p in df_products_for_Ex.index:
                    tmp_pop = results_pop.loc['pop',df_products_for_Ex.loc[p,'メイン分類']]
                    df_cus_Ex_menu.loc[customID,p] = df_cus_Ex.loc[customID,p] * tmp_pop
                Ex_SUM = df_cus_Ex.loc[customID].sum() #種類関係なく　弁当の総数の予想
                Ex_menu_SUM = df_cus_Ex_menu.loc[customID].sum() #popを反映した期待値の総計    
                
                for m in results_pop.columns:
                    df_tmp_products = df_products_for_Ex[df_products_for_Ex['メイン分類']==m]
                    M_Ex_SUM = df_cus_Ex.loc[customID,df_tmp_products.index].sum()+0.00000001
                    for p in df_tmp_products.index:
                        df_cus_Ex.loc[customID,p] = df_cus_Ex_menu.loc[customID,p]/Ex_menu_SUM*Ex_SUM \
                                                    *(df_cus_Ex.loc[customID,p]/M_Ex_SUM)
#                        print(df_cus_Ex.loc[customID,p])

    return df_cus_Ex