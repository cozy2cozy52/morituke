# -*- coding: utf-8 -*-
"""
Created on Mon Nov 30 14:17:28 2020

@author: user
"""

import datetime
import 弁当数予想.SQL2DF as SQL2DF
import pandas as pd
import 弁当数予想.order_timeDEF as ORD_TIME
#import menu_pop2
import os
import 弁当数予想.Write_DB as Write_DB
import copy

#%% 予想日から予想に使うデータの日付を取り出す
def pick_up_date_for_data(predict_day,now_daytime,
                          term,term_holi,holidays,closed_days,
                          holi_closed_menu_from_day,predict_daytime):
    
    # 予想データ除外日の読み込み
    except_days = SQL2DF.get_except_days(holi_closed_menu_from_day,predict_daytime)
#    print(except_days)
    
    now_day = datetime.date(now_daytime.year,now_daytime.month,now_daytime.day)
    cand_days = []
    if (predict_day in holidays) & (predict_day.weekday() < 5):#祝日で平日
        for hd in holidays[1:-1]: # holidaysの最初は予想日なので除く
            if (hd.weekday() < 5) & (hd < now_day)& (not hd in except_days):# 平日の場合
                cand_days.append(hd) # 候補日追加
                if len(cand_days)>=term_holi:
                    break
    else: #祝日でない平日または土日の場合
        d = predict_day - datetime.timedelta(days=7)
        t=0
        while t < term:
            if (d < now_day) & (not d in holidays) & (not d in closed_days) \
                                                   & (not d in except_days):
                cand_days.append(d)
                t += 1
            d -= datetime.timedelta(days=7)

    return cand_days

#%%
def caluculate_Ex_base(df_data,products_Name):
    df_cus_Ex = pd.DataFrame()
    df_cus_prob = pd.DataFrame()
    bosuu = len(df_data['日付'].unique())
    for id1 in df_data['顧客ID']:
        df_tmp_id = df_data[df_data['顧客ID']==id1]
        cancel_num = len(df_tmp_id[df_tmp_id['キャンセル']==1])
        bosuu_id = bosuu - cancel_num
        if bosuu_id > 0:
            for p in products_Name:
                df_tmp_p = df_tmp_id[df_tmp_id['商品名']==p]
                df_cus_Ex.loc[id1,p] = df_tmp_p['個数'].sum()/bosuu_id
            df_cus_prob.loc[id1,'注文確率'] = len(df_tmp_id['日付'].unique())/bosuu
    return [df_cus_Ex,df_cus_prob]

#%%
def INPUT_DB_Data(db,lunch_diner,now_daytime,past_data_days,products):
    
    str_data_days = []
    for d in past_data_days:
        str_data_days.append(SQL2DF.datetime2otodokeday(d))
                  
    dict_col_list = { '日付': str_data_days,
                      '商品名':products}
    df_data = SQL2DF.read_products_data_chose_day_time(
                                dict_col_list,db,now_daytime
                                ,past_data_days[-1],past_data_days[0]
                                 ,lunch_diner)
    return df_data

#%%
def make_time_over(df_order_time,predict_day,predict_daytime,now_daytime,db,lunch_diner,sn):
    # 最終時刻が今現在の時刻を過ぎていれば候補から除外
    df_time_over = pd.DataFrame(columns = df_order_time.columns)
    n=0
    thresh_time = now_daytime-predict_daytime
    
    # 締切時刻の0.5時間前より現在時刻が後の時刻の時は注文平均時刻を過ぎたら候補から外す
    if thresh_time > datetime.timedelta(days=-1, seconds=84600): # 締切0.5時間より後
        str_thre_time = '1/2時刻'
    else: # 締切0.5時間より前
        str_thre_time = '3/4時刻'
#    print(str_thre_time)
    for i in df_order_time.index:
        if thresh_time > df_order_time.loc[i,str_thre_time]:
            df_time_over.loc[n] = df_order_time.loc[i]
            n += 1
            df_order_time = df_order_time.drop(i)
            
    f_name = '弁当数予想/注文平均時刻の顧客リスト/平均時刻顧客リスト' + db + lunch_diner + '_' + \
                str(predict_day) + '_' + str(sn) +'.pkl'
    df_order_time.to_pickle(f_name)
    
    # df_time_overを人が見やすい形にする
    df_time_over = df_time_over.sort_values('1/2時刻')
    #df_time_over['1/2時刻'] = df_time_over['1/2時刻']+predict_daytime
    df_time_over = df_time_over.drop('3/4時刻',axis=1)
    df_time_over = df_time_over.set_index('顧客ID')
    
    f_name = '弁当数予想/注文時刻切れの顧客リスト/時刻切れ顧客リスト' + db + lunch_diner + '_' + \
                str(predict_day) + '_' + str(sn) +'.csv'
    if os.path.isfile(f_name):
        df_time_over_read = pd.read_csv(f_name, index_col=0)
        df_time_over_new = pd.concat([df_time_over_read, df_time_over])
    else:
        df_time_over_new = df_time_over
    
    return [df_time_over_new,df_order_time]
