# -*- coding: utf-8 -*-

#  This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#    Copyright (C) 2012-2019 mutschler, cervinko, ok11, jkrehm, nanu-c, Wineliva,
#                            pjeby, elelay, idalin, Ozzieisaacs
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import division, print_function, unicode_literals

import sys
import requests
if (sys.version_info > (3, 0)):
    from urllib.parse import quote
else:
    from urllib import quote

from cps.plugins import MetadataProvider


class DoubanMetadataProvider(MetadataProvider):
    name = "douban"
    title = "Douban"
    description = "A Douban metadata provider"
    version = "0.1"
    _search_url = "https://api.douban.com/v2/book/search"
    _apikey = "0df993c66c0c636e29ecbb5344252a4a"

    def search_results(self, book, additional_keywords={}):
        title_search = additional_keywords.get('title', book.title)
        if not title_search:
            return []
        headers = {
            # A random user agent, but a valid one
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
        }
        r = requests.get(self._search_url
                         + "?apikey=" + self._apikey
                         + "&q=" + quote(title_search)
                         + "&fields=all&count=10", headers=headers)
        if r.status_code != 200:
            return []
        json = r.json()
        if "books" not in json:
            return []
        result = []
        for item in json["books"]:
            published = ''
            if 'pubdate' in item:
                year, month= '1', '1'
                split = item['pubdate'].split('-')
                if len(split) == 1:
                    year = split[0]
                else:
                    year, month = split[:2]
                try:
                    published = "%d-%02d-%02d" % (int(year), int(month), 1)
                except ValueError:
                    pass
            rating = 0
            try:
                rating = float(item.get('rating', {}).get('average', 0)) / 2.0
            except ValueError:
                pass
            book = {
                'id': item['id'],
                'title': item.get('title', ''),
                'authors': item.get('author', []),
                'description': item.get('summary', ''),
                'publisher': item.get('publisher', ''),
                'publishedDate': published,
                'tags': [ tag['title'].lower().replace(',', '_') for tag in item.get('tags', []) if 'title' in tag ],
                'rating': rating,
                'series': item.get('series', {}).get('title', ''),
                'cover': item.get('image', '/static/generic_cover.jpg'),
                'url': 'https://book.douban.com/subject/' + item['id'],
                'source': {
                        'id': 'douban',
                        'description': 'Douban Books',
                        'url': 'https://book.douban.com/'
                }
            }
            result.append(book)
        return result

