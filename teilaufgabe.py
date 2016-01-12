"""Aufgabe
- Anfang erkennen und alles davor wegschneiden
- Vorkommen von bestimmten Stichworten überprüfen für die
Qualitätsprüfung (soll Boolean zurückgeben)
- Spracherkennung
"""
import sqlite3
from langdetect import detect

def languagedetect(xml):
    """Check if there are curly braces inside given xml-string

    @param xml: xml string to check
    @type xml: string
    @return: string like en/de
    """
    String s =detect(xml-string)
    return s 

def erkennenDSE(xml):
 """Check if there are curly braces inside given xml-string

    @param xml: xml string to check
    @type xml: string
    @return: true of false
    """
    n = -1   
    e=False 
    var1 = xml.find("Datenschutz")
    var2 = xml.find("Allgemeine Geschäftsbedingungen")
    var3 = xml.find("Privacy")
    var4 = xml.find("DSE")
    var5 = xml.find("AGB")
    var6 = xml.find("DATENSCHUTZ")
    var7 = xml.find("PRIVACY")

    if var1 > n: 
        e=True 
    elif var2 > n:  
        e=True 
    elif var3 > n:  
        e=True 
    elif var4 > n:  
        e=True  
    elif var5 > n:  
        e=True  
    elif var6 > n:  
        e=True  
    elif var7 > n:  
        e=True  
    return e

def minimum(liste):


    min = liste[0]
    i = 1
    while i < len(liste):
        if liste[i] < min:
            min = liste[i] 
        i = i + 1

    return min

def Cutting(xml):
 """Check if there are curly braces inside given xml-string

    @param xml: xml string to check
    @type xml: string
    @return: true of false
    """
    ausgang=xml    
    anfang=-1
    ende=-1
    gefunden=-1
    e=0
    while (e<1):
        anfang = xml.find("<title>")
        #print(anfang)
        ende = xml.find("</title>")
        #print(ende)
        gefunden1 = xml.find("Datenschutz")
        if gefunden1 == -1: 
            gefunden1=1000000000000
        gefunden2 = xml.find("DATENSCHUTZ")
        if gefunden2 == -1: 
            gefunden2=1000000000000
        gefunden3 = xml.find("Allgemeine Geschäftsbedingungen")
        if gefunden3 == -1: 
            gefunden3=1000000000000
        gefunden4 = xml.find("Privacy")
        if gefunden4 == -1: 
            gefunden4=1000000000000
        gefunden5 = xml.find("DSE")
        if gefunden5 == -1: 
            gefunden5=1000000000000
        gefunden6 = xml.find("AGB")
        if gefunden6 == -1: 
            gefunden6=1000000000000
        gefunden7 = xml.find("PRIVACY")
        if gefunden7 == -1: 
            gefunden7=1000000000000
        gefunden= minimum([gefunden1, gefunden2, gefunden3, gefunden4, gefunden5, gefunden6; gefunden7])
        #print(gefunden)
        if len(xml)<2000: 
            break
        if gefunden<ende:
            if gefunden>anfang:
                ergebnis= xml[anfang:]
                e=1
                break        
        elif gefunden>ende:
            if gefunden>len(xml):
                ergebnis=ausgang;
                break
            xml= xml[(ende+8):]
            #print(e)
        elif gefunden<anfang:
            xml= xml[anfang:]
            #print(e)

  
    text ='<?xml version="1.0" encoding="utf-8"?>\n<dse>\n <para>\n  '
    endergebnis=text+ergebnis
    return endergebnis

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
    


