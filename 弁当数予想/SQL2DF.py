# -*- coding: utf-8 -*-

import pyodbc
import pandas as pd
import datetime
import jpholiday

import urllib
from sqlalchemy import create_engine

server = '192.168.24.10' # 30:dev  10:ofukuro
class sql2df:
    
    def __init__(self,query,tupls,db,df_columns):
        self.query = query
        self.tupls = tupls
        self.db = db
        self.df_columns = df_columns

    def login(self):
        
        driver = 'ODBC Driver 17 for SQL Server'
        #server = '192.168.24.10' # 30:dev  10:ofukuro
        username = 'sa'
        password = 'ofu'
        
        odbc_connect = urllib.parse.quote_plus(
            'DRIVER={%s};SERVER=%s;UID=%s;PWD=%s;DATABASE=%s;' % (driver, server, username, password,self.db))
        engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % odbc_connect)

        return engine.connect()
    
    def fetch(self):
        cursor = self.login()
        return cursor.execute(self.query,self.tupls)

    def make_df(self):
        
        rows = self.fetch()
        
        cat_jisyo = {}
        for i in self.df_columns:
            cat_jisyo[i] = []
        df_DB = pd.DataFrame(cat_jisyo)
        
        n=0
        for r in rows:
            df_DB.loc[n] = r
            n=n+1
        
        return df_DB

#%%  クエリ文にIN句を追加する。
def query_for_IN(query,dict_col_list):
    
    query = query+ ' '
    tupls = ()
    for db_column in dict_col_list.keys():
        search_list = dict_col_list[db_column]
        
        if len(search_list) != 0:
            strq=''
            for i in range(len(search_list)):
                strq += '?'
            q_in = 'AND ' + db_column + ' IN ({})'.format(', '.join(strq))
            query = query+ q_in
            tupls = tupls + tuple(search_list)
            
    return [query,tupls]

def query_for_IN2(query,dict_col_list,tupls):
    
    query = query+ ' '
    for db_column in dict_col_list.keys():
        search_list = dict_col_list[db_column]
        
        if len(search_list) != 0:
            strq=''
            for i in range(len(search_list)):
                strq += '?'
            q_in = 'AND ' + db_column + ' IN ({})'.format(', '.join(strq))
            query = query+ q_in
            tupls = tupls + tuple(search_list)
            
    return [query,tupls]
            
#%% お届けの日付を文字列からdatetimeに変換
def otodoke_time(df,time_column,deadline_h,deadline_m):
    lis = []
        
    for r in df[time_column]:
        d = datetime.datetime(int('20'+r[0:2]),int(r[2:4]),int(r[4:6]), \
                              deadline_h,deadline_m,0)
        lis.append(d)
    
    df[time_column] = lis
    df[time_column] = df[time_column].astype('datetime64')
    
    return df

#%% お届けの日付を文字列からdatetimeに変換
import copy
def otodoke_date(df,time_column):
    df_re = copy.copy(df)
    for i in df.index:
        r = df.loc[i,time_column]
        df_re.loc[i,time_column] = datetime.datetime(
                                int('20'+r[0:2]),int(r[2:4]),int(r[4:6]),0,0,0)
    
    return df_re

#%% 指定した日付、期間からその曜日のお届けDBの形式の日付のリストを出力

def datetimeymd2str_appendlist(day,res):
    from datetime import datetime, timedelta
    str_day = datetime.strftime(day, '%Y%m%d') #datetimeから文字列に変換
    res.append(str_day[2:])
    return res

def predictday2otodokeday(predictday, term_week):
    from datetime import datetime, timedelta
    predictday = datetime.strptime(predictday, '%Y-%m-%d') #文字列からdatetimeに変換
    day_before = predictday
    res = []
    if predictday.weekday() >= 5: #土日の場合
        for i in range(term_week):
            day_before = day_before - timedelta(days=7) #一週間前
            res = datetimeymd2str_appendlist(day_before,res)
    else: #平日の場合
        if jpholiday.is_holiday(predictday): # 祝日の場合
            i=1
            while len(res) < term_week:
                holi = jpholiday.holidays(predictday - timedelta(days=365), predictday)[-i][0]
                i+=1
                if holi.weekday() < 5: #平日の場合
                    res = datetimeymd2str_appendlist(holi,res)
        else: #祝日でない場合
            while len(res) < term_week:
                day_before = day_before - timedelta(days=7) #一週間前
                if not jpholiday.is_holiday(day_before): # 祝日でない場合
                    res = datetimeymd2str_appendlist(day_before,res)
    return res

