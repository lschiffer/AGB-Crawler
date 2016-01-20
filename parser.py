#!/usr/bin/python

import sys
import os.path
import logging

import sqlite3 as lite

from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from socket import timeout

from bs4 import BeautifulSoup
from bs4 import Tag, NavigableString

from datetime import datetime

from optparse import OptionParser

import re

import multiprocessing as mp
from queue import Queue
import asyncio

import check_trim
import checkJS


def process_table(input_file, output_file, crawler_name, store_name):
    '''
    Processes all urls in a stated input file and writes the parsed
    privacy policies into an output file.

    :param input_file: path to the sqlite database containing the app ids, urls
    and app permissions (optional), each in one column from left to right
    :type input_file: string
    :param output_file: path to the desired output sqlite database
    :type output_file: string
    :param crawler_name: name of the url crawler
    :type crawler_name: string
    :param store_name: name of the app store
    :type store_name: string
    :return: returns nothing

    '''

    logger = logging.getLogger()

    if(not os.path.isfile(output_file)):
        new_database(output_file)

    input_con = lite.connect(input_file)
    output_con = lite.connect(output_file)

    with input_con:

        cursor = input_con.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY Name")
        table = cursor.fetchone()
        table_name = table[0]

        cursor.execute("SELECT * FROM {table}".format(table=table_name))

        while True:

            try:

                row = cursor.fetchone()

                if row == None:
                    break

                app_id = row[0]
                url = row[1]
                permissions = row[2]

                (page, xml, empty_text_count) = parse_url(url)
                logger.debug(str(xml) + "\n\n\n")

                with output_con:

                    output_cursor =  output_con.cursor()

                    output_cursor.execute(\
                    "INSERT OR IGNORE INTO AGB (app_id,text_url) VALUES ('{id}','{text_url}')".\
                    format(id=app_id, text_url=url))

                    output_cursor.execute("UPDATE AGB SET text_crawldate=('{date}') WHERE app_id='{id}'".\
                    format(id=app_id, date=datetime.isoformat(datetime.now())))

                    if(permissions):
                        output_cursor.execute("UPDATE AGB SET app_permissions=('{perm}') WHERE app_id='{id}'".\
                        format(id=app_id, perm=permissions))

                    output_cursor.execute("UPDATE AGB SET crawler_name=('{crawler}') WHERE app_id='{id}'".\
                    format(id=app_id, crawler=crawler_name))

                    output_cursor.execute("UPDATE AGB SET app_storename=('{store}') WHERE app_id='{id}'".\
                    format(id=app_id, store=store_name))

                    output_cursor.execute("UPDATE AGB SET text_raw=('{raw}') WHERE app_id='{id}'".\
                    format(id=app_id, raw=page.replace("'", "''")))

                    output_cursor.execute("UPDATE AGB SET text_xml=('{text_xml}') WHERE app_id='{id}'".\
                    format(id=app_id, text_xml=xml.replace("'", "''")))

                    output_cursor.execute("UPDATE AGB SET empty_text_count=('{count}') WHERE app_id='{id}'".\
                    format(id=app_id, count=empty_text_count))

                    # call auto check functions and trimming

                    if(xml):

                        lang = check_trim.language_detect(xml)

                        trimmed= ''

                        #result_queue = mp.Queue()

                        #p = mp.Process(target=teilaufgabe.cutting,
                        #name="Cutting", args=(result_queue, xml,))
                        #p.start()
                        #p.join(3)


                        ## terminate trimming function if timeout
                        #if p.is_alive():
                        #    logger.debug("trimming function timeout")
                        #    p.terminate()
                        #    p.join()

                        #if(not result_queue.empty()):
                        #    try:
                        #        trimmed = result_queue.get_nowait()
                        #    except (asyncio.QueueEmpty):
                        #        print("Queue empty?")
                        #        continue
                        #else:
                        #    print("Queue empty!")

                        trimmed = check_trim.cutting(xml)

                        contains_keywords = check_trim.check_keywords(xml)

                        contains_javascript = checkJS.checkJS(xml)

                        output_cursor.execute("UPDATE AGB SET language=('{language}') WHERE app_id='{id}'".\
                        format(id=app_id, language=lang))

                        output_cursor.execute("UPDATE AGB SET text_xml=('{text_xml_trimmed}') WHERE app_id='{id}'".\
                        format(id=app_id, text_xml_trimmed=trimmed.replace("'", "''")))

                        output_cursor.execute("UPDATE AGB SET contains_keywords=('{contains}') WHERE app_id='{id}'".\
                        format(id=app_id, contains=contains_keywords))

                        output_cursor.execute("UPDATE AGB SET contains_js=('{contains}') WHERE app_id='{id}'".\
                        format(id=app_id, contains=contains_javascript))

            except Exception as e:
                logger.warning("error " + str(e) + " at url " + url)