#%%
def squeeze_candidate(db,now_daytime,predict_daytime,df_products,
                      lunch_diner,df_past_data,dead_time,holidays,sn,predict_day):
    
    # 祝日不要
    if predict_daytime in holidays:
        dict_col_list = {'顧客ID':df_past_data['顧客ID'].unique()}
        df_Non_holiday_order = SQL2DF.get_Non_holiday_order(db,dict_col_list)
    #    print(df_Non_holiday_order)
    
    #　定期購入
    df_subscription = SQL2DF.subscribe(db,predict_daytime,df_products,lunch_diner)
#    df_subscription.to_csv('df_subscription.csv',encoding='utf_8_sig')
#    print(df_subscription)
    
    # すでに注文している顧客の抽出
    df_pre_orderd = SQL2DF.read_products_data_chose_day_time(
                                {},db,now_daytime,
                                predict_daytime,predict_daytime,lunch_diner)
#    print(df_pre_orderd)
    
    # df_pre_orderdに定期購入を加える
    predict_daytime00 = datetime.datetime(predict_daytime.year
                                    ,predict_daytime.month
                                    ,predict_daytime.day
                                    ,0,0,0)
    
    if (predict_daytime-now_daytime) >= datetime.timedelta(days=7):
        if len(df_pre_orderd)>0:
            p = df_pre_orderd.index[-1]+1
        else:
            p = 0
        for s in df_subscription.index:
            if not df_subscription.loc[s,'顧客ID'] in df_pre_orderd['顧客ID'].to_list():
                df_pre_orderd.loc[p,'日付'] = predict_daytime00
                df_pre_orderd.loc[p,'顧客ID'] = df_subscription.loc[s,'顧客ID']
                df_pre_orderd.loc[p,'商品名'] = df_subscription.loc[s,'商品名']
                df_pre_orderd.loc[p,'個数']   = df_subscription.loc[s,'個数']
                df_pre_orderd.loc[p,'キャンセル']   = 0
                p += 1
    #    print(df_pre_orderd)
    
    # 予想日より後に注文している顧客データの取り出し
#    predict_daytime_30 = predict_daytime+datetime.timedelta(days=30)
#    dict_col_list = { '顧客ID': df_past_data['顧客ID'].to_list(),
#                      '商品名':df_products.index}
#    
#    df_after30_data = SQL2DF.read_products_data_chose_day_time(
#                                dict_col_list,db,now_daytime,
#                                predict_daytime,predict_daytime_30,
#                                lunch_diner)
#    print(df_after30_data)

    # 各情報からデータフレームを削除
    if predict_daytime in holidays:
        df_past_data = df_past_data[~df_past_data['顧客ID'].isin(df_Non_holiday_order['顧客ID'])]
    df_past_data = df_past_data[~df_past_data['顧客ID'].isin(df_subscription['顧客ID'])]
    df_past_data = df_past_data[~df_past_data['顧客ID'].isin(df_pre_orderd['顧客ID'])]
#    df_past_data = df_past_data[~df_past_data['顧客ID'].isin(df_after30_data['顧客ID'])]
    
    
    # 注文時刻の平均と最終を出す
    df_order_time = ORD_TIME.order_time_df(df_past_data,dead_time)
#    print(df_past_data)

    # 時刻切れの顧客を出す
    [df_time_over,df_order_time] = make_time_over(
                            df_order_time,predict_day,predict_daytime,
                            now_daytime,db,lunch_diner,sn)

    # 各情報からデータフレームを削除
    df_past_data = df_past_data[df_past_data['顧客ID'].isin(df_order_time['顧客ID'])]
    
    return [df_past_data,df_pre_orderd,df_time_over]