#%% query selectの文字列を作成
def query_select_str(query_select_list):
    query_select_list_str = 'select '
    for s in query_select_list:
        query_select_list_str = query_select_list_str + s + ' , '
    query_select_list_str = query_select_list_str[:-2]
    return query_select_list_str

#%% お届けに必要なデータをDBから読み込む
    
def read_delivery_data(dict_col_list,db,lunch_diner):
    query_select_list = ['日付', '顧客名', '商品名', '個数', '登録時刻', \
                         'コース','緯度経度','顧客ID']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from 販売データ \
               INNER JOIN 販売明細 ON 販売データ.伝票番号 = 販売明細.伝票番号 \
               WHERE キャンセル = 0' + \
               ' AND 時間帯 = ' + lunch_diner + \
               ' AND NOT 顧客名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? ' 
               
    [query,tupls] = query_for_IN(query,dict_col_list)
    tupls = tuple(['要確認']) + tupls
    tupls = tuple(['回送']) + tupls
    tupls = tuple(['★特%']) + tupls # 特弁は除く
    tupls = tuple(['注文外%']) + tupls
#    print(query)
#    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    
    return df

#%% 登録時刻を指定して取り出し
def read_delivery_data_chose_day_time(dict_col_list,db,register_time,
                                 str_start_day,str_last_day,lunch_diner):
        
    #    print(str_predict_day)
    query_select_list = ['日付', '顧客名', '商品名', '個数', '登録時刻', \
                         'コース','緯度経度','顧客ID']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from 販売データ \
               INNER JOIN 販売明細 ON 販売データ.伝票番号 = 販売明細.伝票番号 \
               WHERE キャンセル = 0' + \
               ' AND 時間帯 = ' + lunch_diner + \
               " AND 日付 >= '" + str_start_day + "'" + \
               " AND 日付 <= '" + str_last_day + "'" + \
               " AND 登録時刻 <= '" +register_time.strftime('%Y-%m-%d %H:%M:%S') + "'" + \
               ' AND NOT 顧客名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? ' 
               
    [query,tupls] = query_for_IN(query,dict_col_list)
    tupls = tuple(['要確認']) + tupls
    tupls = tuple(['回送']) + tupls
    tupls = tuple(['★特%']) + tupls # 特弁は除く
    tupls = tuple(['注文外%']) + tupls
    #    print(query)
    #    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    
    if len(df) > 0:
        df = otodoke_date(df,'日付')
    
    return df

#%%
def read_delivery_data_chose_day(dict_col_list,db,
                                 str_start_day,str_last_day,lunch_diner):
    query_select_list = ['日付', '顧客名', '商品名', '個数', '登録時刻', \
                         'コース','緯度経度','顧客ID']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from 販売データ \
               INNER JOIN 販売明細 ON 販売データ.伝票番号 = 販売明細.伝票番号 \
               WHERE キャンセル = 0' + \
               ' AND 時間帯 = ' + lunch_diner + \
               " AND 日付 >= '" + str_start_day + "'" + \
               " AND 日付 <= '" + str_last_day + "'" + \
               ' AND NOT 顧客名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? ' 
               
    [query,tupls] = query_for_IN(query,dict_col_list)
    tupls = tuple(['要確認']) + tupls
    tupls = tuple(['回送']) + tupls
    tupls = tuple(['★特%']) + tupls # 特弁は除く
    tupls = tuple(['注文外%']) + tupls
#    print(query)
#    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    
    return df

