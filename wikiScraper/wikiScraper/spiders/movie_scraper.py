from pathlib import Path
from urllib.parse import urljoin

import scrapy


class MoviesInfoParser(scrapy.Spider):
    name = "movies"
    # Стартовая страница
    start_urls = [
        "https://ru.wikipedia.org/wiki/%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:%D0%A4%D0%B8%D0%BB%D1%8C%D0%BC%D1%8B_%D0%BF%D0%BE_%D0%B0%D0%BB%D1%84%D0%B0%D0%B2%D0%B8%D1%82%D1%83",
    ]
    # Не учитывать robots.txt
    custom_settings = {
        'ROBOTSTXT_OBEY': False
    }

    def parse(self, response):
        base_url = response.url
        # Извлекаем href ссылки на страницы фильмов
        movie_page_links = response.xpath("//*[@id='mw-pages']/div/div/div/ul/li/a/@href").getall()
        for page in movie_page_links: 
            # Составляем полную ссылку на страницу фильма и извлекаем из нее информацию
            page_link = urljoin(base_url, page)
            yield response.follow(page_link, self.info_parse)

        # Извлекаем href ссылку на следующую страницу
        pagination_link = response.xpath("/html/body/div[3]/div[3]/div[5]/div[2]/div[2]/a[2]/@href").get()
        if pagination_link is not None:
            # Составляем полную ссылку на следующую страницу и переходим на нее
            next_page_url = urljoin(base_url, pagination_link)
            yield response.follow(next_page_url, self.parse)

    def info_parse(self, response):
        # Извлекаем информацию о фильме
        movie_info = {'title': None, 'genres': [], 'year': None, 'director': [], 'country': None}
        # Извлекаем название фильма
        quote = response.css("table.infobox")
        movie_info['title'] = "".join(quote.css("th.infobox-above::text").get())

        # Информация о фильме хранится в таблице, состоящей из строк и столбцов
        for row in response.xpath("/html/body/div[3]/div[3]/div[5]/div[1]/table[1]/tbody/tr"):
            # Достаем название атрибута
            attribute = row.xpath("th//text()").get()
            if attribute is not None:
                attribute.strip()
            else:
                continue
            
            # Достаем значение атрибута и удаляем из него лишние символы
            values = [line.strip().replace(',', '') for line in row.xpath("td//text()").getall() if line.strip()]
            filtered_values = [value for value in values if not value.startswith('[') and value != '']
            value = ",".join(filtered_values)


            # Если атрибут - Жанр (Genre), то сохраняем его в поле 'genres' и т.д.
            if 'Жанр' in attribute or 'Жанры' in attribute:
                movie_info['genres'] = value
            elif attribute == 'Год':
                movie_info['year'] = value
            elif attribute in ['Режиссёр', 'Режиссёры']:
                movie_info['director'] = value
            elif attribute in ['Страна', 'Страны']:
                movie_info['country'] = value

        yield movie_info