#%%
def df_products_lunch_diner(lunch_diner):
    if lunch_diner == '01':
        df_products = pd.DataFrame(index = \
        ['昼食弁当_並','昼食弁当_大','お魚弁当_並','お魚弁当_大',
         'からあげ弁当_並','からあげ弁当_大','ハンバーグ弁当_並',
         'ハンバーグ弁当_大','冷やしうどん','冷やしそば'],
        columns = ['商品_ID','メイン分類','メニュー_ID',
                    'メニュー_名','同メニュー過去回数','pop',
                     'メニューNG変更先'])
        df_products.loc['昼食弁当_並','商品_ID'] = 18
        df_products.loc['昼食弁当_大','商品_ID'] = 17
        df_products.loc['お魚弁当_並','商品_ID'] = 98
        df_products.loc['お魚弁当_大','商品_ID'] = 99
        df_products.loc['からあげ弁当_並','商品_ID'] = 111
        df_products.loc['からあげ弁当_大','商品_ID'] = 112
        df_products.loc['ハンバーグ弁当_並','商品_ID'] = 113
        df_products.loc['ハンバーグ弁当_大','商品_ID'] = 114
        df_products.loc['冷やしうどん','商品_ID'] = 115
        df_products.loc['冷やしそば','商品_ID'] = 116
        df_products.loc['お野菜弁当','商品_ID'] = 117
        df_products.loc['昼食弁当_彩','商品_ID'] = 15
        df_products.loc['季節のお弁当','商品_ID'] = 119
        
        df_products.loc['昼食弁当_並','メイン分類'] = '昼日替'
        df_products.loc['昼食弁当_大','メイン分類'] = '昼日替'
        df_products.loc['お魚弁当_並','メイン分類'] = '昼お魚'
        df_products.loc['お魚弁当_大','メイン分類'] = '昼お魚'
        df_products.loc['からあげ弁当_並','メイン分類'] = '昼日替'
        df_products.loc['からあげ弁当_大','メイン分類'] = '昼日替'
        df_products.loc['ハンバーグ弁当_並','メイン分類'] = '昼日替'
        df_products.loc['ハンバーグ弁当_大','メイン分類'] = '昼日替'
        df_products.loc['冷やしうどん','メイン分類'] = '昼日替'
        df_products.loc['冷やしそば','メイン分類'] = '昼日替'
        df_products.loc['お野菜弁当','メイン分類'] = '昼日替'
        df_products.loc['昼食弁当_彩','メイン分類'] = '昼日替'
        df_products.loc['季節のお弁当','メイン分類'] = '昼日替'
        
        # 食べれないメニューがあった時の弁当をどれに変更するか
        df_products.loc['昼食弁当_並','メニューNG変更先'] = 'お魚弁当_並'
        df_products.loc['昼食弁当_大','メニューNG変更先'] = 'お魚弁当_大'
        df_products.loc['お魚弁当_並','メニューNG変更先'] = '昼食弁当_並'
        df_products.loc['お魚弁当_大','メニューNG変更先'] = '昼食弁当_大'
        df_products.loc['からあげ弁当_並','メニューNG変更先'] = '昼食弁当_並'
        df_products.loc['からあげ弁当_大','メニューNG変更先'] = '昼食弁当_並'
        df_products.loc['ハンバーグ弁当_並','メニューNG変更先'] = '昼食弁当_並'
        df_products.loc['ハンバーグ弁当_大','メニューNG変更先'] = '昼食弁当_並'
        df_products.loc['冷やしうどん','メニューNG変更先'] = '昼食弁当_並'
        df_products.loc['冷やしそば','メニューNG変更先'] = '昼食弁当_並'
        df_products.loc['お野菜弁当','メニューNG変更先'] = '昼食弁当_並'
        df_products.loc['昼食弁当_彩','メニューNG変更先'] = '昼食弁当_並'
        df_products.loc['季節のお弁当','メニューNG変更先'] = '昼食弁当_並'
        
    else:
        df_products = pd.DataFrame(index = ['夕食お肉惣菜セット','夕食お魚惣菜セット',
                                            '夕食幕ノ内惣菜セット',
                                            'ご飯_並','ご飯_大'],
                               columns = ['商品_ID','メイン分類','メニュー_ID',
                                          'メニュー_名','同メニュー過去回数','pop'])
        df_products.loc['夕食お肉惣菜セット','商品_ID'] = 100
        df_products.loc['夕食お魚惣菜セット','商品_ID'] = 101
        df_products.loc['夕食幕ノ内惣菜セット','商品_ID'] = 102
        df_products.loc['ご飯_並','商品_ID'] = 103
        df_products.loc['ご飯_大','商品_ID'] = 104
        df_products.loc['夕食お肉惣菜セット','メイン分類'] = '夕お肉'
        df_products.loc['夕食お魚惣菜セット','メイン分類'] = '夕お魚'
        df_products.loc['夕食幕ノ内惣菜セット','メイン分類'] = '夕幕内'
        df_products.loc['ご飯_並','メイン分類'] = '夕幕内'
        df_products.loc['ご飯_大','メイン分類'] = '夕幕内'
        
        # 食べれないメニューがあった時の弁当をどれに変更するか
        df_products.loc['夕食お肉惣菜セット','メニューNG変更先'] = '夕食お魚惣菜セット'
        df_products.loc['夕食お魚惣菜セット','メニューNG変更先'] = '夕食お肉惣菜セット'
        df_products.loc['夕食幕ノ内惣菜セット','メニューNG変更先'] = '夕食お肉惣菜セット'
        df_products.loc['ご飯_並','メニューNG変更先'] = '夕食お肉惣菜セット'
        df_products.loc['ご飯_大','メニューNG変更先'] = '夕食お肉惣菜セット'

    return df_products

