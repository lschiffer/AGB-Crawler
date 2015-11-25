#!/usr/bin/python

import sys

import sqlite3 as lite

from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from socket import timeout

from bs4 import BeautifulSoup
from bs4 import Tag, NavigableString

from datetime import datetime

from optparse import OptionParser


def process_table(input_file, output_file, table_name):

    new_database(output_file)
    input_con = lite.connect(input_file)
    output_con = lite.connect(output_file)

    with input_con:

        cursor = input_con.cursor()
        cursor.execute("SELECT * FROM {table}".format(table=table_name))

        while True:

            row = cursor.fetchone()

            if row == None:
                break

            app_id = row[0]
            url = row[1]

            (page, xml) = parse_url(app_id, url)
            print(xml, "\n\n\n")

            with output_con:

                output_cursor =  output_con.cursor()

                output_cursor.execute("INSERT OR IGNORE INTO AGB (app_id,text_url) VALUES ('{id}','{text_url}')".\
                format(id=app_id, text_url=url))

                output_cursor.execute("UPDATE AGB SET text_crawldate=('{date}') WHERE app_id='{id}'".\
                format(id=app_id, date=datetime.isoformat(datetime.now())))

                output_cursor.execute("UPDATE AGB SET text_raw=('{raw}') WHERE app_id='{id}'".\
                format(id=app_id, raw=escape(page)))

                output_cursor.execute("UPDATE AGB SET text_xml=('{text_xml}') WHERE app_id='{id}'".\
                format(id=app_id, text_xml=escape(xml)))

                #TODO: write into existing database without creating a new one every time


def escape(text):

    return text.replace("'", "''")


def new_database(output_file):

    output_con = lite.connect(output_file)

    with output_con:

       cur =  output_con.cursor()
       cur.execute('''DROP TABLE IF EXISTS AGB''')
       cur.execute('''CREATE TABLE AGB(app_id TEXT PRIMARY KEY, text_url
       TEXT, text_raw TEXT, text_xml TEXT, crawler_name TEXT, text_type
       TEXT, text_crawldate TEXT, check_auto BOOL, check_man BOOL,
       text_quality INTEGER, app_name TEXT, app_storename TEXT,
       app_permissions TEXT)''')


def parse_url(app_id, url):

    try:

        page = ''

        # TODO: test exception handling

        try:
            page = urlopen(url, timeout = 5)

        except (HTTPError, URLError) as error:
            print("error", error, "at url", url)
        else:
            print("opening", url)

        if page == '':
            return ('','')

        soup = BeautifulSoup(page, "lxml")
        xml_output = "<dse>"

        headings = soup.find_all('h3')

        for heading in headings:

            xml_output += "<para>"

            xml_output += "<title>"
            xml_output += heading.get_text()
            xml_output += "</title>"
            xml_output += "<text>"

            sibling = heading.next_sibling

            while sibling.name != 'h3':

                if isinstance(sibling, Tag):
                    xml_output += sibling.get_text()

                sibling = sibling.next_sibling

                if sibling is None:
                    break

            xml_output += "</text>"
            xml_output += "</para>"

        xml_output += "</dse>"

        xml_output = ' '.join(xml_output.split())
        xml_output = xml_output.replace('\n', ' ')

        xml_soup = BeautifulSoup(xml_output, "lxml-xml")

        return (soup.prettify(), xml_soup.prettify())

    except:

        return ('', '')


def main():

    parser = OptionParser()
    parser.add_option("-i", "--input", dest="input_file", default="input.sqlite", metavar="INPUT_FILE",
            help="read App-IDs and URLs from sqlite3 database stored in INPUT_FILE (default: input.sqlite)")
    parser.add_option("-t", "--table", dest="table_name", default="URLs", metavar="TABLE_NAME",
            help="name of the relevant table in INPUT_FILE (default: URLs)")
    parser.add_option("-o", "--output", dest="output_file", default="output.sqlite", metavar="OUTPUT_VAR",
            help="write output as sqlite3 database into OUTPUT_FILE (default: output.sqlite)")
    options, args = parser.parse_args()

    process_table(options.input_file, options.output_file, options.table_name)

    sys.exit(0)

if __name__ == "__main__":
    main()