#%%
def read_youkakunin_chose_day(db,str_start_day,str_last_day,lunch_diner):
    query_select_list = ['顧客名', '顧客ID']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from 販売データ \
               INNER JOIN 販売明細 ON 販売データ.伝票番号 = 販売明細.伝票番号 \
               WHERE キャンセル = 0' + \
               ' AND 時間帯 = ' + lunch_diner + \
               " AND 日付 >= '" + str_start_day + "'" + \
               " AND 日付 <= '" + str_last_day + "'" + \
               ' AND 商品名 LIKE ? ' 
               
    #[query,tupls] = query_for_IN(query,[])
    tupls = tuple(['要確認']) #+ tupls
#    print(query)
#    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    
    return df
#df = read_youkakunin_chose_day('鈴鹿店','210827','210827','01')
#%% datetimeからお届けの文字の日付に変換

def datetime2otodokeday(day1):
    syear = str(day1.year)[2:]

    if day1.month < 10:
        smonth = '0' + str(day1.month)
    else:
        smonth = str(day1.month)
    
    if day1.day < 10:
        sday = '0' + str(day1.day)
    else:
        sday = str(day1.day)
    
    str_predict_day = syear + smonth + sday
    
    return str_predict_day

#%%
def login(db):
    # user = "sa"
    # pasword = "ofu"
    # connection = "DRIVER={SQL Server};SERVER=" +  ";uid=" + \
    #                 user + ";pwd=" + pasword + ";DATABASE=" + db
    # return pyodbc.connect(connection)

    driver = 'ODBC Driver 17 for SQL Server'
    #server = '192.168.24.10'
    username = 'sa'
    password = 'ofu'
    
    odbc_connect = urllib.parse.quote_plus(
        'DRIVER={%s};SERVER=%s;UID=%s;PWD=%s;DATABASE=%s;' % (driver, server, username, password,db))
    engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % odbc_connect)

    return engine.connect()

#%% 祝日の取得
def get_holiday(from_day,end_day):
    str_from_day = from_day.strftime('%Y-%m-%d')
    str_end_day  = end_day.strftime('%Y-%m-%d')
    
    con = login('配達共通')
    rows = con.execute('select 祝日 \
                   from 祝日 \
                   WHERE 祝日 >= ? AND 祝日 <= ?',(str_from_day,str_end_day) \
                   )
    
    holidays = []
    for r in rows:
        holidays.append(datetime.date(int(r[0].year),int(r[0].month),int(r[0].day)))
        
    return holidays

#%% 休業日の取得
def get_closed_days(from_day,end_day,lunch_diner):
    str_from_day = from_day.strftime('%Y-%m-%d')
    str_end_day  = end_day.strftime('%Y-%m-%d')
    
    con = login('配達共通')
    rows = con.execute('select 休業日 \
                   from 休業日 \
                   WHERE 休業日 >= ? AND 休業日 <= ? AND 時間帯 = ?',
                   (str_from_day,str_end_day,lunch_diner) \
                   )
    
    closed_days = []
    for r in rows:
        closed_days.append(datetime.date(int(r[0].year),int(r[0].month),int(r[0].day)))
        
    return closed_days

#%% 予想データ外日付の取得
def get_except_days(from_day,end_day):
    str_from_day = from_day.strftime('%Y-%m-%d')
    str_end_day  = end_day.strftime('%Y-%m-%d')
    
    con = login('配達共通')
    rows = con.execute('select 除外日 \
                   from 予想データ外 \
                   WHERE 除外日 >= ? AND 除外日 <= ?',
                   (str_from_day,str_end_day) \
                   )
    
    except_days = []
    for r in rows:
        except_days.append(datetime.date(int(r[0].year),int(r[0].month),int(r[0].day)))
        
    return except_days

#%% 顧客定休週日の取得
def get_custom_regular_holidays(db,dict_col_list):
    
    query_select_list = ['顧客ID', '曜日', '週番']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from 顧客定休週日 WHERE 取扱店舗 LIKE ?'
               
    [query,tupls] = query_for_IN(query,dict_col_list)
    tupls = tuple([db]) + tupls

#    print(query)
#    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,'配達共通',df_columns)
    df = obj.make_df()
    
    for i in df.index:
        w = df.loc[i,'曜日']
        df.loc[i,'曜日'] = youbi_DB2python(w)
    
    return df

