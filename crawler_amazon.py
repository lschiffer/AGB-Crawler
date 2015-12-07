"""crawler for amazon app store
"""

import sqlite3
import urllib.request
import re

amazon_url = "http://www.amazon.de/mobile-apps/b?node=1661648031"

def getPermissions(html):
    """
    @param html: the html file as string object
    @return: list with apps permissions (as string)
    """
    pat = re.compile('<li><span class=\"a-list-item\">\n[\t|\s]*([^<\n\r]+)\n')
    return (list(set(pat.findall(html))) )

def getPP(html):
    """
    @param html: the html file as string object
    @return: list with url to privacy policy (or empty list)
    """
    pat = re.compile('<a .*href=\".*location=([^"]+)\&token.*\".*[\n].*Datenschutz')
    return (pat.findall(html))

def getAppTitle(html):
    """
    @param html: the html file as string Object
    @return: string with apps title (caption of amazon page)
    """
    pat = re.compile('<span id=\"btAsinTitle\">[\s]+<span style=\"padding-left: 0\">[\s]+([^\n]+)')
    return (pat.findall(html))

def crawl(database = "amazon.db", maxVisits = 1000, maxApps = 1000):
    """crawl amazon store, save visited links as well as links to app products and write to sqlite database
    @param database: name of the target database where the results will be stored
    @param maxVisits: maximum number of sites to visited
    @param maxApps: maximum number of apps to use
    """
    # regex expression to filter links from html string
    pat = re.compile('<a href=\"([^#][^"]+)\"')
    # list to store links
    links = [amazon_url]
    # list to store links to app products
    appLinks = []
    # list to store visited links
    visited = []

    while (len(visited) < maxVisits and len(appLinks) < maxApps):
        print(links[0])
        try:
            req = urllib.request.Request(links[0], data=None)#, headers={'User-Agent':'Mozilla/5.0'})
            # get html from url and decode it as utf-8
            html = urllib.request.urlopen(req).read().decode("utf-8", "ignore")
        except:
            print("HTML Error")
            visited.extend([links.pop(0)])
            continue

        # remove link from heap and insert it into visited urls
        visited.extend([links.pop(0)])
        # get all unique url references and add amazon domain to each string (if relative reference)
        links.extend( "http://www.amazon.de" + s if (s[0] == "/") else s for s in set(pat.findall(html)))
        # make sure there are no duplicates
        links = list(set(links))
        # remove already visited urls
        links = [s for s in links if (not s in visited)]
        # save links to app pages separate from other links
        appLinks.extend([l for l in links if (l.find("/dp/") != -1 or l.find("/gp/product/") != -1)])
        # all links NOT leading to app products will be candidates for next crawling iteration
        links = ([l for l in links if (not l in appLinks)])

    # remove duplicates
    appLinks = list(set(appLinks))

    # open database connection and create table
    connection = sqlite3.connect(database)
    with connection:
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS ID_pp(ID TEXT UNIQUE, URL TEXT, PERMISSIONS TEXT)")
        print("\nWriting App DB:")
        # if app product has privacy policy, data will be written to database
        for l in appLinks:
            try:
                req = urllib.request.Request(l, data=None, headers={'User-Agent':'Mozilla/5.0'})
                html = urllib.request.urlopen(req).read().decode("utf-8", "ignore")
            except:
                print("HTML ERROR")
                continue
            # get app title and privacy policy links (if empty move on to next app)
            title = getAppTitle(html)
            pp = getPP(html)
            if (len(pp) == 0):
                continue
            print(title, "\t", pp)
            try:
                cursor.execute("INSERT INTO ID_pp (ID, URL, PERMISSIONS) VALUES(?, ?, ?)", (title[0], pp[0], "\t".join(getPermissions(html))))
            except:
                print("already in DB")
