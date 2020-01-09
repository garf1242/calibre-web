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
    from urllib.parse import quote_plus
else:
    from urllib import quote_plus

from cps.plugins import MetadataProvider

class GoogleMetadataProvider(MetadataProvider):
    name = "google"
    title = "Google"
    description = "A Google metadata provider"
    version = "0.1"
    _search_url = "https://www.googleapis.com/books/v1/volumes";

    def search_results(self, book, additional_keywords={}):
        title_search = additional_keywords.get('title', book.title)
        if not title_search:
            return []
        headers = {
            # A random user agent, but a valid one
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
        }
        r = requests.get(self._search_url + "?q=" + quote_plus(title_search), headers=headers)
        if r.status_code != 200:
            return []
        json = r.json()
        if "items" not in json:
            return []
        result = []
        for item in json["items"]:
            info = item.get('volumeInfo', {})
            book = {
                'id': item['id'],
                'title': info.get('title', ''),
                'authors': info.get('authors', []),
                'description': info.get('description', ''),
                'publisher': info.get('publisher', ''),
                'publishedDate': info.get('publishedDate', ''),
                'tags': info.get('categories', []),
                'rating': info.get('averageRating', 0),
                'cover': info.get('imageLinks', {}).get('thumbnail', '/static/generic_cover.jpg'),
                'url': 'https://books.google.com/books?id=' + item['id'],
                'source': {
                        'id': 'google',
                        'description': 'Google Books',
                        'url': 'https://books.google.com/'
                }
            }
            result.append(book)
        return result

