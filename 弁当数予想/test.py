#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 30 18:36:58 2021

@author: user
"""

# import pyodbc
 
# #cnxn = pyodbc.connect('DSN=CData SQL Sys;')
# #cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};User=sa;Password=ofu;Database=鈴鹿店;Server=DEVELOP;Port=1433;')
# cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};User=sa;Password=ofu;Server=DEVELOP;')
# cursor = cnxn.cursor()
# cursor.execute("SELECT @@version;")
# rows = cursor.fetchall()
# while rows:
#     print(rows[0])
#     rows = cursor.fetchone()
    
#%%

import urllib
from sqlalchemy import create_engine

driver = 'ODBC Driver 17 for SQL Server'
server = '192.168.24.30'
username = 'sa'
password = 'ofu'
db = '鈴鹿店'

odbc_connect = urllib.parse.quote_plus(
    'DRIVER={%s};SERVER=%s;UID=%s;PWD=%s;DATABASE=%s;' % (driver, server, username, password,db))
engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % odbc_connect)

with engine.connect() as conn:
    #rs = conn.execute('SELECT @@VERSION as version')
    rs = conn.execute('select 顧客名 from 販売データ WHERE 日付 > 210517 AND 日付 < 210524;')
    for row in rs:
        print(row['顧客名'])
