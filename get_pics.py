#!/usr/bin/python

import os
import logging
import shutil
from six.moves import urllib

from nypl import api_request

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

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
    req = urllib.request.urlopen(highResLink)
    LOG.debug(req)
    with open(filename, 'wb') as f:
        while True:
            chunk = req.read(16*1024)
            if not chunk:
                break
            f.write(chunk)

#from pprint import pprint
#LOG.debug(pprint(data))
collection_search = 'Italy, 1895-1900'
if not os.path.isdir(collection_search):
    os.mkdir(collection_search)

args = NYPLArgs('search', query=collection_search, field='title')
for uuid in get_uuids(args):
    download_uuid(uuid, path=collection_search)
