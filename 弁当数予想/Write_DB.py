# -*- coding: utf-8 -*-
"""
Created on Sun Feb 21 12:19:24 2021

@author: user
"""
import datetime
import 弁当数予想.SQL2DF as SQL2DF

import urllib
from sqlalchemy import create_engine

#%%
def login(db):

    driver = 'ODBC Driver 17 for SQL Server'
    server = '192.168.24.10' # 30:dev  10:ofukuro
    username = 'sa'
    password = 'ofu'
    
    odbc_connect = urllib.parse.quote_plus(
        'DRIVER={%s};SERVER=%s;UID=%s;PWD=%s;DATABASE=%s;' % (driver, server, username, password,db))
    engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % odbc_connect)

    return engine.connect()

#%%
def write_predict_insert():
    sql = """INSERT INTO 予想数(配達日,店舗名,商品名,予想数,予備数) 
             VALUES (?,?,?,?,?)"""
    return sql
#%% レコードがなかったら挿入、あったら更新
def write_predict_insert_update():
    sql = """MERGE INTO 予想数 AS A
    USING (SELECT ? AS 配達日,? AS 店舗名, ? AS 商品名, ? AS 予想数, ? AS 予備数 ) AS B
    ON　(A.配達日 = B.配達日) and (A.店舗名 = B.店舗名) and (A.商品名 = B.商品名)　
    WHEN MATCHED THEN
        UPDATE SET
             予想数 = B.予想数
            ,予備数 = B.予備数
    WHEN NOT MATCHED THEN
        INSERT (配達日,店舗名,商品名,予想数,予備数)
        VALUES
        (B.配達日,B.店舗名,B.商品名,B.予想数,B.予備数
        );"""
    return sql
#%%
def write_predict(store,product,num,predict_day):
    
    str_day1 = predict_day.strftime('%Y-%m-%d')
    
    db = "配達共通"
    con = login(db)
    
    df = SQL2DF.get_predict_num(predict_day)
    df_tmp = df[df['商品名']==product]

    if len(df_tmp)>0:
        sql =  """UPDATE 予想数 SET 予想数=? WHERE 配達日=? AND 商品名=? AND 店舗名=?;"""
        con.execute(sql,num,str_day1,product,store)
    else:
        sql =  """INSERT INTO 予想数 (配達日,店舗名,商品名,予想数,予備数)
                VALUES (?,?,?,?,0);"""
        con.execute(sql,str_day1,store,product,num)
    
write_predict("鈴鹿店","昼食弁当_並",40,datetime.date(2021,6,23))

#%%　メニューの非表示を更新

def menu_invisible(db):
    db = "献立"
    con = login(db)
    
    sql = "UPDATE M_料理 SET 非表示 = 1, 時間帯 = '' "
    con.execute(sql)
    con.commit()
    con.close()
    
def menu_visible_update(db,list_ID,lunch_dinner):
    
    db = "献立"
    con = login(db)
    
    sql = "UPDATE M_料理 SET 非表示 = 0, 時間帯 = '" + lunch_dinner + "' WHERE 料理ID > 0" # WHERE 料理ID > 0　は意味がないが、IN句の関数にANDがついてしまうため
    dict_col_list = {'料理ID':list_ID}
    [sql,tupls] = SQL2DF.query_for_IN(sql,dict_col_list)
    con.execute(sql,tupls)
    con.commit()
    
    con.close()

#%% 製造数
def write_seizou(predict_day,product,num,column):
    
    db = "配達共通"
    con = login(db)
    
    str_day1 = predict_day.strftime('%Y-%m-%d')
    df = SQL2DF.get_seizou_num(predict_day,column)
    
    df_tmp = df[(df['日付']==str_day1)&(df['商品名']==product)]
    
    if column == '製造数':
        if len(df_tmp)>0:
            sql =  """UPDATE 製造 SET 製造数=? WHERE 日付=? AND 商品名=?;"""
            con.execute(sql,num,str_day1,product)
        else:
            sql =  """INSERT INTO 製造 (日付,商品名,製造数,調整数)
                    VALUES (?,?,?,0);"""
            con.execute(sql,str_day1,product,num)
    else:
        if len(df_tmp)>0:
            sql =  """UPDATE 製造 SET 調整数=? WHERE 日付=? AND 商品名=?;"""
            con.execute(sql,num,str_day1,product)
        else:
            sql =  """INSERT INTO 製造 (日付,商品名,製造数,調整数)
                    VALUES (?,?,0,?);"""
            con.execute(sql,str_day1,product,num)
#write_seizou(datetime.date(2021,6,12),"昼食弁当_大",5,'調整数')

#%% 顧客を非表示にする
def customer_invisible_update(db,list_ID):
    
    con = login(db)
    
    sql = "UPDATE 顧客台帳 SET 非表示 = 1 WHERE 顧客ID > 0" # WHERE 料理ID > 0　は意味がないが、IN句の関数にANDがついてしまうため
    dict_col_list = {'顧客ID':list_ID}
    [sql,tupls] = SQL2DF.query_for_IN(sql,dict_col_list)
    con.execute(sql,tupls)
    con.commit()
    
    con.close()

#customer_invisible_update('鈴鹿店',[3,4])