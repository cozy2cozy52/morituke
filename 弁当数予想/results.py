# -*- coding: utf-8 -*-

import 弁当数予想.SQL2DF as SQL2DF
import datetime
import pandas as pd
import global_values as gv
import 弁当数予想.shidashi as shidashi

import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import japanize_matplotlib

        
class results_class:
    def __init__(self,day1,db):
        self.day1 = day1
        self.db = db
    
    def read_data(self):
        
        f_name_Ex = '弁当数予想/注文予想の顧客リスト/予想顧客リスト' + \
                        self.db + '01_' + str(self.day1) + '_1.csv'
                    #弁当数予想/
        f_name_order = '弁当数予想/注文平均時刻の顧客リスト/平均時刻顧客リスト' + \
                        self.db + '01_' + str(self.day1) + '_1.pkl'
        
        self.df_cus_Ex = pd.read_csv(f_name_Ex,encoding='utf_8_sig', index_col=0)
        df_predict_time = pd.read_pickle(f_name_order)
        self.df_predict_time = df_predict_time.set_index('顧客ID')
        
        daytime1 = datetime.datetime(self.day1.year,
                                     self.day1.month,
                                     self.day1.day,
                                     7,0,0)
        daytime2 = datetime.datetime(self.day1.year,
                                     self.day1.month,
                                     self.day1.day,
                                     10,0,0)
        self.df_orderd = SQL2DF.read_products_data_chose_register_day(
                                {},self.db,daytime1,daytime2,
                                daytime1,daytime1,'01')
        
        for c_id in self.df_orderd[self.df_orderd['キャンセル']==1]['顧客ID']:
            if c_id in self.df_cus_Ex.index:
                self.df_cus_Ex.drop(c_id,axis=0)
        # print(daytime1)
        # print(datetime.datetime.now())
        # print(self.df_orderd)
        self.df_orderd.drop(columns=['日付','登録時刻','キャンセル','顧客ID'],inplace=True)
    
    def squeeze(self):
        self.df_predict_time = \
            self.df_predict_time['3/4時刻']<datetime.timedelta(hours=-5)
        self.df_cus_Ex = self.df_cus_Ex[self.df_cus_Ex.index.isin(self.df_predict_time.index)]
        
        
    def select_menu(self,menu_name):
        self.df_predict_num = self.df_cus_Ex[[menu_name,'顧客名']]
        self.df_predict_num = self.df_predict_num.rename(columns={menu_name:'予想数'})
        
        self.df_orderd_res = self.df_orderd[self.df_orderd['商品名'] == menu_name]
        #self.df_orderd_res = self.df_orderd_res.set_index('顧客ID')
        self.df_orderd_res.drop(columns='商品名',inplace=True)
        self.df_orderd_res = self.df_orderd_res.rename(columns={'個数':'注文数'})
    
    def merge_df(self):
        df = pd.merge(self.df_predict_num, self.df_orderd_res,on='顧客名',how='outer')
        df.fillna(0,inplace=True)
        df = df[~((df['予想数']==0) & (df['注文数']==0))]
        df['差'] = df['予想数'] - df['注文数']
        df = df.reindex(columns=['顧客名', '予想数', '注文数','差'])
        df = df.sort_values(['差','予想数'],ascending=False)
        return(df)
  
def make_predict_results(day1,db,menu_name):
    obj = results_class(day1,db)
    obj.read_data()
    obj.squeeze()
    obj.select_menu(menu_name)
    df_m = obj.merge_df()
    df_m = df_m.set_index('顧客名')
    return(df_m)
    
# day1 = datetime.date(2021,9,12)
# menu_name = 'お魚弁当_並'
# df_predict_results = make_predict_results(day1,menu_name)
# print(df_predict_results)

cus_name_list = ['店頭用','夕方店舗用']
shidashi2teiban = \
    ['昼食弁当_並','昼食弁当_大','お魚弁当_並','お魚弁当_大',
     '昼食弁当_並ＣＯ','昼食弁当_大ＣＯ','お魚弁当_並CO','お魚弁当_大ＣＯ']
week_youbi = ['月','火','水','木','金','土','日']

def get_shidashi_order_num(day1):
    obj_shidashi = shidashi.shidashi_class(day1)
    df_list = []
    for cn in cus_name_list:
        df_list.append(obj_shidashi.slice_store_city(cn))
    
    [df_shidashi,df_shidashi_cancel] = \
                obj_shidashi.make_df_shidashi(cus_name_list)
    for i in df_shidashi.index:
        name = df_shidashi.loc[i,'品名']
        if ('CO' in name) or ('ＣＯ' in name):
            df_shidashi.loc[i,'品名'] = df_shidashi.loc[i,'品名'][:-2]
    return df_shidashi


