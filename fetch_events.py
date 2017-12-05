# vim: fileencoding=utf-8 tw=80 expandtab ts=4 sw=4 :

import json
import locale
import re

from urllib import request
from datetime import date
from time import time, mktime

JSON_URL = 'https://opendata.larochelle.fr/dataset/evenementiel-agenda-des-evenements/?download=1661'
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
        # Transform to list while removing duplicates
        obj['categories'] = list(dict.fromkeys(obj['categories'].split(',')))


def to_timestamp(d):
    return int(mktime(date(
        year=int(d[0]),
        month=int(d[1]),
        day=int(d[2]),
    ).timetuple()))


def get_delta(d1, d2):
    d1 = date(year=int(d1[0]), month=int(d1[1]), day=int(d1[2]))
    d2 = date(year=int(d2[0]), month=int(d2[1]), day=int(d2[2]))
    delta = d2 - d1
    return delta.days


def fetch():
    with request.urlopen(JSON_URL) as response:
        raw_json = response.read().decode('utf-8')

    if not is_json(raw_json):
        print('Input is not valid JSON! Exiting...')
        return

    ugly_dict = json.loads(raw_json)['data']

    write_v1(ugly_dict)
    write_v2(ugly_dict)


def write_v1(ugly_dict):
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

        out['ts_end'] = to_timestamp(out['date_end'].split('-'))

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


def write_v2(ugly_dict):
    pretty_dict = {
        'timestamp': int(time()),
        'short': [],  # Array of months, then events by month
        'long': [],  # Array of events
    }
    all_events = []

    for e in ugly_dict:
        out = {
            'id': int(e['id']),
            'title': e['titre'],
            'date_start': to_json_date(e['date_debut']),
            'date_end': to_json_date(e['date_fin']),
        }

        out['duration'] = get_delta(
            out['date_start'].split('-'),
            out['date_end'].split('-'),
        ) + 1
        out['ts_start'] = to_timestamp(out['date_start'].split('-'))
        out['ts_end'] = to_timestamp(out['date_end'].split('-'))

        put_if_relevant(e, out, 'lieu', 'location')
        put_if_relevant(e, out, 'categorie', 'categories')
        put_if_relevant(e, out, 'description', 'description')
        put_if_relevant(e, out, 'complement', 'more')

        sanitize(out)

        all_events.append(out)

    all_events = sorted(all_events, key=lambda event: event['ts_start'])
    current_month = None
    current_month_content = []

    for event in all_events:
        if event['duration'] > 4:
            pretty_dict['long'].append(event)
        else:
            d = event['date_start'].split('-')
            date_start = date(year=int(d[0]), month=int(d[1]), day=int(d[2]))
            event_month = date_start.strftime('%B %Y')

            if not current_month:
                current_month = event_month

            if event_month != current_month:
                # noinspection PyTypeChecker
                pretty_dict['short'].append({
                    'month': current_month,
                    'events': current_month_content,
                })
                current_month = event_month
                current_month_content = []

            current_month_content.append(event)

    with open('events-v2.json', 'w') as json_file:
        json_file.write(json.dumps(pretty_dict, indent=4))


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
    fetch()
