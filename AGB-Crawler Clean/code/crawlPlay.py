"""
Created on Dez 01, 2015

:author: Janos Borst

This is a crawler for the links to Privacy Agreements in GooglePlay store.
It is specialised in finding only German Agreements.
Because of high precision requirements it stops crawling the current app as soon as any possible source of error is detected, then proceeds with the next app.
"""

from bs4 import BeautifulSoup
import urllib
import re
import os
import sqlite3
import time
from pyvirtualdisplay import Display
from selenium import webdriver #used javascript like redirection of pages
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import sys
from optparse import OptionParser
#
#Macroscopic Variables
#======================
#"""

#Establish Database Connection
global database
global conn

#List all the possible categories
categories = ['ENTERTAINMENT', 'BOOKS_AND_REFERENCE', 'BUSINESS', 'COMICS', 'COMMUNICATION', 'EDUCATION',  'FINANCE', 'HEALTH_AND_FITNESS', 'LIBRARIES_AND_DEMO', 'LIFESTYLE', 'APP_WALLPAPER', 'MEDIA_AND_VIDEO', 'MEDICAL', 'MUSIC_AND_AUDIO', 'NEWS_AND_MAGAZINES', 'PERSONALIZATION', 'PHOTOGRAPHY', 'PRODUCTIVITY', 'SHOPPING', 'SOCIAL', 'SPORTS', 'TOOLS', 'TRANSPORTATION', 'TRAVEL_AND_LOCAL', 'WEATHER', 'ARCADE', 'BRAIN', 'CARDS', 'CASUAL', 'GAME_WALLPAPER', 'RACING', 'SPORTS_GAMES', 'GAME_WIDGETS']
app_types = ['free', 'paid']

#Anchorsfor Linkdetection
agbAnchors = [ 'Datenschutz'  ] 

#Baseurl of Playstore
baseurl = 'https://play.google.com'

#
#Function Definitions
#=====================
#'


def get_redirected_url(url):
    """
    Trying to resolve the URL redirection with respect to the precision
    
    :param url: intial url 
    :type url: string 
    
    :return the url of the final page, if it is a german AGB or Privacy Agreement. Otherwise None.
    """

    soup = getPageAsSoup(url,None)
    redirected_url = url
    
    #if Website not retrieved stop trying
    if not soup:
        return None
    #else if Website is  a redirect get the nre URL

    if soup.find('body') and any(word.lower()  in soup.find('body').get_text().lower() for word in ["Redirect Notice", "Weiterleitungshinweis"]):
        #print( soup.find('body').get_text())
        #print("There was a redirection")
        redirected_url = soup.find('body').findAll('a')[0].get('href')


    #Now see if theres a german language link on the Page
    display = Display(visible=0, size=(800, 600))
    display.start()
    driver = webdriver.Firefox()
    try:
        driver.set_page_load_timeout(10)
        driver.get(redirected_url)

    except:
        pass
    
    foundGermanLink = 0
    try:
        link = driver.find_element_by_partial_link_text('Deutsch')
        link.click()
        redirected_url = driver.current_url
        foundGermanLink = 1
    except:
        print ( "No German Link" )
        pass
    
    if foundGermanLink == 0:
        try:
            link = driver.find_element_by_partial_link_text('Datenschutz')
            link.click()
            redirected_url = driver.current_url
        except:
            print ( "No Datenschutz Link" )
            pass
        
    driver.quit()
    display.stop()
    
    #now get the source of the latest linkage
    soup = getPageAsSoup(redirected_url,None);
    if not soup:
        return None
    print(redirected_url)
    #Now check if the Words are present  
    #print(soup.get_text())
    if any( word.lower() in soup.get_text().lower() for word in ["Datenschutz" , "Datenschutzerkl??rung" , "Datenschutzbestimmung","AGB"]):
        return redirected_url
    #driver.close()
    return None



character_encoding = 'utf-8'



def getPageAsSoup( url, post_values):
    
    """
    Retrieving the sourcecode for the given url and Beautify with Bs4
    
    :param url: the Pages urlencode
    :type url: string
    
    :param post_values: Giving options to the HTML- Request
    :type post_values: Dictionary
    
    :return: the source Code as soup
    :rtype: soup
    """   
    
    print("souping")
    if post_values:
        data = urllib.parse.urlencode(post_values )
        data = data.encode( character_encoding )
        req = urllib.request.Request( url, data , headers = { 'User-Agent' : 'Mozilla/5.0 (de)','Accept-Language' : 'de' } )
    else:
        req = url
    try:
        response = urllib.request.urlopen( req , None, 30)
    except:
        return None
    the_page = response.read()
    soup = BeautifulSoup( the_page , "html.parser" )
    return soup

 