def make_sum_results(day_o,term,c_week):
    
    list_days = []
    df_res = pd.DataFrame()
    for d in range(term):
        day1 = day_o - datetime.timedelta(days=d*c_week)
        df_seizou = SQL2DF.get_seizou_num(day1,'製造数')
        df_seizou = df_seizou.set_index('商品名')
        
        str_day = SQL2DF.datetime2otodokeday(day1)
        df_order_suzuka = SQL2DF.read_delivery_data_chose_day({},'鈴鹿店',str_day,str_day,'01')
        df_order_yokkaichi = SQL2DF.read_delivery_data_chose_day({},'四日市店',str_day,str_day,'01')
        
        df_order_sum = pd.DataFrame()
        for p in df_seizou.index:
            df_order_sum.loc[p,'注文数'] = df_order_suzuka[df_order_suzuka['商品名']==p]['個数'].sum() + \
                                        df_order_yokkaichi[df_order_yokkaichi['商品名']==p]['個数'].sum()
        
        # #仕出し
        df_shidashi = get_shidashi_order_num(day1)
        
        # 仕出しに以下の弁当が入っていたらdf_predictに追加する
        append_list = shidashi2teiban
        df_append = df_shidashi[df_shidashi['品名'].isin(append_list)]
        
        if len(df_append)>0:
            for j in df_append.index:
                name = df_append.loc[j,'品名']
                df_order_sum.loc[name,'注文数'] += df_append.loc[j,'数量']
    
        disp_day = day1.strftime('%m/%d')
        disp_day += week_youbi[day1.weekday()]
        list_days.append(disp_day)
        for p in df_seizou.index:
            seizou_num = df_seizou.loc[p,'製造数']
            order_num = df_order_sum.loc[p,'注文数']
            df_res.loc[p,disp_day] = seizou_num-order_num
            
    
    df_res['合計'] = df_res[list_days].sum(axis=1)
    df_res['平均'] = df_res[list_days].mean(axis=1)
    df_res['絶対値合計'] = df_res[list_days].abs().sum(axis=1)
    df_res['絶対値平均'] = df_res[list_days].abs().mean(axis=1)
    df_res = df_res.reindex(index=gv.predict_products)
    df_res = df_res.fillna(0)
    df_res.loc['合計',:] = df_res.sum(axis=0)
    df_res.loc['絶対値合計',:] = df_res.loc[gv.predict_products,:].abs().sum(axis=0)
    
    pd.options.display.precision = 1
    return(df_res)


#################################

def get_shidashi_order_num_term(day1,day2):
    obj_shidashi = shidashi.shidashi_period_class(day1, day2)
    df_list = []
    for cn in cus_name_list:
        df_list.append(obj_shidashi.slice_store_city(cn))
    
    [df_shidashi,df_shidashi_cancel] = \
                obj_shidashi.make_df_shidashi(cus_name_list)
    for i in df_shidashi.index:
        name = df_shidashi.loc[i,'品名']
        if ('CO' in name) or ('ＣＯ' in name):
            df_shidashi.loc[i,'品名'] = df_shidashi.loc[i,'品名'][:-2]
    return df_shidashi

class results_graph_class:
    def __init__(self,day1,day2,products_list,col_list):
        self.day1 = day1
        self.day2 = day2
        self.p_list = products_list
        self.c_list = col_list
        plt.cla()
    
    def read_seizou_data(self):
        df_seizou = SQL2DF.get_seizou_num_term(self.day1,self.day2,'製造数')
        df_seizou_sum = pd.DataFrame()
        for p in df_seizou['商品名'].unique():
            for d in df_seizou['日付'].unique():
                n = df_seizou[(df_seizou['商品名']==p) & 
                              (df_seizou['日付']==d)]['製造数'].sum()
                df_seizou_sum.loc[d,p] = n
        df_seizou_sum.index = df_seizou_sum.index.astype('str')
        return df_seizou_sum    
        
    def read_order_data(self):
        str_day1 = SQL2DF.datetime2otodokeday(self.day1)
        str_day2 = SQL2DF.datetime2otodokeday(self.day2)
        df_order_suzuka = SQL2DF.read_delivery_data_chose_day(
                                {},'鈴鹿店',str_day1,str_day2,'01')
        df_order_yokkaichi = SQL2DF.read_delivery_data_chose_day(
                                {},'四日市店',str_day1,str_day2,'01')
        
        df_order_sum = pd.DataFrame()
        for p in df_order_suzuka['商品名'].unique():
            for d in df_order_suzuka['日付'].unique():
                sn = df_order_suzuka[(df_order_suzuka['商品名']==p) & \
                                (df_order_suzuka['日付']==d)]['個数'].sum()
                yn = df_order_yokkaichi[(df_order_yokkaichi['商品名']==p) & \
                                (df_order_yokkaichi['日付']==d)]['個数'].sum()
                d2 = datetime.date(
                            int('20'+d[0:2]),int(d[2:4]),int(d[4:6]))
                d2 = d2.strftime('%Y-%m-%d')
                df_order_sum.loc[d2,p] = sn + yn
        
        # #仕出し
        df_shidashi = get_shidashi_order_num_term(self.day1,self.day2)
        # 仕出しに以下の弁当が入っていたら追加する
        for p in df_order_sum.columns:
            for d in df_order_sum.index:
                n = df_shidashi[(df_shidashi['品名']==p) & 
                                   (df_shidashi['注文日']==d)]['数量'].sum()
                df_order_sum.loc[d,p] += n
            
        return df_order_sum
    
    def create_graph(self,x_list,t_list,name):
        plt.plot(t_list, x_list, label=name)
        plt.xlabel('t')
        plt.ylabel('x')
        plt.legend(loc=0) 
    
    def get_graph(self):
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        image_png = buffer.getvalue()
        graph = base64.b64encode(image_png)
        graph = graph.decode('utf-8')
        buffer.close()
        return graph
        
        
# day1 = datetime.date(2021,9,22)
# day2 = datetime.date(2021,9,23)
# obj = results_graph_class(day1,day2,[],['注文数'])

# df_seizou_sum = obj.read_seizou_data()
# df_order_sum = obj.read_order_data()
# # print(df_seizou_sum)
# # print(df_order_sum)

# x_list = df_order_sum['昼食弁当_並'].to_list()
# t_list = df_order_sum.index.to_list()
# graph = obj.create_graph(x_list,t_list)