#%% 顧客NGメニューの取得
def get_NG_menu(db,dict_col_list):
    
    query_select_list = ['顧客ID', '料理ID']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from 顧客NG料理 WHERE 取扱店舗 LIKE ?'
               
    [query,tupls] = query_for_IN(query,dict_col_list)
    tupls = tuple([db]) + tupls

#    print(query)
#    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,'配達共通',df_columns)
    df = obj.make_df()
    
    return df

#%% 顧客N祝日不要の取得
def get_Non_holiday_order(db,dict_col_list):
    
    query_select_list = ['顧客ID']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from 顧客台帳 WHERE 非表示 = 0' + \
               ' AND  祝日不要 = 1'
               
    [query,tupls] = query_for_IN(query,dict_col_list)

#    print(query)
#    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    
    return df

#%% 注文断りの取得
def get_order_refuse(db,predict_day):
    
    str_predict_day = predict_day.strftime('%Y-%m-%d')
    
    query_select_list = ['顧客ID']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from 注文断り WHERE 取扱店舗 LIKE ? AND 日付 = ?'
               
    tupls = ()
    tupls = tupls + tuple([db]) 
    tupls = tupls + tuple([str_predict_day])

#    print(query)
#    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,'配達共通',df_columns)
    df = obj.make_df()
    
    return df
#%% 予想日の継続購入の内容をまとめる

def ReadProductList(lunch_diner):
    db = '配達共通'
    query_select_list = ['ID', '登録名', '受注表示名', '単価']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from 品目台帳' + \
               ' WHERE 休止 = 0' + \
               ' AND  昼 = ? '  + \
               ' AND  夕 = ? '  + \
               ' AND  品目外項目 = 0 '
    
    if lunch_diner == '01':
        tupls = tuple([1,0])
    else:
        tupls = tuple([0,1])
    
    #print(query)
    #print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()

    return df

#%%
def subscription(db,lunch_diner,predict_day):

    if predict_day.month > 4 and predict_day.month < 11:
        summer_winter = '01' # summer
    else:
        summer_winter = '02' # summer
    
    # product list
    df_PL = ReadProductList(lunch_diner)
    
    df_PL['商品ID'] = df_PL['ID']
    df_PL['商品ID'] = df_PL['商品ID'].astype('int')
    df_PL = df_PL.drop(columns = 'ID')
    
    dict_col_list = { '商品ID':df_PL['商品ID'].to_list()}
    query_select_list = ['顧客ID', '商品ID', '個数']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from M継続購入顧客台帳 ' + \
               'INNER JOIN M継続購入明細台帳 ' + \
               'ON M継続購入顧客台帳.継続ID = M継続購入明細台帳.継続ID ' + \
               'WHERE 中止 = 0' + \
               ' AND 時間帯 LIKE ? ' + \
               ' AND 夏冬 = ? '
               
    [query,tupls] = query_for_IN(query,dict_col_list)
    tupls = tuple([summer_winter]) + tupls
    tupls = tuple([lunch_diner]) + tupls
    
#    print(query)
#    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df_subscription = obj.make_df()
    
    df_subscription['商品ID'] = df_subscription['商品ID'].astype('int')
    
    for i in range(len(df_subscription)):
        tmp = df_PL[df_PL['商品ID'] == df_subscription['商品ID'][i]]['受注表示名']
        pname = tmp[tmp.index[0]]
        df_subscription.loc[i,'商品名'] = pname
    
    return df_subscription
    
#%% ある商品の指定日の注文内容を抽出

def Order_detail(predict_day,pre_products,db,lunch_diner):
    str_predict_day = datetime2otodokeday(predict_day)
                      
    dict_col_list = { '日付': [str_predict_day],
                      '商品名':pre_products}
#    print(str_predict_day)
    df_orderd = read_delivery_data(dict_col_list,db,lunch_diner)
    
    return df_orderd

#%% ある商品の指定日の注文内容を抽出 顧客も指定

