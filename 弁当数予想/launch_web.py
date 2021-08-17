# -*- coding: utf-8 -*-
"""
Created on Sat Mar  6 20:21:17 2021

@author: user
"""

import 弁当数予想.main_web as main_web
import datetime
#import SQL2DF
import pandas as pd
import numpy as np


def predict_num(predict_daytime_input,lunch_diner):
    
    db_list_Input = ["鈴鹿店","四日市店"] # 鈴鹿店 四日市店
    #lunch_diner = '01' # 昼：01  夕:02
    
    now_daytime = datetime.datetime.now()+datetime.timedelta(hours=9)
    #predict_daytime_input = datetime.datetime(2021,5,6,0,0)
    
    inspect = 1 # 予想日の正解データを読み込むか
    
    [df_agri_results,df_agri_orderd,df_cus_Ex,df_time_over] = \
        main_web.main(predict_daytime_input,db_list_Input,
                          lunch_diner,now_daytime,inspect)
    
    db_list = df_agri_results.index
    
    df_agri_results.loc['予想',:]= df_agri_results.sum()
    df_agri_orderd.loc['注文',:] = df_agri_orderd.sum()
    
    for db in db_list:
        df_agri_results = df_agri_results.drop(db)
        df_agri_orderd = df_agri_orderd.drop(db)
    
    df_pre = pd.concat([df_agri_results, df_agri_orderd])
    df_pre = df_pre.T
    df_pre['余り'] = df_pre['予想'] - df_pre['注文']
    df_pre = df_pre.replace([np.inf, -np.inf], np.nan)
    df_pre = df_pre.fillna(0)
    df_pre = df_pre.astype(int)
    
    return [df_pre,df_cus_Ex,df_time_over]

# predict_daytime_input = datetime.datetime(2021,6,4,0,0,0)
# [df_pre,df_cus_Ex,df_time_over] = predict_num(predict_daytime_input,'01','DEVELOP')