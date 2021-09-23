# -*- coding: utf-8 -*-

import 弁当数予想.SQL2DF as SQL2DF
import datetime
import pandas as pd

class shidashi_class:
    def __init__(self,day1):
        self.df_read = SQL2DF.get_shidashi(day1)
    
    def get_df_read(self):
        return self.df_read
    
    def slice_store_city(self,cus_name):
        df_c = self.df_read[self.df_read['キャンセル']==0]
        df = df_c[df_c['顧客名']==cus_name]
        d_list = ['注文日','時間帯','顧客名','配達時間','配達方面',
                  'キャンセル','単価',
                  '店頭引取時間','備考']
        df = df.drop(d_list, axis=1)
        df = df.sort_values('品名')
        df.rename(columns={'品名': cus_name}, inplace=True)
        df = df.fillna('')
        return df
    
    def make_df_shidashi(self,cus_name_list):
        df = self.df_read[~self.df_read['顧客名'].isin(cus_name_list)]
        df = df[~(df['顧客名']=='お届け')]
        df = df.fillna('')
        df = df[df['単価']>10]
        df = df[~(df['品名']=='お茶ペットボトル100')]
        df = df.sort_values(['配達方面','単価'])
        
        df_store = df[df['配達方面']=='店舗']
        df_otodoke = df[df['配達方面']!='店舗']
        
        df_store['時間'] = df_store['店頭引取時間']
        df_otodoke['時間'] = df_otodoke['配達時間']
        df_s = pd.concat([df_otodoke,df_store])
        
        df_s = df_s.reindex(columns=['時間帯', '配達方面','品名','数量', '時間',
                                '単価','メモ','キャンセル'])
        df_s = df_s.sort_values('時間帯')
        
        df_s['時間帯'] = df_s['時間帯'].replace(1, '昼')
        df_s['時間帯'] = df_s['時間帯'].replace(2, '夕')
        
        df_cancel = df_s[df_s['キャンセル']==1]
        df_s = df_s[df_s['キャンセル']==0]
        d_list = ['キャンセル']
        df_s         = df_s.drop(d_list, axis=1)
        df_cancel  = df_cancel.drop(d_list, axis=1)
        
        df_s.rename(columns={'時間帯': '仕出'}, inplace=True)
        df_cancel.rename(columns={'時間帯': 'キャンセル'}, inplace=True)
        
        return [df_s,df_cancel]

# predict_day = datetime.date.today()
# obj_shidashi = shidashi_class(predict_day)

# cus_name_list = ['店頭用','夕方店舗用','鈴鹿市役所　売店']
# df_list = []
# for cn in cus_name_list:
#     df_list.append(obj_shidashi.slice_store_city(cn))



class shidashi_period_class:
    def __init__(self,from_day,end_day):
        self.df_read = SQL2DF.get_shidashi_period(from_day, end_day)
    
    def get_df_read(self):
        return self.df_read
    
    def slice_store_city(self,cus_name):
        df_c = self.df_read[self.df_read['キャンセル']==0]
        df = df_c[df_c['顧客名']==cus_name]
        d_list = ['注文日','時間帯','顧客名','配達時間','配達方面',
                  'キャンセル','単価',
                  '店頭引取時間','備考']
        df = df.drop(d_list, axis=1)
        df = df.sort_values('品名')
        df.rename(columns={'品名': cus_name}, inplace=True)
        df = df.fillna('')
        return df
    
    def make_df_shidashi(self,cus_name_list):
        df = self.df_read[~self.df_read['顧客名'].isin(cus_name_list)]
        df = df[~(df['顧客名']=='お届け')]
        df = df.fillna('')
        df = df[df['単価']>10]
        df = df[~(df['品名']=='お茶ペットボトル100')]
        df = df.sort_values(['配達方面','単価'])
        
        df_store = df[df['配達方面']=='店舗']
        df_otodoke = df[df['配達方面']!='店舗']
        
        df_store['時間'] = df_store['店頭引取時間']
        df_otodoke['時間'] = df_otodoke['配達時間']
        df_s = pd.concat([df_otodoke,df_store])
        
        df_s = df_s.reindex(columns=['注文日','時間帯', '配達方面','品名','数量', '時間',
                                '単価','メモ','キャンセル'])
        df_s = df_s.sort_values('時間帯')
        
        df_s['時間帯'] = df_s['時間帯'].replace(1, '昼')
        df_s['時間帯'] = df_s['時間帯'].replace(2, '夕')
        
        df_cancel = df_s[df_s['キャンセル']==1]
        df_s = df_s[df_s['キャンセル']==0]
        d_list = ['キャンセル']
        df_s         = df_s.drop(d_list, axis=1)
        df_cancel  = df_cancel.drop(d_list, axis=1)
        
        df_s.rename(columns={'時間帯': '仕出'}, inplace=True)
        df_cancel.rename(columns={'時間帯': 'キャンセル'}, inplace=True)
        
        return [df_s,df_cancel]

# predict_day = datetime.date.today()
# obj_shidashi = shidashi_class(predict_day)

# cus_name_list = ['店頭用','夕方店舗用','鈴鹿市役所　売店']
# df_list = []
# for cn in cus_name_list:
#     df_list.append(obj_shidashi.slice_store_city(cn))