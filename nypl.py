#!/usr/bin/python

import argparse
import logging

import requests
from pprint import pprint

BASE_API_URL="http://api.repo.nypl.org/api/v1"

LOG = logging.getLogger('nypl.main')

def parse_cmdline():
    parser = argparse.ArgumentParser()
    parser.add_argument("method", help="API method",
                        choices=['search', 'mods', 'items', 'collections',
                                 'mods_captures', 'item_details'])
    parser.add_argument("--auth-token", help="Auth token file", required=True)
    parser.add_argument("--query", help="String to query")
    parser.add_argument("--field", help="MODS field to query")
    parser.add_argument("--uuid", help="Collection/item/capture UUID")
    args = parser.parse_args()

    if args.method == 'search':
        if not args.query:
            raise Exception("Query terms undefined")
        if args.uuid:
            raise Exception("UUID argument not valid for query method")
    else:
        if args.query:
            raise Exception("Query terms only valid for query method")
    return args


def api_request(args, headers):
    resp = None
    if args.method == 'search':
        params = {'q': args.query}
        if args.field:
            params.update({'field': args.field})
        resp = requests.get(BASE_API_URL + "/items/search",
                            params=params, headers=headers)
    elif args.method in ['mods', 'items', 'collections']:
        url = "/".join([BASE_API_URL, args.method, args.uuid])
        resp = requests.get(url, headers=headers)
    elif args.method in ['mods_captures', 'item_details']:
        url = BASE_API_URL + "/items/%s/%s" % (args.method, args.uuid)
        resp = requests.get(url, headers=headers)
    else:
        raise Exception("Unknown method: %s" % args.method)

    try:
        return resp.json()
    except:
        resp.raise_for_status()
        raise


def main():
    args = parse_cmdline()
    with open(args.auth_token, 'r') as f:
        token = f.read().strip()
    headers = {'Authorization': "Token token=%s" % token}
    data = api_request(args, headers)
    pprint(data)

if __name__ == '__main__':
    main()
