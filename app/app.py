import os

import flask
import requests
from flask import render_template, request, make_response, url_for
from werkzeug.utils import redirect
import pymongo

app = flask.Flask(__name__)

client = pymongo.MongoClient(os.environ.get('MONGODB_STRING'))

reader = client["reader"]
books = reader["books"]
pages = reader["pages"]


def change_user_page(uid, book_id, new_page_n):
    document = {'uid': uid, 'bid': book_id, 'pn': new_page_n}
    try:
        existed = pages.update_one({'uid': uid, 'bid': book_id}, {"$set": {"pn": new_page_n}})
    except Exception as e:
        print(e)
        new = pages.insert_one(document)
    return document


def get_user_page(uid, book_id):
    document = {'uid': uid, 'bid': book_id}
    try:
        existed = dict(pages.find(document)).get('pn')
    except Exception as e:
        return -1
    return existed


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
    next_page = get_user_page(uid, book_id)
    print(next_page)
    change_user_page(uid, book_id, page_n)
    next_page = get_user_page(uid, book_id)
    print(next_page)

    with open(f'books/paging/{book_id}.csv') as f:
        d = tuple(v.split(';') for v in f.read().split('\n'))
        data = {k[0]: k[1] for k in d}
    return requests.get(data[page_n]).text


@app.route('/login')
def login_tg():
    print(request.values.get('id'), request.cookies.get('userID'))

    resp = make_response('Успешная авторизация')
    resp.set_cookie('userID', request.values['id'])
    return resp


@app.errorhandler(404)
def telegraph_files(err):
    return redirect(f'https://telegra.ph/{request.full_path }')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
