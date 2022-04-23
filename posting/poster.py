import sys
import time

import pypandoc
import os
import tqdm
import telegraph.utils
from telegraph import Telegraph
import bs4

domain = 'https://eurika-reader.herokuapp.com'


class Poster:
    def __init__(self):
        self.t = Telegraph(access_token=os.environ.get('TELEGRAPH_ACCESS_TOKEN'))
        os.environ.setdefault('PYPANDOC_PANDOC', '/opt/homebrew/bin/pandoc')

    def split_html_book(self, soup, divider='h3', lines_n=50):
        elements, temp, tag = [], [], None
        s = telegraph.utils.html_to_nodes(str(soup))

        def flatten_dict(dct):
            nonlocal elements, tag

            if isinstance(dct, str):
                elements += [f'<{tag}>{dct}</{tag}>']
            elif isinstance(dct, list):
                for x in dct:
                    flatten_dict(x)
            elif dct.get('tag') == 'br':
                return "<br>"
            elif dct.get('children') is not None:
                tag = dct.get('tag')
                for x in dct['children']:
                    flatten_dict(x)

        flatten_dict(s)
        elements = tuple(filter(lambda x: x is not None, elements))
        chapters, temp = [], []

        if elements.count(divider) > 1:
            for element in elements:
                if element.startswith(f'<{divider}>'):
                    chapters += (temp,)
                    temp = [element]
                else:
                    temp += [element]
            res, temp = [], ''
            for chapter in chapters:
                ns = sys.getsizeof(telegraph.utils.html_to_nodes(temp + ''.join(chapter)))
                if len(temp) * 2 / 1024 > 16:
                    res += [temp]
                    temp = ''
                else:
                    temp += ''.join(chapter)
            res = [temp] if res == [] else res
        else:
            res = [elements[x:x + lines_n] for x in range(0, len(elements), lines_n)]

        return res

    def prepare_html(self, soup: bs4.BeautifulSoup):
        """Prepares html doc for telegraph"""
        ALLOWED_TAGS = {'aside', 'b', 'blockquote', 'br', 'code', 'em', 'figcaption', 'figure',
                        'h3', 'h4', 'hr', 'i', 'iframe', 'img', 'li', 'ol', 'p', 'pre', 's',
                        'strong', 'u', 'ul', 'video'
                        }
        replaces = {'div': 'p', 'section': 'p', 'sup': 'b', 'em': 'p', 'span': 'p', 'a': 'p'}

        for t in ('img', 'table', 'colgroup', 'col', 'tbody', 'tr', 'td', 'strong'):
            for match in soup.findAll(t):
                match.unwrap()

        for s in soup.select('svg'):
            s.extract()

        for tag in [tag.name for tag in soup.find_all()]:
            if tag not in ALLOWED_TAGS:
                if tag[0] == 'h':
                    for header in soup.find_all(tag):
                        header.name = "h3"
                else:
                    for header in soup.find_all(tag):
                        header.name = replaces[tag]
        for x in soup.find_all():
            if len(x.get_text(strip=True)) == 0 and x.name not in ['br', 'img']:
                x.extract()
        return soup

    def convert_book(self, file_path: str):
        pathname, filename = os.path.split(file_path)
        new_file_path = file_path.replace('.epub', '.html')

        # Convert EPUB to HTML
        pypandoc.convert_file(file_path,
                              format='epub', to='html5',
                              extra_args=['--read=epub', f'--extract-media={pathname}', '--wrap=none'],
                              encoding='utf-8', outputfile=new_file_path,
                              verify_format=True
                              )
        return new_file_path

    def post_book(self, file_path: str):

        pathname, filename = os.path.split(file_path)
        book_id = filename.split('.')[0]

        # Get the book title from metadata
        with open('books/meta.csv') as f:
            books_meta = {v[0]: (v[1], v[2]) for v in tuple(k.split(';') for k in f.read().split('\n'))}
            title, author = books_meta[book_id]

        # Convert HTML to Telegraph
        with open(file_path, mode='r') as f:
            html = f.read()

            soup = bs4.BeautifulSoup(html, 'html.parser')
            soup = self.prepare_html(soup)
            sp = self.split_html_book(soup, lines_n=100)

            with open(f'books/paging/{book_id}.csv', mode='w') as paging_db:
                for page_n, elem in tqdm.tqdm(enumerate(sp, 1)):

                    # Add next/previous pages URLs
                    elem = ''.join(elem)
                    prev_p_url, next_p_url = (f'{domain}/{book_id}/page/{i}' for i in (page_n - 1, page_n + 1))
                    t = "<br> <b>"
                    if page_n != 1:
                        t += f'<a href="{prev_p_url}"> Предыдущая страница </a>'
                    if page_n != 1 and page_n != len(sp):
                        t += ' | '
                    if page_n != len(sp):
                        t += f'<a href="{next_p_url}"> Следующая страница </a>'
                    t += '</b> <br>'

                    # Publish page to Telegraph
                    while True:
                        try:
                            time.sleep(1)
                            response = self.t.create_page(
                                title,
                                author_name=f'{author}, страница {page_n}',
                                html_content=t + elem + t
                            )
                            url = 'https://telegra.ph/{}'.format(response['path'])
                            paging_db.write(f'{page_n};{url}\n')
                            break
                        except Exception as e:
                            print(e)
                            continue


p = Poster()
p.post_book('books/3.html')
