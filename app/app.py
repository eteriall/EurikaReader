import os

import flask
import requests
from flask import render_template, request, make_response, url_for
from werkzeug.utils import redirect
import pymongo

from db import Database

app = flask.Flask(__name__)
db = Database('db.json')
pages = db["pages"]


def change_user_page(uid, book_id, new_page_n):
    document = {'uid': uid, 'bid': book_id, 'pn': new_page_n}
    print(f"user {uid} swiped {book_id} to page {new_page_n}")
    existed = None
    try:
        existed = pages.update_field({'uid': uid, 'bid': book_id}, {'pn': new_page_n})
    except Exception as e:
        new = pages.insert_one(document)
    if existed is None:
        
        new = pages.insert_one(document)
    return document


def get_user_page(uid, book_id):
    document = {'uid': uid, 'bid': book_id}
    existed = pages.find(document)
    return None if existed is None else existed.get('pn')


@app.route('/')
def login():
    if request.values.get('id') is None:
        if request.cookies.get('userID') is None:
            return render_template('login.html', next=request.values.get('next'))
        else:
            if request.values.get('next') is not None:
                return redirect(request.values['next'])
            return 'Вы уже авторизованы. Выберите книгу в боте, чтобы начать читать.'
    else:
        print(request.values.get('next'), request.values.get('id'), request.cookies.get('userID'))

        resp = make_response(redirect(request.values.get('next')))
        resp.set_cookie('userID', request.values['id'])
        return resp

@app.route("/0/page/0")
def instant_view_test_page():
    with open(f'posting/books/paging/3.csv') as f:
        d = tuple(v.split(';') for v in filter(lambda x: x != '', f.read().split('\n')))
        data = {k[0]: k[1] for k in d}
    print(data)
    return requests.get(data['2']).text

@app.route('/<book_id>')
def book(book_id):
    if request.cookies.get('userID') is None:
        return redirect(url_for('.login', next=request.url))

    uid = request.cookies.get('userID')
    page_n = get_user_page(uid, book_id)
    page_n = 1 if page_n is None else page_n

    with open(f'posting/books/paging/{book_id}.csv') as f:
        d = tuple(v.split(';') for v in filter(lambda x: x != '', f.read().split('\n')))
        data = {k[0]: k[1] for k in d}
    return requests.get(data[page_n]).text

@app.route('/<book_id>/page/<page_n>')
def page(book_id, page_n):
    if request.cookies.get('userID') is None:
        return redirect(url_for('.login', next=request.url))

    uid = request.cookies.get('userID')
    change_user_page(uid, book_id, page_n)
    
    with open(f'posting/books/paging/{book_id}.csv') as f:
        d = tuple(v.split(';') for v in filter(lambda x: x != '', f.read().split('\n')))
        data = {k[0]: k[1] for k in d}
    return requests.get(data[page_n]).text
    

@app.route('/test')
def infinite_scroll_test():
    return render_template('index.html')


@app.errorhandler(404)
def telegraph_files(err):
    return redirect(f'https://telegra.ph/{request.full_path}')

@app.route('/test2')
def test():
    return render_template('test.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