def getApps( url, start, num):
    """
    Get the initial Top Apps from the Category Page
    
    :param url: url of the category page
    :type url: string
    
    :param start: offset 
    :type: string
    
    :param num: Number of Apps to be retrieved
    :type num: int 
    
    :return: List of App - IDs
    :rtype: list
    
    """
    values = {'start' : start,
              'num': num,
              'numChildren':'0',
              'ipf': '1',
              'xhr': '1',
              'lang' : 'de'}
    soup = getPageAsSoup( url, values )
    if not soup: return [], []

    apps = []
    for div in soup.findAll( 'div', {'class' : 'details'} ):
        title = div.find( 'a', {'class':'title'} )
        apps.append(title.get('href'))
    return apps
    









def getAGBLink(pageCode):

    """
    Retrieve the Link to the privacy Agreement from the sourceCode of the App page
    
    :param pageCode: Page source Code as string
    :type pageCode: string
    
    :return: url to the Privacy Agreement
    :rtype: string
    
    """
    
    
    
    #Only links in the Body are useful
    try:
        pageCodeBody = pageCode.split('<title id="main-title">')[1].split('<div class="footer">')[0]
    except:
        print("No Body")
        return None


    if not pageCodeBody:
        print("pageCodeBody empty")
        return None
    
    #print (pageCodeBody)
    for anchor in agbAnchors:
        print (anchor)
        #print (pageCodeBody)
        pattern  ='href="(?P<agb_link>\S{20,200})"[ ]{0,2}\S{0,30}[ ]{0,2}\S{0,30}">'+anchor
        result = re.search(pattern,pageCodeBody)
        if result:
            #resolve redirect
            print(result.group('agb_link'))
            return get_redirected_url(result.group('agb_link'))
        
        else:
            continue
    return None




def getLinks():
    """
    Main Function Loop
    Retrieving all the links to Privacy Agreements for alle the top 100 Apps in every Category 
    Written as function, cann be called from outside.
    Has no return value, because discovered links will be directly written to sqlite3-Database.
    
    
    """
    for category, app_type in [( x, y ) for x in categories for y in app_types]:
        print( "\nType = ", app_type, " Cateory = ", category )
        url = baseurl + '/store/apps/category/' + category + '/collection/topselling_' + app_type
        #print(url)
        appList = getApps( url , 0 , 100 )
        for app in appList:
            print("\n\n")
            
            #check if already tested
            conn.execute("select ID from (select ID from agb_links UNION ALL select ID from noAGB) WHERE ID = ?", (app.replace('/store/apps/details?id=',''),))
            data=conn.fetchone()
            if data is None:
                print('Searching for %s'%app.replace('/store/apps/details?id=',''))
            else  :
                print('Skipping %s'%(app.replace('/store/apps/details?id=','')))
                continue

                        
            #Get the Page Source Code
            req =  baseurl + app + '&hl=de'
            try:
                response = urllib.request.urlopen( req ,None, 1 )
            except:
                print( "HTTPError with: ", url, "\t", e )
                continue
            the_page = response.read()
            the_page = the_page.decode("utf-8")
            
            
            #Get the AGB URL from source Code
            agb_url = ""
            agb_url = getAGBLink(the_page)
            if not agb_url:
                print("No Url found")
                try:
                    conn.execute("INSERT INTO noAGB (ID) VALUES ('"+app.replace('/store/apps/details?id=','')+"');")
                    database.commit()
                except:
                    print("SQL Error...")
                    pass
                continue
            else:
                print(app.replace('/store/apps/details?id=',''),"   ",agb_url)
                permissions = getPermissions(app.replace('/store/apps/details?id=',''))
                try:
                    update_cm=u"INSERT INTO agb_links (ID,url,permissions) VALUES ('"+app.replace('/store/apps/details?id=','')+u"','"+agb_url+u"','" + permissions + u"');"
                    conn.execute(update_cm)
                    database.commit()
                except:
                    pass
                
            break




