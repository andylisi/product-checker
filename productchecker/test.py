from flask import render_template, url_for, flash, redirect, request
from productchecker.models import User, Product, ProductHistory
from productchecker import db
import logging, sys
from datetime import datetime
from sqlalchemy import func

'''
    sql = "Select p.alias, p.brand, p.model, p.retailer, CASE ph.stock WHEN True THEN 'Yes' ELSE 'No' END As stock, ph.price, MAX(ph.checked_ts) As checked_ts\
            FROM product_history ph\
            Join product p\
            ON ph.product_id=p.id\
            WHERE p.user_id = :cur_usr\
            GROUP BY ph.product_id;"
'''
def test():
    q = db.session.query(Product.alias, Product.brand, Product.model, Product.retailer, ProductHistory.stock, ProductHistory.price, func.max(ProductHistory.checked_ts))\
        .filter(Product.user_id==1)\
        .filter(Product.id==ProductHistory.product_id)\
        .group_by(Product.id).all()
    #q = q.group_by(Product.id)
    for line in q:
        print(line)


test()

Product.alias, Product.brand, Product.model, Product.retailer, ProductHistory.stock, ProductHistory.price, func.max(ProductHistory.checked_ts).label('checked_ts'))\
<td>{{ "${:,.2f}".format(product[5]) }}</td>
<td>{{ product[6]|timeFormat }}</td>