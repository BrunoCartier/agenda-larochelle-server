# vim: fileencoding=utf-8 tw=80 expandtab ts=4 sw=4 :

import json
import re

from urllib import request
from datetime import date
from time import time

JSON_URL = 'http://www.opendata.larochelle.fr/' \
           'telechargement/json/F_jeunesse_sport_et_culture/' \
           'agenda/agenda.json'
TRACKER_REGEX = r'onclick=&quot.{0,150}; &quot;'  # Ugly, please fix if possible


def is_json(json_input):
    try:
        json.loads(json_input)
    except ValueError:
        return False
    return True


def to_json_date(nonsense_string):
    l = [int(string) for string in nonsense_string.split('-')]
    return date(year=l[2], month=l[1], day=l[0]).isoformat()


def put_if_relevant(e, out_obj, french, english):
    if e.get(french) is not None and\
            e[french] != '\n' and\
            len(e[french]) > 0:
        out_obj[english] = e[french]


def sanitize(obj):
    if obj.get('description') is not None:
        obj['description'] = re.sub(TRACKER_REGEX, '', obj['description'])

    if obj.get('categories') is not None:
        obj['categories'] = obj['categories'].split(',')


def fetch_and_write():
    with request.urlopen(JSON_URL) as response:
        raw_json = response.read().decode('utf-8')

    if not is_json(raw_json):
        print('Input is not valid JSON! Exiting...')
        return

    ugly_dict = json.loads(raw_json)['data']
    pretty_dict = {
        'timestamp': int(time())
    }

    for e in ugly_dict:
        out = {
            'id': int(e['id']),
            'title': e['titre'],
            'date_start': to_json_date(e['date_debut']),
            'date_end': to_json_date(e['date_fin']),
        }

        put_if_relevant(e, out, 'lieu', 'location')
        put_if_relevant(e, out, 'categorie', 'categories')
        put_if_relevant(e, out, 'description', 'description')
        put_if_relevant(e, out, 'complement', 'more')

        sanitize(out)

        pretty_dict[int(e['id'])] = out

    # Debug
    # print(json.dumps(pretty_dict, indent=4))
    # print(raw_json)

    with open('events.json', 'w') as json_file:
        json_file.write(json.dumps(pretty_dict, indent=4))

if __name__ == '__main__':
    fetch_and_write()