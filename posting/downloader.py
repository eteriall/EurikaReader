import requests
import bs4
import urllib.request
import wget

genres = ()

for genre in genres:
    for page_n in range(1, 3):
        page_url = f'https://avidreaders.ru/genre/{genre}/{page_n}'
        print(page_url)
        buttons = bs4.BeautifulSoup(requests.get(page_url).text,
                                    features="html.parser").find_all(attrs={'class': 'btn'})
        books = tuple(map(lambda x: x['href'].split('/')[-1], buttons))
        for book in books:
            file_url = f'https://avidreaders.ru/download/{book}?f=epub'
            download_url = bs4.BeautifulSoup(requests.get(file_url).text, features="html.parser") \
                .find('div', attrs={'class': 'dnld-info'}).find('a')['href']
            print(download_url)
            # https://avidreaders.ru/api/get.php?b=8999&f=epub
            # https://avidreaders.ru/api/get.php?b=8999&f=epub

            resp = requests.get(download_url)
            print(resp.status_code)
            open('books/' + book.replace('.html', '.epub'), 'wb').write(resp.content)

for i in range(428843 - 100, 428843):
    print(i)
    f = wget.download(f"https://www.rulit.me/download-books-{i}.html?t=epub", f'books/{i}.epub')
