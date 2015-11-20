#!/usr/bin/python

import sqlite3 as lite

from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from socket import timeout

from bs4 import BeautifulSoup
from bs4 import Tag, NavigableString

from datetime import datetime


def main():

    new_database()

    input_con = lite.connect('playstore.sqlite')

    output_con = lite.connect('output.sqlite')

    with input_con:

        cursor = input_con.cursor()
        cursor.execute("SELECT * FROM URLs")

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


def new_database():

    output_con = lite.connect('output.sqlite')

    with output_con:

       cur =  output_con.cursor()
       cur.execute('''DROP TABLE IF EXISTS AGB''')
       cur.execute('''CREATE TABLE AGB(app_id TEXT PRIMARY KEY, text_url
       TEXT, text_raw TEXT, text_xml TEXT, crawler_name TEXT, text_type
       TEXT, text_crawldate TEXT, check_auto BOOL, check_man BOOL,
       text_quality INTEGER, app_name TEXT, app_storename TEXT,
       app_permissions TEXT)''')


def parse_url(app_id, url):

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
        xml_output += heading.string
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


main()
