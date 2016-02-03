"""
Created on Feb 01, 2016

:author: Svende Landwehrkamp, Enrico Reich

Contains functions to check textfeatures, like:
Trimming the Text to relevant part,
check the Occurence of keywords
check the language of the text

"""


#imports
import sqlite3
from langdetect import detect
import re

#from multiprocessing import Queue

def language_detect(xml):
    """Check if there are curly braces inside given xml-string

    :param xml: xml string to check
    :type xml: string
    :return: string like en/de
    """
    s = detect(xml)
    return s

def check_keywords(xml):
    """Check if there are curly braces inside given xml-string

    :param xml: xml string to check
    :type xml: string
    :return: true of false
    """

    xml = xml.lower()
    keywords = ["datenschutz", "allgemeine gesch??ftsbedingungen", "privacy", "agb"]
    return (any(x in xml for x in keywords))

def cutting(xml):
    """Check if there are curly braces inside given xml-string

    :param xml: xml string to check
    :type xml: string
    :return: true of false
    """
    #Anfangsvariablen setzen
    raw_text=xml
    xml_lower=xml.lower()
    begin=-1
    end=-1
    first_word_found=-1
    text ='<?xml version="1.0" encoding="utf-8"?>\n<dse>\n <para>\n  '
    final_result=raw_text
    keywords = ["datenschutz", "allgemeine gesch??ftsbedingungen", "privacy", "agb"]

    while True:
        indizes=[]
        begin = xml.find("<title>")
        end = xml.find("</title>")
        for i in keywords:
            a= xml_lower.find(i)
            if a == -1:
                indizes += [float('inf')]
            else:
                indizes += [a]

        first_word_found=min(indizes)


        #Only check xml with more than 2000 characters
        if len(xml)<2000:
            final_result=raw_text
            break

        #If the found word occurs in title tag, everything before <title> can be omitted
        if first_word_found<end:
            if first_word_found>begin:
                result= xml[begin:]
                final_result=text+result
                break

        #If the word is found after the first title-tag: there are two options:
        #   1:  if it occurs before the end of the paragraph, then everything, the title-tags included, will be omitted
        #   2:  If it occurs not inside the text, then the algorithm will exit, because no further word in the text can be found.
        if first_word_found>end:
            if first_word_found>len(xml):
                final_result=raw_text
                break
            xml= xml[(end+8):]
            xml_lower= xml[(end+8):]

        #If the Word is foudn before a title-tag, that paragraph will be omitted.
        if first_word_found<begin:
            final_result = raw_text
            break

        if begin == -1:
            if end ==-1:
                final_result=raw_text
                break
    return final_result


def checkJS(xml):
    """Check if there are curly braces inside given xml-string

    :param xml: xml string to check
    :type xml: string
    :return: true if there is a pair of curly braces
    """
    pat = re.compile('{.*}', re.DOTALL)
    return (len(pat.findall(xml)) > 0)


def main(database = "parsed_all.db"):
    """main
    :param database: name of the database to use
    :type database: string
    """


    fin = open("dse6.xml","r")
    dateiinhalt = fin.read()
    print(erkennenDSE(dateiinhalt))
    print(Cutting(dateiinhalt))