def new_database(output_file):
    '''
    Creates a new sqlite database with all necessary columns.

    :param output_file: path to the sqlite database
    :type output_file: string
    :return: returns nothing

    '''

    output_con = lite.connect(output_file)

    with output_con:

       cur =  output_con.cursor()
       cur.execute('''DROP TABLE IF EXISTS AGB''')
       cur.execute('''CREATE TABLE AGB(app_id TEXT PRIMARY KEY,
       text_url TEXT, text_raw TEXT, text_xml TEXT,
       language TEXT, text_quality INTEGER, check_man BOOL,
       duplicate BOOL, contains_keywords BOOL, contains_js BOOL,
       empty_text_count INTEGER, app_storename TEXT,
       crawler_name TEXT, app_permissions TEXT, text_crawldate TEXT, comment TEXT)''')


def parse_url(url):
    '''
    Parses the privacy policy at the given url.
    Only websites with utf-8 enconding are accepted.
    After the fetch of the website, in a preprocessing step all tags
    probably not containing content of the privacy policy are removed.
    A split on all headings (h3, h2, h1, strong) is performed to section
    the policy into paragraphs.

    :param url: url of a website containing a privacy policy
    :type url: string
    :return: tuple of the raw html and the parsed xml of the website
    :rtype: tuple(string, string)

    '''

    logger = logging.getLogger()

    empty_text_count = 0

    try:

        # fetch html from given url
        page = ''
        response = ''

        try:
            response = urlopen(url, timeout = 5)

        except (HTTPError, URLError) as error:
            logger.warning("error " + str(error) + " at url " + url)
        else:
            logger.info("opening " + url)

        if(not response):
            return ('','', empty_text_count)

        page = response.read()
        page = page.decode("utf-8")

        # get body of the website as  soup
        html_soup = BeautifulSoup(page, "lxml")
        soup = html_soup.find('body')

        # remove tags which are unlikely to contain relevant text
        soup = remove_unwanted_tags(soup)

        # create xml output
        xml_output = "<dse>"

        # split on headings and get text of all siblings of a heading
        headings = soup.findAll(['h3', 'h2', 'h1', 'strong'])


        for heading in headings:

            text_output = ''

            sibling = heading.next_sibling

            while sibling and sibling.name not in ['h3', 'h2', 'h1', 'strong']:

                if isinstance(sibling, Tag):
                    text_output += sibling.get_text()

                sibling = sibling.next_sibling

            # consider only text with at least 10 characters
            # else heading and following text are skipped
            if(len(text_output) > 10):

                text_output = text_output.replace('<', '(')
                text_output = text_output.replace('>', ')')

                xml_output += "<para>"
                xml_output += "<title>"
                xml_output += heading.get_text()
                xml_output += "</title>"
                xml_output += "<text>"
                xml_output += text_output
                xml_output += "</text>"
                xml_output += "</para>"

            else:

                empty_text_count += 1

        xml_output += "</dse>"

        xml_output = ' '.join(xml_output.split())
        xml_output = xml_output.replace('\n', ' ')

        xml_soup = BeautifulSoup(xml_output, "lxml-xml")

        # consider only privacy policies with at least 100 characters
        if(len(xml_soup.prettify()) < 100):
            return(soup.prettify(), '', empty_text_count)

        return (html_soup.prettify(), xml_soup.prettify(), empty_text_count)

    except Exception as e:
        logger.warning("error " + str(e) + " at url " + url)
        return ('', '', empty_text_count)


