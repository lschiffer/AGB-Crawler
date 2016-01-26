"""Aufgabe
- Anfang erkennen und alles davor wegschneiden
- Vorkommen von bestimmten Stichworten überprüfen für die
Qualitätsprüfung (soll Boolean zurückgeben)
- Spracherkennung
"""
import sqlite3
from langdetect import detect

#from multiprocessing import Queue

def language_detect(xml):
    """Check if there are curly braces inside given xml-string

    @param xml: xml string to check
    @type xml: string
    @return: string like en/de
    """
    s = detect(xml)
    return s

def check_keywords(xml):
    """Check if there are curly braces inside given xml-string

    @param xml: xml string to check
    @type xml: string
    @return: true of false
    """

    xml = xml.lower()
    keywords = ["datenschutz", "allgemeine geschäftsbedingungen", "privacy", "dse", "agb"]
    return (any(x in xml for x in keywords))
    
def cutting(xml):
    """Check if there are curly braces inside given xml-string

    @param xml: xml string to check
    @type xml: string
    @return: true of false
    """
    #Anfangsvariablen setzen
    raw_text=xml
    xml_lower=xml.lower()
    begin=-1
    end=-1
    first_word_found=-1
    text ='<?xml version="1.0" encoding="utf-8"?>\n<dse>\n <para>\n  '
    final_result=raw_text
    keywords = ["datenschutz", "allgemeine geschäftsbedingungen", "privacy", "dse", "agb"]

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
       

        #Der Text soll mind noch 2000 Wörter haben, wenn weniger soll nicht gekürzt werden
        if len(xml)<2000:
            final_result=raw_text
            break

        #Wenn das gefundene Wort zwischen den title steht, dann kürze alles vor dem title weg und nimm den rest als result
        if first_word_found<end:
            if first_word_found>begin:
                result= xml[begin:]
                final_result=text+result
                #print(final_result)
                break

        #Wenn das gefundene Wort hinter dem title steht gibt es 2 Varianten: Die erste ist es steht noch vor dem Ende des Textes, dann wird alles incl der 2 title rausgekürzt
        #Die zweite es steht außerhalb des textes, was dadurch passieren kann weil oben alle nicht gefundenen Wörter auf len+1 gesetzt wurden, dann soll es abbrechen, dann gibt es keines der Wörter weiter im Text
        if first_word_found>end:
            if first_word_found>len(xml):
                final_result=raw_text
                break
            xml= xml[(end+8):]
            xml_lower= xml[(end+8):]

        #Wenn das Wort in einem text vor dem title steht wird dieser text weggekürzt
        if first_word_found<begin:
            #xml= xml[begin:]
            final_result = raw_text
            break

        if begin == -1:
            if end ==-1:
                final_result=raw_text
                break

    #queue.put(final_result)
    return final_result

def main(database = "parsed_all.db"):
    """main
    @param database: name of the database to use
    @type database: string
    """

    Y = "War doesn't show who's right, just who's left."
    language = languagedetect(Y); print(language)

    fin = open("dse6.xml","r")
    dateiinhalt = fin.read()
    print(erkennenDSE(dateiinhalt))
    print(Cutting(dateiinhalt))