def getLinksRecursive():
    """
    Main Function Loop
    Retrieving all the links to Privacy Agreements for alle the top 100 Apps in every Category 
    Written as function, cann be called from outside.
    Has no return value, because discovered links will be directly written to sqlite3-Database.
    
    
    """
    for category, app_type in [( x, y ) for x in categories for y in app_types]:
        print( "\nType = ", app_type, " Cateory = ", category )
        url = baseurl + '/store/apps/category/' + category + '/collection/topselling_' + app_type
        #print(url)
        appList = getApps( url , 0 , 100 )
        for app in appList:
            print("\n\n")
            
            #check if already tested
            conn.execute("select ID from (select ID from agb_links UNION ALL select ID from noAGB) WHERE ID = ?", (app.replace('/store/apps/details?id=',''),))
            data=conn.fetchone()
            if data is None:
                print('Searching for %s'%app.replace('/store/apps/details?id=',''))
            else  :
                print('Skipping %s'%(app.replace('/store/apps/details?id=','')))
                continue

                        
            #Get the Page Source Code
            req =  baseurl + app + '&hl=de'
            try:
                response = urllib.request.urlopen( req ,None, 1 )
            except:
                print( "HTTPError with: ", url, "\t", e )
                continue
            the_page = response.read()
            the_page = the_page.decode("utf-8")
            
            
            #Get the AGB URL from source Code
            agb_url = ""
            agb_url = getAGBLink(the_page)
            if not agb_url:
                print("No Url found")
                try:
                    conn.execute("INSERT INTO noAGB (ID) VALUES ('"+app.replace('/store/apps/details?id=','')+"');")
                    database.commit()
                except:
                    print("SQL Error...")
                    pass
                continue
            else:
                print(app.replace('/store/apps/details?id=',''),"   ",agb_url)
                permissions = getPermissions(app.replace('/store/apps/details?id=',''))
                try:
                    update_cm=u"INSERT INTO agb_links (ID,url,permissions) VALUES ('"+app.replace('/store/apps/details?id=','')+u"','"+agb_url+u"','" + permissions + u"');"
                    conn.execute(update_cm)
                    database.commit()
                except:
                    pass
                
            break



import requests
def getPermissions(ids):
    """
    Retrieve App permissions
    :param ids: App-ID
    
    :return : Comma seperated list of permissions
    
    """
    payload ={'ids' : ids, 'xhr' : '1'}
    r = requests.post("https://play.google.com/store/xhr/getdoc?authuser=0",data=payload)

    content = r.text
    pattern  ='\[\[\"(?P<permission>.{0,50})\",\"Erm'   
    result = re.findall(pattern,content)
    if result:
        print("\nPermissions found.")
        for perm in set(result): 
            sys.stdout.buffer.write(perm.encode('utf-8'))
            sys.stdout.buffer.write("\n".encode('utf-8'))
        return ",".join(set(result));
    else:
        print("No permissions found")
        return ""


def new_database(output_file):
    """
    Create a New Database suited for the Duplicates.
    Columns: ID1, ID2, percentage1, percentage2
    
    :param output_file: Name of the sqlite3 database file that will be created
    """

    output_con_tmp = sqlite3.connect(output_file)
    with output_con_tmp:
        cur =  output_con_tmp.cursor()
        cur.execute("""CREATE TABLE agb_links(ID text primary key, url text, permissions text);""")
        cur.execute("""CREATE TABLE noAGB (ID text primary key);""")


    output_con_tmp.close()


"""
Calling the crawler
===================
"""
if __name__ == '__main__':
    
    parser = OptionParser()
    
    parser.add_option("-r","--recursive",dest = "recursive",action = "store_true", help="Start Retrieving Links recursivly, Starting with an existing Database.")
    parser.add_option("-i","--initial",dest = "initial",action = "store_true", help="Crawl initial Sites from the top Categories, can be used as Seeds for the recursive Crawl.")
 
    
    options, args = parser.parse_args()
    
    recursive = options.recursive
    initial = options.initial
    output = "GooglePlay.db"

    if not os.path.exists(output):
        new_database(output)
        
    database = sqlite3.connect('GooglePlay.db')
    conn  = database.cursor()
    
    if recursive and initial:
        print("Only one option allowed.")
        exit()
    
    if recursive:
        print("Do recursive Crawl.")
        getLinksRecursive()

    if initial:
        print("Initial Crawl.")
        getLinks()