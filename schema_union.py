#!/usr/bin/env python
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

SITEMAP_URL = 'http://laurentian.concat.ca/osul_sitemap1.xml'
SITEMAP_URL = 'http://laurentian.concat.ca/osul_sitemapindex.xml'
SITEMAP_URL = 'http://find.senatehouselibrary.ac.uk/sitemapIndex.xml'

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
    outfile = open(args.output, 'wb')
    # urls = parse_sitemap(args.sitemap)
    # urls = [u'http://laurentian.concat.ca/eg/opac/record/146655?locg=105']
    urls = [u'http://find.senatehouselibrary.ac.uk/Record/.b24804241']
    for url in urls:
        try:
            extract_rdfa(url, outfile, args.parser, args.serializer)
        except Exception as e:
            traceback.print_exc()

if __name__ == '__main__':
    main()