#%% 顧客NG料理
def delete_NG_Ex(df_cus_Ex,df_products,db):
    # 読み込み
    dict_col_list = {'顧客ID':df_cus_Ex.index,
                     '料理ID':df_products['メニュー_ID'].unique()}
    df_NG_menu = SQL2DF.get_NG_menu(db,dict_col_list)
    #        print(df_NG_menu)
    
    # 数変更
    if len(df_NG_menu) > 0:
        for i_NG in df_NG_menu.index:
            cID = df_NG_menu.loc[i_NG,'顧客ID']
            NG_menu_ID = df_NG_menu.loc[i_NG,'料理ID']
            NG_products = df_products[df_products['メニュー_ID']==NG_menu_ID].index
            for i_np in NG_products:
                new_product = df_products.loc[i_np,'メニューNG変更先']
                df_cus_Ex.loc[cID,new_product] += df_cus_Ex.loc[cID,i_np]
                df_cus_Ex.loc[cID,i_np] = -1000
        df_cus_Ex[df_cus_Ex < 0] = 0
    
#%% 
def get_nth_week(day):
    return (day - 1) // 7 + 1

#%% 祝日が少ない時にエラーメッセージを出す
def output_Error_file_holiday(lunch_diner,predict_day):
    path_w = 'Error\E_' + lunch_diner + '_' + str(predict_day) +'.txt'        
    s = '祝日数が少ないので予想できませんでした。'
    with open(path_w, mode='w') as f:
        f.write(s)
        
#%% 祝日が少ない時にエラーメッセージを出す
def output_Error_file_closed(lunch_diner,predict_day):
    path_w = 'Error\E_' + lunch_diner + '_' + str(predict_day) +'.txt'        
    s = '予想日は休業日です。'
    with open(path_w, mode='w') as f:
        f.write(s)
        
#%% 祝日、休業日、メニューの読み込み
def Input_holday_closed_menu(term_holi,predict_day,lunch_diner,df_products,
                             predict_daytime_input,term_holi_closed_menu_days):
    #祝日、休業日の読み込み開始日
    holi_closed_menu_from_day = predict_daytime_input \
                            - datetime.timedelta(days=term_holi_closed_menu_days)
    
    #% 祝日の読み込み    holidays list datetime.date
    holidays = SQL2DF.get_holiday(holi_closed_menu_from_day
                                          ,predict_daytime_input)
    holidays.reverse() #逆順にする

    # 予想日が祝日で、祝日数が少なかったら終わる
    if (len(holidays)<term_holi+1) & (predict_day in holidays):
        output_Error_file_holiday(lunch_diner,predict_day)
        return [[],[]] # break
    
    #% 休業日の読み込み  closed_days list datetime.date
    closed_days = SQL2DF.get_closed_days(holi_closed_menu_from_day
                                              ,predict_daytime_input
                                              ,lunch_diner)
    # 祝日が少なかったら終わる
    if predict_day in closed_days:
        output_Error_file_closed(lunch_diner,predict_day)
        return [[],[]] # break
    
    #%メニュー読み込み       
    df_date_menu = SQL2DF.get_menu(lunch_diner,holi_closed_menu_from_day,\
                                       predict_daytime_input,"献立",
                                       df_products['メイン分類'].unique())
        
    #　予想日のメニュー情報
    for p in df_products.index:
        main_bunrui = df_products.loc[p,'メイン分類']
        if (predict_day,'ID_' + main_bunrui) in df_date_menu:
            df_products.loc[p,'メニュー_ID'] = \
                                df_date_menu.loc[predict_day,'ID_' + main_bunrui]
            df_products.loc[p,'メニュー_名'] = \
                                df_date_menu.loc[predict_day,'name_' + main_bunrui]
            df_products.loc[p,'同メニュー過去回数'] = \
                            len(df_date_menu[df_date_menu['ID_' + main_bunrui]==
                             df_products.loc[p,'メニュー_ID']])-1
            
    return [holidays,closed_days,holi_closed_menu_from_day,df_date_menu]

