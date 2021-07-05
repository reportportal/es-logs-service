"""
* Copyright 2019 EPAM Systems
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
* http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
"""

import re
from urllib.parse import urlparse
import string


def remove_credentials_from_url(url):
    parsed_url = urlparse(url)
    new_netloc = re.sub("^.+?:.+?@", "", parsed_url.netloc)
    return url.replace(parsed_url.netloc, new_netloc)


def split_words(text, min_word_length=0, only_unique=False, split_urls=True,
                remove_all_punctuation=False, to_lower=False):
    all_unique_words = set()
    all_words = []
    translate_map = {}
    for punct in string.punctuation + "<>{}[];=()'\"":
        if remove_all_punctuation or\
                (punct != "." and punct != "_" and (split_urls or punct not in ["/", "\\"])):
            translate_map[punct] = " "
    text = text.translate(text.maketrans(translate_map)).strip().strip(".")
    for word_part in text.split():
        word_part = word_part.strip().strip(".")
        if to_lower:
            word_part = word_part.lower()
        for w in word_part.split():
            if w != "" and len(w) >= min_word_length:
                if not only_unique or w not in all_unique_words:
                    all_unique_words.add(w)
                    all_words.append(w)
    return all_words
