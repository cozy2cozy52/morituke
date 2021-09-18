# -*- coding: utf-8 -*-

predict_products = \
    ['昼食弁当_並','昼食弁当_大','お魚弁当_並','お魚弁当_大',
     'からあげ弁当_並','からあげ弁当_大','ハンバーグ弁当_並',
     'ハンバーグ弁当_大','お野菜弁当',
     '昼食弁当_彩','季節のお弁当','キーマカレーうどん']

predict_products_tuple = []
for p in predict_products:
    predict_products_tuple.append((p,p))