#%% 
def update_db_list(db_list_Input,predict_day,lunch_diner):
    db_list = copy.copy(db_list_Input)
    if (predict_day.weekday() == 6) & ("四日市店" in db_list):#四日市の日曜はなし
        db_list.remove('四日市店')
    if (predict_day.weekday() > 4) & (lunch_diner == '02'):#夕食の土日はなし
        db_list.clear()
    if (lunch_diner == '02') & ("四日市店" in db_list):#夕食は四日市なし
        db_list.remove('四日市店')
    return db_list

#%%
def plus_dead_time(lunch_diner,db,predict_daytime_input):
    if lunch_diner == '01':
        if db == "鈴鹿店":
            dead_time = datetime.timedelta(hours=10)
        else:
            dead_time = datetime.timedelta(hours=9.5)
    else:
        dead_time = datetime.timedelta(hours=15)
    
    predict_daytime = datetime.datetime(
                        predict_daytime_input.year,
                        predict_daytime_input.month,
                        predict_daytime_input.day,
                        0,0,0)
    predict_daytime += dead_time
    
    return(predict_daytime,dead_time)

#%%
def update_Ex(predict_daytime,now_daytime):
    #データ更新するか
    time_del = predict_daytime - now_daytime
    if time_del<datetime.timedelta(days=6):
        sn = 1
    elif time_del<datetime.timedelta(days=13):
        sn = 2
    else:
        sn = 3
        
    return sn

#%%
def write_DB_results(df_agri_results,lunch_diner,predict_day):
    for s in df_agri_results.index:
        store = s
        if lunch_diner == '02':
            store = '夕' + s
        for p in df_agri_results.columns:
            n = df_agri_results.loc[s,p]
            Write_DB.write_predict("DEVELOP",store,p,n,predict_day)
#%% 期待値を読み込んで、新しい注文を反映させて予想数を更新する
def read_Ex_and_update_predict(f_name_order,f_name_Ex,f_name_prob,db,lunch_diner,sn,
                               predict_daytime,predict_day,now_daytime,df_products):
    # df_order_timeの読み込み
    df_order_time = pd.read_pickle(f_name_order)
    
    # すでに注文している顧客の抽出
    df_pre_orderd = SQL2DF.read_products_data_chose_day_time(
                                {},db,now_daytime,
                                predict_daytime,predict_daytime,lunch_diner)
    df_pre_orderd.to_csv('df_pre_orderd.csv',encoding='utf_8_sig')
    # 注文済みの顧客を外す
    df_order_time = df_order_time[~df_order_time['顧客ID'].isin(df_pre_orderd['顧客ID'])]
    
    # 時刻切れの顧客を出す
    [df_time_over,df_order_time] = make_time_over(
                                    df_order_time,predict_day,
                                    predict_daytime,now_daytime,db,
                                    lunch_diner,sn)
    df_time_over = df_time_over[~df_time_over.index.isin(df_pre_orderd['顧客ID'].unique())]
    
    # 期待値読み込み
    df_cus_Ex = pd.read_csv(f_name_Ex,encoding='utf_8_sig', index_col=0)
    df_cus_prob = pd.read_csv(f_name_prob,encoding='utf_8_sig', index_col=0)
    
    # 注文済みのものを外す
    df_cus_Ex = df_cus_Ex[~df_cus_Ex.index.isin(df_pre_orderd['顧客ID'].unique())]
    df_cus_prob = df_cus_prob[~df_cus_prob.index.isin(df_pre_orderd['顧客ID'].unique())]
    
    # 時間切れの顧客を外す
    df_cus_Ex = df_cus_Ex[~df_cus_Ex.index.isin(df_time_over.index.unique())]
    df_cus_prob = df_cus_prob[~df_cus_prob.index.isin(df_time_over.index.unique())]
    
    # 時間切れの顧客の期待値
    df_cus_Ex_time_over = df_cus_Ex[df_cus_Ex.index.isin(df_time_over.index.unique())]
    df_cus_Ex_time_over = df_cus_Ex_time_over[df_products.index].sum(axis=1)
    
    return [df_cus_Ex,df_cus_prob,df_cus_Ex_time_over,df_pre_orderd,df_time_over]

