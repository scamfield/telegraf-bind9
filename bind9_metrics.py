#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import time
from calendar import timegm
import re
import http.client
import xml.etree.ElementTree as ElementTree

__author__ = "Stephen Camfield"
__copyright__ = "Copyright 2019, %s" % __author__
__url__ = "https://github.com/scamfield/telegraf-bind9"

### Variables ###
BIND_HOST = 'localhost'
BIND_PORT = 8053
CACHEFILE = '/tmp/telegraf_bind.cache'
CACHELIFE = 60

### Classes / Functions ###
class Decoder(json.JSONDecoder):
    def decode(self, s):
        result = super().decode(s)
        return self._decode(result)

    def _decode(self, o):
        if isinstance(o, str) or isinstance(o, str):
            try:
                return int(o)
            except ValueError:
                return o
        elif isinstance(o, dict):
            return {k: self._decode(v) for k, v in o.items()}
        elif isinstance(o, list):
            return [self._decode(v) for v in o]
        else:
            return o

# Read from the cache if it exists.
if os.path.exists(CACHEFILE) and time.time() - os.path.getmtime(CACHEFILE) <= CACHELIFE:
    with open(CACHEFILE) as f:
        j = json.dumps(json.load(f, cls=Decoder))
        print(j)
        sys.exit(0)

# Gather stats from bind9
else:
    conn = http.client.HTTPConnection(BIND_HOST, BIND_PORT, timeout=5)
    conn.request('GET', '/')
    resp = conn.getresponse()
    if not resp.status == 200:
        print("HTTP GET Failed")
        sys.exit(1)
    content = resp.read()
    conn.close()

    root = ElementTree.fromstring(content)
    # Full version number 
    version = root.attrib['version']
    # We only want the first digit
    regex = re.match('^(\d{1})\.', version)
    version = int(regex.group(1))
    
    # Build JSON
    j = {
            'views': {},
            'server': {},
            'memory': {},
            'cache': {},
            'counter': {},
            'socketcounter': {},
            'zonemaintenancecounter': {},
            'resolvercounter': {},
            'incounter': {},
            'outcounter': {}
        }

    # not tested on version 2, so not supported
    if version == 2:
        print("Not supported version: {}".format(root.attrib), file=sys.stderr)
        sys.exit(1)

    # this is for newer version 3
    if version == 3:
        for metric in root.iterfind('./server/boot-time'):
            utc_time = time.strptime(metric.text, "%Y-%m-%dT%H:%M:%SZ")
            j['server'][metric.tag] = epoch_time = timegm(utc_time)
        for metric in root.iterfind('./server/config-time'):
            utc_time = time.strptime(metric.text, "%Y-%m-%dT%H:%M:%SZ")
            j['server'][metric.tag] = epoch_time = timegm(utc_time)
        for metric in root.iterfind('./server/counters'):
            if metric.attrib['type'] == 'nsstat':
                for stat in metric.iterfind('./counter'):
                    j['counter'][stat.attrib['name']] = stat.text
            if metric.attrib['type'] == 'sockstat':
                for stat in metric.iterfind('./counter'):
                    j['socketcounter'][stat.attrib['name']] = stat.text
            if metric.attrib['type'] == 'zonestat':
                for stat in metric.iterfind('./counter'):
                    j['zonemaintenancecounter'][stat.attrib['name']] = stat.text
            if metric.attrib['type'] == 'qtype':
                for stat in metric.iterfind('./counter'):
                    j['incounter'][stat.attrib['name']] = stat.text
            if metric.attrib['type'] == 'opcode':
                for stat in metric.iterfind('./counter'):
                    j['incounter'][stat.attrib['name']] = stat.text
        for metric in root.iterfind('./views/view/counters'):
            if metric.attrib['type'] == 'resqtype':
                for stat in metric.iterfind('./counter'):
                    j['outcounter'][stat.attrib['name']] = stat.text
            if metric.attrib['type'] == 'resstats':
                for stat in metric.iterfind('./counter'):
                    j['resolvercounter'][stat.attrib['name']] = stat.text
            if metric.attrib['type'] == 'cachestats':
                for stat in metric.iterfind('./counter'):
                    j['cache'][stat.attrib['name']] = stat.text
        
        # Bind view stats
        for metric in root.iterfind('./views/view'):
            counters = {}
            for stat in metric.iterfind('./counters'):
                 for counter in stat.iterfind('./counter'):
                    counters[counter.attrib['name']] = counter.text
            j['views'][metric.attrib['name']] = counters
        for metric in root.iterfind('./views/view/cache'):
                for stat in metric.iterfind('./rrset'):
                    j['views'][metric.attrib['name']][stat.findtext('./name').replace('!', '_').join(('rrsets_',''))] = stat.findtext('./counter')

        for metric in root.iterfind('./memory/summary/*'):
            j['memory'][metric.tag] = metric.text

    # write gathered metrics to cache file
    with open(CACHEFILE, 'w') as f:
        json.dump(j, f)
 
# Display the metrics
with open(CACHEFILE) as f:
    j = json.dumps(json.load(f, cls=Decoder))
    print(j)
    sys.exit(0)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