def Order_detail_Custom(predict_day,pre_products,db,lunch_diner,customID):
    str_predict_day = datetime2otodokeday(predict_day)
                      
    dict_col_list = { '日付': [str_predict_day],
                      '商品名':pre_products,
                      '顧客ID':customID,
                      }
#    print(str_predict_day)
    df_orderd = read_delivery_data(dict_col_list,db,lunch_diner)
    
    return df_orderd

#%% datetime.date から　文字列に変換
def datetimedate2strMD(date1):
    if date1.month < 10:
        strM = '0' + str(date1.month)
    else:
        strM = str(date1.month)
    
    if date1.day < 10:
        strD = '0' + str(date1.day)
    else:
        strD = str(date1.day)
    
    return [strM,strD]

#%% 注文回数をしていして取り出し
def pick_up_cus_by_order(db,lunch_diner,from_day,end_day,o_num,pre_products):
    str_start_day = datetime2otodokeday(from_day)
    str_last_day = datetime2otodokeday(end_day)
    
    dict_col_list = { '商品名':pre_products}
    
    query_select_list = ['顧客ID']
    query_select_list_str = query_select_str(query_select_list)
        
    # query文作成
    query = query_select_list_str + \
               'from 販売データ' + \
               ' INNER JOIN 販売明細 ON 販売データ.伝票番号 = 販売明細.伝票番号' + \
               ' WHERE キャンセル = 0' + \
               ' AND 時間帯 = ' + lunch_diner + \
               " AND 日付 >= '" + str_start_day + "'" + \
               " AND 日付 <= '" + str_last_day + "'" + \
               ' AND NOT 顧客名 LIKE ? '

    tupls = ()
    tupls = tupls + tuple(['注文外%'])

    [query,tupls] = query_for_IN2(query,dict_col_list,tupls)
    
    query = query + ' GROUP BY 顧客ID  HAVING COUNT(顧客ID) > ?'
    tupls = tupls + tuple([o_num])
    
#    print(query)
#    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    
    return df

#%% 登録時刻を指定して販売データを取り出し
def read_products_data_chose_day_time(dict_col_list,db,register_time,
                                 start_daytime,last_daytime,lunch_diner):
    
    str_start_day = datetime2otodokeday(start_daytime)    
    str_last_day = datetime2otodokeday(last_daytime)    

    query_select_list = ['日付', '顧客名', '商品名', '個数', '登録時刻','顧客ID','キャンセル']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from 販売データ \
               INNER JOIN 販売明細 ON 販売データ.伝票番号 = 販売明細.伝票番号 \
               WHERE ' + \
               ' 時間帯 = ' + lunch_diner + \
               " AND 日付 >= '" + str_start_day + "'" + \
               " AND 日付 <= '" + str_last_day + "'" + \
               " AND 登録時刻 <= '" +register_time.strftime('%Y-%m-%d %H:%M:%S') + "'" + \
               ' AND NOT 顧客名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? '
               
    [query,tupls] = query_for_IN(query,dict_col_list)
    tupls = tuple(['回送']) + tupls
    tupls = tuple(['★特%']) + tupls # 特弁は除く
    tupls = tuple(['注文外%']) + tupls
    #    print(query)
    #    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    
    if len(df) > 0:
        df = otodoke_date(df,'日付')
        
    df = df[~((df['商品名']=='要確認') & (df['キャンセル']==0))]
    
    return df

# now_daytime = datetime.datetime(2021,6,2,20,0,0)
# predict_daytime = datetime.datetime(2021,6,3,0,0,0)
# df_pre_orderd = read_products_data_chose_day_time(
#                                 {},'四日市店',now_daytime,
#                                 predict_daytime,predict_daytime,'01')