#%%
def make_Ex(db,lunch_diner,
            predict_day,predict_daytime,now_daytime,
            term,term_holi,holidays,closed_days,holi_closed_menu_from_day,
            df_products,dead_time,sn,term_menu,df_date_menu):
    #データとして使う過去の日にちを出す
    past_data_days = pick_up_date_for_data(predict_day,now_daytime,
                              term,term_holi,holidays,closed_days,
                              holi_closed_menu_from_day,predict_daytime)
#    print('---------past_data_days---------------------------------')
#    print(past_data_days)

    #%　予想のためのデータを読み込む
    df_past_data = INPUT_DB_Data(db,lunch_diner,now_daytime
                                 ,past_data_days,df_products.index)
#    print('---------df_past_data---------------------------------')
#    print(df_past_data)


    ##################% 顧客の絞り込み
    [df_past_data_sq,df_pre_orderd,df_time_over] = \
                    squeeze_candidate(db,now_daytime,predict_daytime,
                                      df_products,lunch_diner,df_past_data,
                                      dead_time,holidays,sn,predict_day)
#    print('---------df_past_data_sq---------------------------------')
#    print(df_past_data_sq)
    

    #################% 顧客の定休週日
    # 読み込み
    week_day = SQL2DF.youbi_python2DB(predict_daytime.weekday())
    nth_week = get_nth_week(predict_daytime.day)
    dict_col_list = {'顧客ID':df_past_data_sq['顧客ID'].unique(),
                     '曜日':[week_day],
                     '週番':[nth_week]}
    df_custom_regular_holidays = \
                SQL2DF.get_custom_regular_holidays(db,dict_col_list)
    #        print(df_custom_regular_holidays)
    
    # 該当する顧客を削除
    for c_i in df_custom_regular_holidays.index:
        cID = df_custom_regular_holidays.loc[c_i,'顧客ID']
        df_past_data_sq = df_past_data_sq[df_past_data_sq['顧客ID']!=cID]
        df_time_over = df_time_over[df_time_over.index!=cID]

    #% 期待値基本
    [df_cus_Ex_base,df_cus_prob] = \
        caluculate_Ex_base(df_past_data_sq,df_products.index)
    df_cus_Ex = df_cus_Ex_base
    
    #% メニューを反映させた期待値
    # if (df_products.loc[:,'メニュー_ID'] < 0).sum() == 0: # メニューがすべて登録されている
    #     df_cus_Ex_menu = menu_pop2.main(db,lunch_diner,df_products,predict_daytime,predict_day,
    #      now_daytime,term_menu,holidays,df_date_menu,df_cus_Ex_base)
        
    #     df_cus_Ex_menu[df_products.index] = \
    #             df_cus_Ex_menu[df_products.index].where(df_cus_Ex_menu[df_products.index] >= 0, 0)
    #     df_cus_Ex = df_cus_Ex_menu  

    #% df_cus_Exに顧客名を付ける
    for customID in df_cus_Ex.index:
        c_i = df_past_data_sq[df_past_data_sq['顧客ID']==customID].index[0]
        df_cus_Ex.loc[customID,'顧客名'] = df_past_data_sq.loc[c_i,'顧客名']
        df_cus_prob.loc[customID,'顧客名'] = df_past_data_sq.loc[c_i,'顧客名']
    
    #注文確率
    df_cus_prob = df_cus_prob[df_cus_prob['注文確率']>0.5]
    df_cus_prob = df_cus_prob[~df_cus_prob.index.isin(df_pre_orderd['顧客ID'].unique())]

    #df_past_data_sq.to_csv('data_sq.csv',encoding='utf_8_sig')
    
    f_name = '弁当数予想/注文予想の顧客リスト/予想顧客リスト' + db + lunch_diner + '_' + \
                str(predict_day) + '_' + str(sn) +'.csv'
    df_cus_Ex.to_csv(f_name,encoding='utf_8_sig')
    f_name = '弁当数予想/注文予想の顧客リスト/予想顧客リスト' + db + lunch_diner + '_' + \
                str(predict_day) + '_' + str(sn) +'_prob.csv'
    df_cus_prob.to_csv(f_name,encoding='utf_8_sig')

    #% 期待値 時刻切れ
    df_past_data_time_over = df_past_data[df_past_data['顧客ID'].isin(df_time_over.index.unique())]
    [df_cus_Ex_time_over,df_cus_prob_time_over] = \
        caluculate_Ex_base(df_past_data_time_over,df_products.index)
    df_cus_Ex_time_over = df_cus_Ex_time_over.sum(axis=1)
    return [df_cus_Ex,df_cus_Ex_time_over,df_pre_orderd,df_time_over,df_cus_prob]

