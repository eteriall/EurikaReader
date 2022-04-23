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
    if request.cookies.get('userID') is None:
        return render_template('login.html')
    else:
        if request.values.get('next') is not None:
            return redirect(request.values['next'])
        return 'Вы уже авторизованы. Выберите книгу в боте, чтобы начать читать.'


@app.route('/<book_id>/page/<page_n>')
def page(book_id, page_n):
    if request.cookies.get('userID') is None:
        return redirect(url_for('.login', next=request.url))

    uid = request.cookies.get('userID')
    print(uid, 'uid')
    change_user_page(uid, book_id, page_n)

    with open(f'posting/books/paging/{book_id}.csv') as f:
        d = tuple(v.split(';') for v in filter(lambda x: x != '', f.read().split('\n')))
        data = {k[0]: k[1] for k in d}
    return requests.get(data[page_n]).text


@app.route('/login')
def login_tg():
    print(request.cookies.get('next'), request.values.get('id'), request.cookies.get('userID'))

    resp = make_response('Успешная авторизация')
    resp.set_cookie('userID', request.values['id'])
    return resp


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
