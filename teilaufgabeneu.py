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
    #Anfangsvariablen setzen
    ausgang=xml    
    anfang=-1
    ende=-1
    gefunden=-1
    text ='<?xml version="1.0" encoding="utf-8"?>\n<dse>\n <para>\n  '
    endergebnis=ausgang

    while True:
        #Suche das Erste Wort title
        anfang = xml.find("<title>")
        #print(anfang)
        #Suche das 2te Wort title
        ende = xml.find("</title>")
        #print(ende)
        #Suche nach den Woertern und wenn nicht im Text setze sie auf die Länge des Textes plus 1 (also hinter den Text sozusagen)
        gefunden1 = xml.find("Datenschutz")
        if gefunden1 == -1: 
            gefunden1=len(xml+1)
        gefunden2 = xml.find("DATENSCHUTZ")
        if gefunden2 == -1: 
            gefunden2=len(xml+1)
        gefunden3 = xml.find("Allgemeine Geschäftsbedingungen")
        if gefunden3 == -1: 
            gefunden3=len(xml+1)
        gefunden4 = xml.find("Privacy")
        if gefunden4 == -1: 
            gefunden4=len(xml+1)
        gefunden5 = xml.find("DSE")
        if gefunden5 == -1: 
            gefunden5=len(xml+1)
        gefunden6 = xml.find("AGB")
        if gefunden6 == -1: 
            gefunden6=len(xml+1)
        gefunden7 = xml.find("PRIVACY")
        if gefunden7 == -1: 
            gefunden7=len(xml+1)
        #Suche den Kleinsten Wert, dies ist das Wort as zuerst geprüft wird, ob es im title steht
        gefunden= minimum([gefunden1, gefunden2, gefunden3, gefunden4, gefunden5, gefunden6; gefunden7])
        #print(gefunden)


        #Der Text soll mind noch 2000 Wörter haben, wenn weniger soll nicht gekürzt werden
        if len(xml)<2000: 
            endergebnis=ausgang
            break

        #Wenn das gefundene Wort zwischen den title steht, dann kürze alles vor dem title weg und nimm den rest als Ergebnis
        if gefunden<ende:
            if gefunden>anfang:
                ergebnis= xml[anfang:]
                endergebnis=text+ergebnis
                break        

        #Wenn das gefundene Wort hinter dem title steht gibt es 2 Varianten: Die erste ist es steht noch vor dem Ende des Textes, dann wird alles incl der 2 title rausgekürzt
        #Die zweite es steht außerhalb des textes, was dadurch passieren kann weil oben alle nicht gefundenen Wörter auf len+1 gesetzt wurden, dann soll es abbrechen, dann gibt es keines der Wörter weiter im Text
        elif gefunden>ende:
            if gefunden>len(xml):
                endergebnis=ausgang
                break
            xml= xml[(ende+8):]
            
        #Wenn das Wort in einem text vor dem title steht wird dieser text weggekürzt
        elif gefunden<anfang:
            xml= xml[anfang:]
            

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
    


