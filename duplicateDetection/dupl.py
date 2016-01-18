#!/bin/python 
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as etree
import re
from optparse import OptionParser
import sqlite3 as lite


threshold_similarity = 0.8
threshold_length = 300
threshold_minlength = 100



def similarityof(document_1,document_2):
    '''
    Calculation the percentage of mutually contained words.
    
    :param document_1: Document 1
    :param document_2: Document to compare with.
    
    :return: Percentage of words from 1 that are contained in 2, Percentage of words from 2 contained in 1
    :return type: float,float
    '''
    
    vocab_1 = re.sub("[^A-Za-z0-9 ]+","",re.sub("<.{1,10}>","",document_1)).split(' ')
    vocab_1 = [word for word in vocab_1 if len(word) > 1]
    vocab_2 = re.sub("[^A-Za-z0-9 ]+","",re.sub("<.{1,10}>","",document_2)).split(' ')
    vocab_2 = [word for word in vocab_2 if len(word) > 1]
    
    if len(vocab_1) < threshold_minlength or len(vocab_2) < threshold_minlength:
        return [0.0,0.0]
    
    #print ("manual_number_of_words:	",vocab_1)
    #print ("autogen_number_of_words:	",vocab_2)


    ##
    tmp=list(vocab_2)
    number_1_in_2=0
    for word in vocab_1:
            if word in tmp:
                    number_1_in_2+=1
                    tmp.remove(word)

    percentage1=float(number_1_in_2)/float(len(vocab_1))
    ##
    tmp=list(vocab_1)
    number_2_in_1 = 0
    for word in vocab_2:
            if word in tmp:
                    number_2_in_1+=1
                    tmp.remove(word)
                    


    percentage2=float(number_2_in_1)/float(len(vocab_2))

    return [percentage1,percentage2]
    
def new_database(output_file):
    '''
    Create a New Database suited for the Duplicates.
    Columns: ID1, ID2, percentage1, percentage2
    
    #:param output_file: Name of the sqlite3 database file that will be created
    '''
    

    output_con = lite.connect(output_file)

    with output_con:

       cur =  output_con.cursor()
       cur.execute('''DROP TABLE IF EXISTS AGB''')
       cur.execute('''CREATE TABLE duplicates(app_id1 TEXT , app_id2 TEXT , percentage1 float, percentage2 float, PRIMARY KEY( app_id1 , app_id2))''')



def grab_duplicates(input_file,output_file):
    '''
    Iterate over the given database and write all the duplicates to an output database with the respective score
    
    :param input_file: Input database
    :param output_file: Output database
    '''
    input_con = lite.connect(input_file)
    output_con = lite.connect(output_file)
    
    with input_con,output_con:
        cursor = input_con.cursor()  
        output_cursor = output_con.cursor()
        
        number_of_entries = cursor.execute("SELECT COUNT(*) from AGB").fetchone()[0]
        print("Number Of Rows: ",number_of_entries)
        
        
        for i in range(1,number_of_entries):
            cursor.execute("Select app_id,text_xml,LENGTH(text_xml) from AGB  WHERE LENGTH(text_xml)>10 ORDER BY LENGTH(text_xml) DESC  LIMIT 1 OFFSET " + repr(i)  )
            row = cursor.fetchone()
            app_id1 = repr(row[0])
            doc1 = repr(row[1].encode('utf-8'));  
            length_doc1 = row[2]
            
            docs = cursor.execute("Select app_id,text_xml,LENGTH(text_xml) from AGB WHERE LENGTH(text_xml)>10 ORDER BY LENGTH(text_xml) DESC Limit " + repr(i+1) +",-1" )

            print("Comparing all to: ",app_id1.encode("utf-8"))
            for doc_row in docs:
                
                app_id2 = repr(doc_row[0])
                doc2 = repr(doc_row[1].encode('utf-8'));
                length_doc2 =int(doc_row[2])
                
                
                #print("SELECT count(*) FROM duplicates WHERE app_id2 = "+app_id2)
                output_cursor.execute("SELECT count(*) FROM duplicates WHERE app_id2 = "+app_id2)
                data=output_cursor.fetchone()[0]

                if data!=0:
                    break
                

                #Do not compare Texts with length difference greater than the threshold
                if abs(int(length_doc1)-int(length_doc2)) > int(threshold_length):
                    #print("yess")
                    continue
                
                
                #compare docs

                perc1,perc2 = similarityof(doc1,doc2)
                
                #if similarity is higher than the threshold 
                if (perc1+perc2)/2.0 > threshold_similarity:
                    print("Duplicate:")
                    print ("\t",app_id2.encode("utf-8"))
                    print("\tPercentage:")
                    print("\t[",perc1,",",perc2,"]\n")
                    #print("INSERT INTO duplicates(app_id1 , app_id2 , percentage1 , percentage2 ) VALUES ("+str(app_id1)+","+str(app_id2)+","+repr(perc1)+","+","+repr(perc2)+")")
                    output_cursor.execute("INSERT INTO duplicates(app_id1 , app_id2 , percentage1 , percentage2 ) VALUES ("+app_id1+","+app_id2+","+repr(perc1)+","+repr(perc2)+")")
                    output_con.commit();
                
            print("\n")
    

    
def main():
    '''
    Short Main function to hand over the commandline Arguments to grap duplicates
    '''

    parser = OptionParser()
    
    parser.add_option("-i","--input",dest = "input_file",default =[], metavar="INPUT_FILE" ,action = "append", help="reading in sqlite3 database")
    parser.add_option("-o","--output",dest = "output_file",default =[], metavar="OUTPUT_FILE" ,action = "append", help="reading in sqlite3 database")
    
    options, args = parser.parse_args()
    input_file = options.input_file   
    output_file = options.output_file
    print(output_file[0])
    #new_database(output_file[0])
    grab_duplicates(input_file[0],output_file[0])
    
    
if __name__ == "__main__":
    main()
