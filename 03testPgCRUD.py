'''
Created on Aug 5, 2010

@author: apm
'''
#Test CRUD on opengemdb database
#CREATE : Create testTable
#       : Insert rows
#READ   : Read rows
#UPDATE : Change row values
#DELETE : Delete Element
#       : Drop Table

#!/usr/bin/python
import psycopg2
#note that we have to import the Psycopg2 extras library!
import sys
import pprint

def main():
    #start of script
    #Define our connection string

    conn_string = "host='gemsun01.ethz.ch' dbname='opengemdb' user='user' password=''"
    
    # print the connection string we will use to connect
    print "Connecting to database\n    ->%s" % (conn_string)
    try:
        # get a connection, if a connect cannot be made an exception will be raised here
        conn = psycopg2.connect(conn_string)
        print "Connected!\n"
        
        # conn.cursor will return a cursor oject, you can use this cursor to perform queries
        cursor = conn.cursor()

        # create a Table
        cursor.execute("CREATE TABLE testTable (name char(8), value float)")
        
        # insert rows into table
        cursor.execute("INSERT INTO testTable VALUES('one', 1.0)")
        cursor.execute("INSERT INTO testTable VALUES('two', 2.0)")
        cursor.execute("INSERT INTO testTable VALUES('three', 3.0)")
        # makes changes permanent
        conn.commit()
        
        # read rows in table and print       
        cursor.execute("SELECT * FROM testTable")
        rows = cursor.fetchall()
        
        for i in range(len(rows)):
            print "Row:", i, "name:", rows[i][0], "value:", rows[i][1]

        # print out the records using pretty print
        print "Print rows using pretty print"
        pprint.pprint(rows)
 
        # delete a row
        print "delete row three"
        cursor.execute("DELETE FROM testTable where name='three'")
        conn.commit()
        
        cursor.execute("SELECT * FROM testTable")
        rows = cursor.fetchall()
        print "Print rows with row 3 deleted using pretty print"
        pprint.pprint(rows)
        
        print "Dropping table testTable"
        cursor.execute("DROP TABLE testTable")
        conn.commit()
        
        cursor.close()
	conn.close()
       
        print "End CRUD Test with Python, DB API 2.0 with db adapter psycopg2!"
    except:
        # Get the most recent exception
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        # Exit the script and print an error telling what happened.
        sys.exit("Database connection failed!\n ->%s" % (exceptionValue))

if __name__ == "__main__":
    sys.exit(main())