#%% 登録時刻を指定して販売データを取り出し
def read_products_data_chose_register_day(dict_col_list,db,
                                          register_stime,register_ltime,
                                 start_daytime,last_daytime,lunch_diner):
    
    str_start_day = datetime2otodokeday(start_daytime)    
    str_last_day = datetime2otodokeday(last_daytime)    

    query_select_list = ['日付', '顧客名', '商品名', '個数', '登録時刻','顧客ID','キャンセル']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from 販売データ \
               INNER JOIN 販売明細 ON 販売データ.伝票番号 = 販売明細.伝票番号 \
               WHERE ' + \
               ' 時間帯 = ' + lunch_diner + \
               " AND 日付 >= '" + str_start_day + "'" + \
               " AND 日付 <= '" + str_last_day + "'" + \
               " AND 登録時刻 >= '" +register_stime.strftime('%Y-%m-%d %H:%M:%S') + "'" + \
               " AND 登録時刻 <= '" +register_ltime.strftime('%Y-%m-%d %H:%M:%S') + "'" + \
               ' AND NOT 顧客名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? ' + \
               ' AND NOT 商品名 LIKE ? '
               
    [query,tupls] = query_for_IN(query,dict_col_list)
    tupls = tuple(['回送']) + tupls
    tupls = tuple(['★特%']) + tupls # 特弁は除く
    tupls = tuple(['注文外%']) + tupls
    #    print(query)
    #    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    
    if len(df) > 0:
        df = otodoke_date(df,'日付')
        
    df = df[~((df['商品名']=='要確認') & (df['キャンセル']==0))]
    
    return df

#%% menuデータを取得
def get_menu(lunch_diner,from_day,end_day,db,main_menu):  
    
    if lunch_diner == '01':
        str_lunch_diner = '昼'
    else:
        str_lunch_diner = '夕'
        
    str_from_day = from_day.strftime('%Y-%m-%d')
    str_end_day  = end_day.strftime('%Y-%m-%d')
    
    query_select_list = ['年月日','料理名','D_料理.料理ID','小区分']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    str_syoukubun = " AND (小区分 = "
    for m in main_menu:
        str_syoukubun += "'" + m + "'"
        if m == main_menu[-1]:
            str_syoukubun += ")"
        else:
            str_syoukubun += " OR 小区分 = "
    
    query = query_select_list_str + \
               'from D_料理' + \
               " INNER JOIN M_料理 ON D_料理.料理ID = M_料理.料理ID" + \
               " WHERE 区分 = '" + str_lunch_diner + "'" + \
               str_syoukubun + \
               " AND 順 = '1主' " + \
               " AND 年月日 >= '" + str_from_day + "'"\
               " AND 年月日 <= '" + str_end_day + "';"
    
    tupls = ()
    
    #print(query)
    #print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df_menu = obj.make_df()
    #print(df_menu)
    
    # 曜日の列を追加
    df_menu = df_menu.set_index('年月日')
    df_menu['曜日'] = df_menu.index.weekday
    
    df_menu = df_menu.rename(columns={'D_料理.料理ID': '料理ID'})

    # データフレームを整える
    df_date_menu = pd.DataFrame()
    for d in df_menu.index.unique():
        for m in main_menu:
            df_tmp = df_menu[(df_menu.index==d)&(df_menu['小区分']==m)]
            if len(df_tmp)>0:
                df_date_menu.loc[d,'ID_' + m] = df_tmp['料理ID'][0]
                df_date_menu.loc[d,'name_' + m] = df_tmp['料理名'][0]
                df_date_menu.loc[d,'曜日'] = df_tmp['曜日'][0]
            else:
                df_date_menu.loc[d,'ID_' + m] = -1
#                str_tmp = str(d) + m + 'のメニューが登録されていません'
#                messagebox.showinfo('確認', str_tmp)
    df_date_menu = df_date_menu.sort_index()
#    print(df_date_menu)
    
    #　欠損値を入力
    if (from_day < datetime.datetime(2020,8,26,0,0,0)) & \
        (datetime.datetime(2020,8,25,0,0,0) < end_day) & (lunch_diner == '01'):
        df_date_menu.loc[datetime.datetime(2020,8,25,0,0,0),'name_ヘルシー'] = '赤魚の煮付け'
        df_date_menu.loc[datetime.datetime(2020,8,25,0,0,0),'ID_ヘルシー'] = 270
    
    return df_date_menu