#%%
def update_save_df_time_over(db,lunch_diner,df_time_over,df_cus_Ex_time_over,
                             predict_day,sn):
    # 時刻切れの顧客で期待値が低いものは外す
    for ii in df_cus_Ex_time_over.index:
        if df_cus_Ex_time_over[ii] < 0.5:
            df_time_over = df_time_over.drop(ii)
    
    f_name = '弁当数予想/注文時刻切れの顧客リスト/時刻切れ顧客リスト' + db + lunch_diner + '_' +\
                str(predict_day) + '_' + str(sn) +'.csv'
    df_time_over.to_csv(f_name,encoding='utf_8_sig')
    
    return df_time_over

#%%
def agri_orderd(df_pre_orderd,df_products):
    df_agri_orderd = pd.DataFrame()
    df_pre_orderd_NonCancel = df_pre_orderd[df_pre_orderd['キャンセル']==0]
    for p in df_products.index:
        df_tmp_p = df_pre_orderd_NonCancel[df_pre_orderd_NonCancel['商品名']==p]
        df_agri_orderd.loc['注文済',p] = df_tmp_p['個数'].sum()
    return df_agri_orderd

#%% 
def agri_results(df_products,df_cus_Ex,df_agri_orderd,df_agri_results,db):
    for p in df_products.index:
        if len(df_cus_Ex)>0:
            Ex_sum = df_cus_Ex[p].sum()
        else:
            Ex_sum = 0
        df_agri_results.loc[db,p] = Ex_sum + df_agri_orderd.loc['注文済',p]
    return df_agri_results
#%%

