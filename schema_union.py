#!/usr/bin/env python

# Copyright (C) 2014 Dan Scott <dscott@laurentian.ca>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Proof-of-concept union catalogue via sitemaps + schema.org

This script currently takes a sitemap URL as a starting point, determines if
there are any linked sitemaps, and crawls all of the URLs it is given with a
singular goal of extracting schema.org structured data from each URL.

By default the script expects to find the metadata marked up in RDFa, but you
can control that via a command line switch. For example, "-p microdata" will
tell the script to parse the metadata in a given URL as microdata instead.

By default the script generates n3 output, but you can control that via a
command line switch. For example, "-t turtle" generates turtle output.

There are many improvements to be made to this script before it would be
suitable for a real life deployment:

* It currently has no idea when the last time it was run, so it will blindly
  crawl every URL in the sitemaps--even if the sitemaps contain <lastmod>
  elements that would enable it to only crawl those URLs that have changed
  since the last time it has run.

* Also, thus far the script has no opinion about where the retrieved metadata
  should be stored. One could target a triple store or a relational database,
  for example--but a more functional script should probably work out of the
  box with _something_ to provides some simple search capabilities.

* sitemaps.org encourages site owners to gzip-compress large sitemaps, but
  this script currently simply blindly expects regular XML and would have
  a horrendous time trying to parse a gzipped XML file.
"""
import logging
import sys

try:
    from urllib.request import urlopen
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
    from urllib import urlopen

from xml.dom.minidom import parse
from rdflib.graph import ConjunctiveGraph
from rdflib.namespace import RDF, RDFS, OWL, XSD
from rdflib.parser import Parser
from rdflib.serializer import Serializer

# Set your default sitemap URL here
SITEMAP_URL = 'http://laurentian.concat.ca/osul_sitemap1.xml'
SITEMAP_URL = 'http://laurentian.concat.ca/osul_sitemapindex.xml'
SITEMAP_URL = 'http://find.senatehouselibrary.ac.uk/sitemapIndex.xml'

# It would be rude to repeatedly retrieve megabytes of sitemaps from a
# third-party site just for testing purposes.
# If true, skip parsing the sitemaps entirely and just use the sample URLs
SHORT_CIRCUIT = True
SAMPLE_URLS = [
    u'http://find.senatehouselibrary.ac.uk/Record/.b24804241',
    u'http://acorn.biblio.org/eg/opac/record/1826746'
]

logging.basicConfig()

def url_value(url):
    "Get the URL value from a given <loc> element"
    locs = url.getElementsByTagName('loc')
    if len(locs) > 1:
        raise Exception('More than 1 loc in url %s' % url.nodeValue)
    if len(locs) < 1:
        raise Exception('No loc in url %s' % url.nodeValue)
    for node in locs[0].childNodes:
        if node.nodeType == node.TEXT_NODE:
            return node.nodeValue

def parse_sitemap_urls(sitemap):
    "Parse the URLs from a sitemap file"
    rv = []
    sitemap = urlopen(sitemap)

    if sitemap.getcode() < 400:
        doc = parse(sitemap)
        for url in doc.getElementsByTagName('url'):
            rv.append(url_value(url))
    return rv

def parse_sitemap_sitemaps(url):
    "Parse the list of linked sitemaps from a sitemap file"
    sitemaps = []
    url = urlopen(url)
    doc = parse(url)
    for sitemap in doc.getElementsByTagName('sitemap'):
        sitemaps.append(url_value(sitemap))
    return sitemaps

def parse_sitemap(url):
    "Parse a sitemap file, including linked sitemaps"
    urls = []
    sitemaps = parse_sitemap_sitemaps(url)
    if sitemaps:
        for sitemap in sitemaps:
            urls += parse_sitemap_urls(sitemap)
    else:
        urls += parse_sitemap_urls(url)
    return(urls)

def extract_rdfa(url, outfile=sys.stdout, parser="rdfa", serializer="n3"):
    """
    Extract RDFa from a given URL

    Parsers are listed at https://rdflib.readthedocs.org/en/4.1.0/plugin_parsers.html
    Serializers are listed at https://rdflib.readthedocs.org/en/4.1.0/plugin_serializers.html
    """
    store = None
    graph = ConjunctiveGraph()
    graph.parse(url, format=parser)
    graph.serialize(destination=outfile, format=serializer)

def main():
    import argparse
    import pprint
    import traceback

    parser = argparse.ArgumentParser(
        description="Crawl a sitemap.xml and extract RDFa from the documents")
    parser.add_argument('-s', '--sitemap', default=SITEMAP_URL,
        help='Location of the sitemap to parse')
    parser.add_argument('-o', '--output', required=True,
        help='Path / filename for the output')
    parser.add_argument('-p', '--parser', default='rdfa1.1',
        help='Parser to use for the input format ("rdfa", "microdata", etc)')
    parser.add_argument('-t', '--serializer', default='n3',
        help='Serializer to use for the output format ("n3", "nt", "turtle", "xml", etc)')
    args = parser.parse_args()

    errors = []
    urls = []
    outfile = open(args.output, 'wb')

    if SHORT_CIRCUIT:
        urls = SAMPLE_URLS
    else:
        urls = parse_sitemap(args.sitemap)
    for url in urls:
        try:
            extract_rdfa(url, outfile, args.parser, args.serializer)
        except Exception as e:
            traceback.print_exc()

if __name__ == '__main__':
    main()