#%% pythonのweekdayの数字を入力するとDBの曜日の数字が出力される
def youbi_python2DB(PY_weekday):
    if PY_weekday <= 5:
        DB_weekday = PY_weekday + 2
    elif PY_weekday == 6:#日曜日
        DB_weekday = 1
    else:
        DB_weekday = -1
    return DB_weekday

#%% DBの曜日の数字を入力するとpythonのweekdayの数字が出力される
def youbi_DB2python(DB_weekday):
    if DB_weekday >= 2:
        PY_weekday = DB_weekday - 2
    elif DB_weekday == 1:#日曜日
        PY_weekday = 6
    else:
        PY_weekday = -1
    return PY_weekday

#%%

def subscribe(db,predict_day,df_products,lunch_diner):
    if predict_day.month > 4 and predict_day.month < 11:
        summer_winter = '01' # summer
    else:
        summer_winter = '02' # winter
    
    dict_col_list = { '商品ID':df_products['商品_ID'].to_list()}
    
    query_select_list = ['顧客ID', '商品ID', '個数']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    query = query_select_list_str + \
               'from M継続購入顧客台帳 ' + \
               'INNER JOIN M継続購入明細台帳 ' + \
               'ON M継続購入顧客台帳.継続ID = M継続購入明細台帳.継続ID ' + \
               'WHERE 中止 = 0' + \
               ' AND 非表示 = 0 ' + \
               ' AND 時間帯 LIKE ? ' + \
               ' AND 曜日 = ? ' + \
               ' AND 夏冬 = ? '
               
    [query,tupls] = query_for_IN(query,dict_col_list)
    tupls = tuple([summer_winter]) + tupls
    tupls = tuple([youbi_python2DB(predict_day.weekday())]) + tupls
    tupls = tuple([lunch_diner]) + tupls
    
#    print(query)
#    print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df_subscription = obj.make_df()
    
    df_subscription['商品ID'] = df_subscription['商品ID'].astype('int')
    
    
    for i in range(len(df_subscription)):
        tmpID = df_subscription.loc[i,'商品ID']
        df_subscription.loc[i,'商品名'] = \
                            df_products[df_products['商品_ID']==tmpID].index[0]

    return df_subscription


#%% menuデータを取得
def get_menu_NOjyun(lunch_diner,from_day,end_day,db,main_menu):  
    
    if lunch_diner == '01':
        str_lunch_diner = '昼'
    else:
        str_lunch_diner = '夕'
        
    str_from_day = from_day.strftime('%Y-%m-%d')
    str_end_day  = end_day.strftime('%Y-%m-%d')
    
    query_select_list = ['年月日','料理名','D_料理.料理ID','小区分']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成
    str_syoukubun = " AND (小区分 = "
    for m in main_menu:
        str_syoukubun += "'" + m + "'"
        if m == main_menu[-1]:
            str_syoukubun += ")"
        else:
            str_syoukubun += " OR 小区分 = "
    
    query = query_select_list_str + \
               'from D_料理' + \
               " INNER JOIN M_料理 ON D_料理.料理ID = M_料理.料理ID" + \
               " WHERE 区分 = '" + str_lunch_diner + "'" + \
               str_syoukubun + \
               " AND 年月日 >= '" + str_from_day + "'"\
               " AND 年月日 <= '" + str_end_day + "';"
    
    tupls = ()
    
#    print(query)
    #print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df_menu = obj.make_df()
#    print(df_menu)
    
    # 曜日の列を追加
    df_menu = df_menu.set_index('年月日')
    df_menu['曜日'] = df_menu.index.weekday
    
    df_menu = df_menu.rename(columns={'D_料理.料理ID': '料理ID'})

    
    
    return df_menu


#%% 仕出しデータを取得
def get_shidashi(day1):  
    db = "特別弁当"
    query_select_list = ['時間帯','配達方面','品名','数量','注文日','顧客名','配達時間','店頭引取時間',
                         '単価','備考','メモ','キャンセル']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成    
    query = query_select_list_str + \
               'from D注文基礎' + \
               " INNER JOIN D注文内容 ON D注文基礎.注文ID = D注文内容.注文ID" + \
               " WHERE 注文日 = '" + day1.strftime('%Y-%m-%d') + "';"
    
    tupls = ()
    
