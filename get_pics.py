#!/usr/bin/python

import argparse
import os, sys
import logging
import shutil
import zipfile
from six.moves import urllib

from nypl import api_request

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)


def parse_cmdline():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", help="Action to perform with given collection",
                        choices=['download', 'archive', 'all'],
                        default='all')
    parser.add_argument("--auth-token", help="Auth token file", required=True)
    parser.add_argument("--title", help="Collection title", required=True)
    args = parser.parse_args()

    return args

class NYPLArgs(object):
    def __init__(self, method, auth_token='api_token.dat', query=None, field=None,
                 uuid=None):
        self.method = method
        self.query = query
        self.field = field
        self.uuid = uuid
        self.auth_token = auth_token



def get_uuids(args):
    page = 1
    while page < 100:
        args.page = page
        data = api_request(args)
        response = data['nyplAPI']['response']
        request = data['nyplAPI']['request']
        items = response.get('result')
        if not items:
            LOG.debug("No results on page %s", args.page)
            return
        for item in items:
            if item[request['search_type']] != request['search_text']:
                LOG.debug("Item %s doesn't match, drop the further", item)
                return
            yield item['uuid']
        page += 1

def belongs_to_collection(data, collection='Vinkhuijzen, Hendrik Jacobus'):
    mods = data['nyplAPI']['response']['mods']
    relatedItem = mods
    while relatedItem.has_key('relatedItem'):
        relatedItem = relatedItem['relatedItem']
        if relatedItem['titleInfo']['title']['$'] == collection:
            return True
    else:
        return False

def download_uuid(uuid, path="."):
    capture_args = NYPLArgs('mods_captures', uuid=uuid)
    data = api_request(capture_args)
    if not belongs_to_collection(data, 'The Vinkhuijzen collection of military uniforms'):
        LOG.warning("Skip item %s, not from collection")
        return
    def _get_tiff_link(data):
        captures = data['nyplAPI']['response']['capture']
        if isinstance(captures, list):
            for cap in captures:
                if cap['uuid']['$'] == uuid:
                    return cap['highResLink']['$']
            else:
                raise Exception("Could not find highResLink in captures: %s" %\
                                captures)
        else:
            return captures['highResLink']['$']
        
    highResLink = _get_tiff_link(data)
    filename = os.path.join(path, "%(uuid)s.tiff" % locals())
    if os.path.exists(filename):
        LOG.info("%s is downloaded, skip...", filename)
        return
    LOG.info("Downloading %(highResLink)s to %(filename)s..." % locals())
    try:
        req = urllib.request.urlopen(highResLink)
    except Exception as e:
        LOG.error(e)
        return
    LOG.debug(req)
    with open(filename, 'wb') as f:
        while True:
            chunk = req.read(16*1024)
            if not chunk:
                break
            f.write(chunk)

def zip_archive(path):
    zip_name = path + ".zip"
    LOG.debug("Create zip archive %s", zip_name)
    with zipfile.ZipFile(zip_name, 'a', allowZip64=True) as z:
        nlist = z.namelist()
        for fn in os.listdir(path):
            if fn not in nlist:
                LOG.debug("Adding to archive %s", fn)
                z.write(os.path.join(path, fn), fn)
            else:
                LOG.debug("%s already archived", fn)

#from pprint import pprint
#LOG.debug(pprint(data))

    
def main():
    args = parse_cmdline()
    collection_search = args.title 
    if args.action in ['download', 'all']:
        if not os.path.isdir(collection_search):
            os.mkdir(collection_search)
        
        nypl_args = NYPLArgs('search', query=collection_search, field='title')
        for uuid in get_uuids(nypl_args):
            download_uuid(uuid, path=collection_search)
    if args.action in ['archive', 'all']:
        zip_archive(collection_search)

if __name__ == '__main__':
    main()