def remove_unwanted_tags(soup):
    '''
    Removes unwanted tags from the given soup, that are unlikely to contain
    contents of the privacy policy. That is achieved by removing specific
    tags and tags with specific class names, id names or text.

    :param soup: soup of the website containing a privacy policy
    :type soup: soup
    :return: returns nothing

    '''

    # remove all unwanted tags
    tags = ["script", "noscript", "link", "comment()", "form", "header", "footer",
    "head", "foot", "nav", "style", "img", "input", "label",
    "select", "meta"]

    remove_tags  = soup.find_all(tags)
    for tag in remove_tags:
        tag.extract()

    # remove tags containing specific text
    contains_phrase = soup.find_all(text=re.compile(r"back to top"))
    contains_phrase += soup.find_all(text=re.compile(r"view full policy"))
    for tag in contains_phrase:
        tag.extract()

    # do not remove elements with these id or class names,
    # since they usually accompany relevant content
    # e.g. <div class ="main content with_sidebar">
    keywords_whitelist = [
        "with_sidebar", "withsidebar", "has_sidebar", "hassidebar",
        "with_sidemenu", "withsidemenu", "has_sidemenu", "hassidemenu",
        "with_side_menu", "withside_menu", "has_side_menu", "hasside_menu",
        "with_menu", "withmenu", "has_menu", "hasmenu"
    ]

    # remove all tags with  class/id containing at least one of these keywords
    keywords = [
        # Header and Banner
        "header", "header_banner", "topbar", "heading",
        # Footer
        "footer", "footer_banner", "impressum", "bottombar",
        # Sidebar
        # do not use "sidebar"! often main-div class "with_sidebar" or "hassidebar"
        # do not use "side". could also be "inside"
        "side_menu",
        # Banner
        "banner_top", "top_banner", "banner_bottom", "bottom_banner", "side_banner",
        "banner_side", "banner",
        # Menu
        # do not use "menu"!
        "logo", "main_menu", "sub_menu", "menubar", "menu_top", "menu_bottom",
        "navbar", "navigator", "navigation", "mobileNav", "desktopNav", "backNav", "nav",
        "breadcrumbs", "pagination", "tabber", "tabs",
        # Social Media
        "facebook", "twitter", "social", "mailinglist", "instagram", "follow", "news", "rss",
        "subscribe",
        # Download and Form and versions
        "email_form", "download_form", "versions", "language_select", "select", "download", "form",
        # table of content
        "toc", "tableofcontent", "table_of_content",
        # adverds
        "advertisement", "advert", "ads", "promo", "popup", "dialog",
        # misc
        "slideshow", "horizontal_line", "line", "language", "button", "support",
        "help", "cookie", "comment", "copyright", "aftercontent", "tags", "related",
        "tag-cloud", "authorbox", "recent-post", "entry-meta", "meta",

        # very specific and maybe wrong
        "boxes", "tabset", "feature", "xcap_title", "bottom"
    ]

    # remove tags by inspecting their id and class names
    unwanted = soup.find_all(class_=(lambda x: x in keywords))
    unwanted += soup.find_all(id=(lambda x: x in keywords))
    for tag in unwanted:
        if(x not in tag.contents for x in keywords_whitelist):
            tag.extract()

    # remove tags containing "menu" or "sidebar" only,
    # if their length does not exceed a specified character limit
    with_menu = soup.find_all(class_='menu')
    with_menu += soup.find_all(id='menu')
    for tag in with_menu:
        if(len(tag.get_text()) < 30):
            tag.extract()

    with_sidebar = soup.find_all(class_='sidebar')
    with_sidebar += soup.find_all(id='sidebar')
    for tag in with_sidebar:
        if(len(tag.get_text()) < 300):
            tag.extract()

    return soup


def main():
    '''
    Reads parameters from the command line.
    For information on  usage run parser with parameter --help.

    '''

    # parse command line options
    parser = OptionParser()

    parser.add_option("-i", "--input", dest="input_files", default=[], metavar="INPUT_FILE", action="append",\
    help="read App-IDs and URLs from sqlite3 database stored in INPUT_FILE (multiple input files possible)")

    parser.add_option("-o", "--output", dest="output_file", default="output.sqlite", metavar="OUTPUT_FILE",\
    help="write output as sqlite3 database into OUTPUT_FILE (default: output.sqlite)")

    parser.add_option("-c", "--crawler", dest="crawler_names", default=[],metavar="CRAWLER", action="append",\
    help="name of the used crawler (multiple names possible)")

    parser.add_option("-s", "--store", dest="store_names", default=[], metavar="STORE", action="append",\
    help="name of the crawled store (multiple stores possible)")

    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False,\
    help="print no output")

    parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False,\
    help="print parsed xml")

    options, args = parser.parse_args()

    # set logging level according to given options
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if options.quiet:
        logger.setLevel(logging.WARNING)
    if options.debug:
        logger.setLevel(logging.DEBUG)

    # adjust number of optional parameters to number of input files
    input_files = options.input_files
    crawler_names = options.crawler_names
    while len(crawler_names) < len(options.input_files):
        crawler_names.append("")
    store_names = options.store_names
    while len(store_names) < len(options.input_files):
        store_names.append("")

    # process all input files
    for i in range(0, len(input_files)):
            process_table(input_files[i], options.output_file,
            crawler_names[i], store_names[i])

    sys.exit(0)

if __name__ == "__main__":
    main()

