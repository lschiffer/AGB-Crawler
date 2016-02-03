'''
Created on Dez 01, 2015

:author: Janos Borst

This is a crawler for the links to Privacy Agreements in GooglePlay store.
It is specialised in finding only German Agreements.
Because of high precision requirements it stops crawling the current app as soon as any possible source of error is detected, then proceeds with the next app.
'''

from bs4 import BeautifulSoup
import urllib
import re
import sqlite3
import time
from pyvirtualdisplay import Display
from selenium import webdriver #used javascript like redirection of pages
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import sys

#
#Macroscopic Variables
#======================
#

#Establish Database Connection
database = sqlite3.connect('GooglePlay.db')
conn  = database.cursor()

#List all the possible categories
categories = ['ENTERTAINMENT', 'BOOKS_AND_REFERENCE', 'BUSINESS', 'COMICS', 'COMMUNICATION', 'EDUCATION',  'FINANCE', 'HEALTH_AND_FITNESS', 'LIBRARIES_AND_DEMO', 'LIFESTYLE', 'APP_WALLPAPER', 'MEDIA_AND_VIDEO', 'MEDICAL', 'MUSIC_AND_AUDIO', 'NEWS_AND_MAGAZINES', 'PERSONALIZATION', 'PHOTOGRAPHY', 'PRODUCTIVITY', 'SHOPPING', 'SOCIAL', 'SPORTS', 'TOOLS', 'TRANSPORTATION', 'TRAVEL_AND_LOCAL', 'WEATHER', 'ARCADE', 'BRAIN', 'CARDS', 'CASUAL', 'GAME_WALLPAPER', 'RACING', 'SPORTS_GAMES', 'GAME_WIDGETS']
app_types = ['free', 'paid']

#Anchorsfor Linkdetection
agbAnchors = [ 'Datenschutzerkl??rung' , 'Datenschutz'  ] 

#Baseurl of Playstore
baseurl = 'https://play.google.com'

#
#Function Definitions
#=====================
#'





import requests
def getPermissions(ids):
    '''
    Retrieve App permissions
    
    :param ids: App-ID
    :type ids: string
    
    :return: Comma seperated list of permissions
    
    
    '''
    payload ={'ids' : ids, 'xhr' : '1'}
    r = requests.post("https://play.google.com/store/xhr/getdoc?authuser=0",data=payload)
    content = r.text
    pattern  ='\[\[\"(?P<permission>.{0,50})\",\"Erm'
    result = re.findall(pattern,content)
    if result:
        print("Permissions found.")
        for perm in set(result): 

            sys.stdout.buffer.write(perm.encode('utf-8'))
        return ",".join(set(result));
    else:
        print("No permissions found")
        return ""


#
#Calling the crawler
#===================
#
if __name__ == '__main__':
    conn.execute("Select id from agb_links")
    id_list = conn.fetchall()


    for row in id_list:
        print(row[0])
        permissions = getPermissions(row[0])
        update_cm=u"Update agb_links SET permissions='"+permissions+u"' WHERE id = '"+row[0]+u"';"
        conn.execute(update_cm)
        database.commit()