#    print(query)
    #print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    df['数量'] = df['数量'].astype(int)
    df['単価'] = df['単価'].astype(int)
#    print(df)

    return df

def get_shidashi_period(from_day,end_day):  
    db = "特別弁当"
    query_select_list = ['時間帯','配達方面','品名','数量','注文日','顧客名','配達時間','店頭引取時間',
                         '単価','備考','メモ','キャンセル']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成    
    query = query_select_list_str + \
               'from D注文基礎' + \
               " INNER JOIN D注文内容 ON D注文基礎.注文ID = D注文内容.注文ID" + \
               " WHERE 注文日 >= '" + from_day.strftime('%Y-%m-%d') + "'" + \
               " AND 注文日 <= '" + end_day.strftime('%Y-%m-%d') + "'"    
    
    tupls = ()
    
#    print(query)
    #print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    df['数量'] = df['数量'].astype(int)
    df['単価'] = df['単価'].astype(int)
#    print(df)

    return df

# from_day = datetime.date(2021,6,5)
# end_day = datetime.date(2021,6,6)
# df = get_shidashi_period(from_day,end_day)

#%% 配達共通の予想数を取得
def get_predict_num(day1):
    db = "配達共通"
    query_select_list = ['配達日','店舗名','商品名','予想数']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成    
    query = query_select_list_str + \
               'from 予想数' + \
               " WHERE 配達日 = '" + day1.strftime('%Y-%m-%d') + "';"
    
    tupls = ()
    
#    print(query)
    #print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    df['予想数'] = df['予想数'].astype(int)
#    print(df)

    return df


# day1 = datetime.date(2021,4,7)
# df = get_predict_num(day1)


#%% 配達共通の製造数を取得
def get_seizou_num(day1,column):
    db = "配達共通"
    query_select_list = ['日付','商品名',column]
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成    
    query = query_select_list_str + \
               'from 製造' + \
               " WHERE 日付 = '" + day1.strftime('%Y-%m-%d') + "';"
    
    tupls = ()
    
    #print(query)
    #print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    df[column] = df[column].astype(int)
#    print(df)

    return df


# day1 = datetime.date(2021,6,5)
# df = get_seizou_num(day1,'製造数')

#%% 配達共通の製造数を取得　期間指定
def get_seizou_num_term(day1,day2,column):
    db = "配達共通"
    query_select_list = ['日付','商品名',column]
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成    
    query = query_select_list_str + \
               'from 製造' + \
               " WHERE 日付 >= '" + day1.strftime('%Y-%m-%d') + "'" + \
               " AND 日付 <= '" + day2.strftime('%Y-%m-%d') + "';"
    
    tupls = ()
    
    #print(query)
    #print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
    df[column] = df[column].astype(int)
#    print(df)

    return df


# day1 = datetime.date(2021,9,5)
# day2 = datetime.date(2021,9,6)
# df = get_seizou_num_term(day1,day2,'製造数')

#%% 非表示でない顧客を取得
def get_kokyaku_visible(db):
    query_select_list = ['顧客ID','名前']
    query_select_list_str = query_select_str(query_select_list)
    
    # query文作成    
    query = query_select_list_str + \
               'from 顧客台帳' + \
               " WHERE 非表示 = 0;"
    
    tupls = ()
    
#    print(query)
    #print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
#    print(df)

    return df


# db= '鈴鹿店'
# df = get_kokyaku_visible(db)

#%% 販売データで購入がない顧客を割り出す
def get_kokyaku_hanbai_rireki(db):
    query_select_list = ['顧客ID','顧客名']
    
    # query文作成    
    query = 'select distinct 顧客ID,顧客名 from 販売データ' + \
               " WHERE 日付 > 210517 AND 日付 < 210524;"
    
    tupls = ()
    
#    print(query)
    #print(tupls)
    
    #　データ抽出、ｄｆ作成
    df_columns = query_select_list
    obj = sql2df(query,tupls,db,df_columns)
    df = obj.make_df()
#    print(df)

    return df

# db= '四日市店'
# df = get_kokyaku_hanbai_rireki(db)