def main(predict_daytime_input,db_list_Input,lunch_diner,now_daytime,inspect):
    
    term = 5 # 平日の過去のデータの日数
    term_holi = 2 # 祝日の過去のデータの日数
    term_menu = 120
    term_holi_closed_menu_days = 180 #　祝日と休業日,メニューを取得する日数

    # 商品情報
    df_products = df_products_lunch_diner(lunch_diner)

        
    predict_day = datetime.date(predict_daytime_input.year
                            ,predict_daytime_input.month
                            ,predict_daytime_input.day)
    print(predict_day)
    
    df_null = pd.DataFrame()
    # 予測する店舗の更新
    db_list = update_db_list(db_list_Input,predict_day,lunch_diner)
    if len(db_list) == 0: return [df_null,df_null]

    # 祝日、休業日、メニューの読み込み
    [holidays,closed_days,holi_closed_menu_from_day,df_date_menu] = \
        Input_holday_closed_menu(term_holi,predict_day,lunch_diner,df_products,
                                predict_daytime_input,term_holi_closed_menu_days)
    if len(holidays) == 0: return [df_null,df_null]
    df_products = df_products.fillna(-1)
    
    #　各店舗で計算
    df_agri_results = pd.DataFrame()
    df_agri_correct = pd.DataFrame()
    df_agri_cus_Ex = pd.DataFrame()
    df_agri_time_over = pd.DataFrame()
    df_agri_cus_prob = pd.DataFrame()
    df_agri_cus_youkaku = pd.DataFrame()
    
    for db in db_list:
        
        # 締切時間を考慮したpredect_day
        [predict_daytime,dead_time] = plus_dead_time(lunch_diner,db,predict_daytime_input)
        
        # 計算した期待値を更新するか
        sn = update_Ex(predict_daytime,now_daytime)
        
        if predict_daytime < now_daytime:
            print('############予想日が過去の日付になっています############')

        #%%   No doc
        f_name_order = '弁当数予想/注文平均時刻の顧客リスト/平均時刻顧客リスト' + db + lunch_diner + '_' + \
                    str(predict_day) + '_' + str(sn) +'.pkl'
        f_name_Ex = '弁当数予想/注文予想の顧客リスト/予想顧客リスト' + db + lunch_diner + '_' + \
                    str(predict_day) + '_' + str(sn) +'.csv'
        f_name_prob = '弁当数予想/注文予想の顧客リスト/予想顧客リスト' + db + lunch_diner + '_' + \
                    str(predict_day) + '_' + str(sn) +'_prob.csv'
        # 期待値のファイルがあるか
        if (os.path.isfile(f_name_order)) & (os.path.isfile(f_name_Ex)):
            
            # 計算しておいた期待値を読み込み、新しい注文を加えて予想数を更新する
            [df_cus_Ex,df_cus_prob,df_cus_Ex_time_over,df_pre_orderd,df_time_over] = \
                    read_Ex_and_update_predict(f_name_order,f_name_Ex,f_name_prob,
                                               db,lunch_diner,sn,
                                               predict_daytime,predict_day,now_daytime,
                                               df_products)
            
        else:
            # 新しく期待値を計算する
            [df_cus_Ex,df_cus_Ex_time_over,df_pre_orderd,
             df_time_over,df_cus_prob] = \
                    make_Ex(db,lunch_diner,
                            predict_day,predict_daytime,now_daytime,
                            term,term_holi,holidays,closed_days,holi_closed_menu_from_day,
                            df_products,dead_time,sn,term_menu,df_date_menu)            
        
        # 注文確率と要確認
        df_cus_prob = df_cus_prob[~df_cus_prob.index.isin(df_pre_orderd['顧客ID'].unique())]
        str_preday = predict_day.strftime('%Y%m%d')
        str_preday = str_preday[2:]
        df_youkaku = SQL2DF.read_youkakunin_chose_day(db, str_preday, str_preday, lunch_diner)
        #要確認に含まれていない確率の顧客
        df_cus_prob2 = df_cus_prob[~df_cus_prob.index.isin(df_youkaku['顧客ID'].unique())]
        df_cus_prob2['店名'] = db
        #確率に含まれていない要確認の顧客
        df_youkaku2 = df_youkaku[~df_youkaku['顧客ID'].isin(df_cus_prob.index.unique())]
        df_youkaku2['店名'] = db
        
        # print('=====================')
        # print(df_cus_prob2)
        # print(df_youkaku2)     
        # print('=====================')
    
        # df_time_over更新と保存
        df_time_over = update_save_df_time_over(db,lunch_diner,df_time_over,
                                                df_cus_Ex_time_over,predict_day,sn)
        
        # NG料理の期待値は変更
        if (df_products.loc[:,'メニュー_ID'] < 0).sum() == 0: # メニューがすべて登録されている
            delete_NG_Ex(df_cus_Ex,df_products,db)
        
        # 注文日の注文済みのデータの統計          
        df_agri_orderd = agri_orderd(df_pre_orderd,df_products)
        
        #%% 結果
        df_agri_results = agri_results(df_products,df_cus_Ex,df_agri_orderd,df_agri_results,db)
        #    print(df_agri_results)
        
        df_agri_cus_Ex = pd.concat([df_agri_cus_Ex, df_cus_Ex])
        df_agri_time_over = pd.concat([df_agri_time_over, df_time_over])
        
        df_agri_cus_prob = pd.concat([df_agri_cus_prob, df_cus_prob2])
        df_agri_cus_youkaku = pd.concat([df_agri_cus_youkaku, df_youkaku2])
        #%% 注文日の結果を読み込む
        if inspect:
            df_correct = SQL2DF.read_products_data_chose_day_time(
                                        {},db,predict_daytime,
                                        predict_daytime,predict_daytime,lunch_diner)            
        #    df_correct.to_csv('df_correct.csv',encoding='utf_8_sig')
            
            df_correct = df_correct[df_correct['キャンセル']==0]
            for p in df_products.index:
                df_tmp_p = df_correct[df_correct['商品名']==p]
                df_agri_correct.loc[db,p] = df_tmp_p['個数'].sum()
            # print(df_agri_correct)
            #%% 注文断りを読み込み
            #df_refuse = SQL2DF.get_order_refuse('DEVELOP',db,predict_day)
            
            # if len(df_refuse) > 0:
            #     df_refuse_Ex = df_cus_Ex[df_cus_Ex.index.isin(df_refuse['顧客ID'])]
            #     refuse_NonEx_num = len(df_refuse[~df_refuse['顧客ID'].isin(df_refuse_Ex.index)])
            #     df_refuse_Num = pd.DataFrame()
            #     for p in df_products.index:
            #         df_refuse_Num.loc['num',p] = df_refuse_Ex.sum()[p] + \
            #                                                 df_products.loc[p,'注文割合']*refuse_NonEx_num
            #     print(df_refuse_Num)
                
            #%%
                # for p in df_products.index:
                #     df_agri_correct.loc[db,p] = df_agri_correct.loc[db,p] + \
                #                                         df_refuse_Num.loc['num',p]
                # print(df_agri_correct)
        
    #%%
    
    print('---------df_agri_results---------------------------------')
    print(df_agri_results) 
    print('---------df_agri_correct---------------------------------')
    print(df_agri_correct)
    print('---------------------------------------------------------')   
        
    #%% DBへの書き込み
    #write_DB_results(df_agri_results,lunch_diner,predict_day)
    
    #%%
    return [df_agri_results,df_agri_correct,df_agri_cus_prob,df_agri_cus_youkaku]

