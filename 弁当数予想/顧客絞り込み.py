# -*- coding: utf-8 -*-
"""
Created on Thu May 20 14:54:44 2021

@author: user
"""

import SQL2DF



instance = 'OFUKURO-SERVER' #OFUKURO-SERVER
db= '四日市店'
df_cus_visible = SQL2DF.get_kokyaku_visible(instance,db)
df_rireki = SQL2DF.get_kokyaku_hanbai_rireki(instance,db)

df_no_order = df_cus_visible[~df_cus_visible['顧客ID'].isin(df_rireki['顧客ID'].unique())]

#df_no_order.to_csv('df_no_order.csv',encoding='utf_8_sig')

#%%
# import Write_DB

# list1 = df_no_order['顧客ID'].to_list()

# Write_DB.customer_invisible_update(instance,db,list1)

# #%%
# df_cus_visible2 = SQL2DF.get_kokyaku_visible(instance,db)