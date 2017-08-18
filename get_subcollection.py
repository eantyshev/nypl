#!/usr/bin/python

import os
import logging
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
    while page < 100: # sanity restriction
        args.page = page
        data = api_request(args)
        response = data['nyplAPI']['response']
        request = data['nyplAPI']['request']
        items = response.get('capture')
        if not items:
            LOG.debug("No capture on page %s", args.page)
            return
        for item in items:
            yield item['uuid']
        page += 1


def download_tiff(uuid, path="."):
    args = NYPLArgs('mods_captures', uuid=uuid)
    data = api_request(args)
    capture = data['nyplAPI']['response']['capture']
    highResLink = capture['highResLink']['$']
    title = capture['title']['$']

    filename = os.path.join(path, "%(title)s.tiff" % locals())
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
collection_search = 'Argentina'
if not os.path.isdir(collection_search):
    os.mkdir(collection_search)

args = NYPLArgs('items', uuid='5246dff0-c52f-012f-a661-58d385a7bc34')
for uuid in get_uuids(args):
    download_tiff(uuid, path=collection_search)
