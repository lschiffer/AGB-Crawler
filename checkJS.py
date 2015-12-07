"""Function to check if text/xml contains java script typical symbols.

In regular text there should be hardly any curly braces. If there is a pair of curly braces inside given xml document there is a high probability that there is some kind of javascript inside the text.
"""

import sqlite3
import re

def checkJS(xml):
    """Check if there are curly braces inside given xml-string

    @param xml: xml string to check
    @type xml: string
    @return: true if there is a pair of curly braces
    """
    pat = re.compile('{.*}', re.DOTALL)
    return (len(pat.findall(xml)) > 0)

def main(database = "parsed_all.db"):
    """main file to loop over given database and check for text quality
    @param database: name of the database to use
    @type database: string
    """

    connection = sqlite3.connect(database)
    with connection:
        cursor = connection.cursor()

        result = cursor.execute('select text_xml from AGB')
        rows = result.fetchall()
        for i,row in enumerate(rows):
            print(i, "\t", checkJS(row[0]))
