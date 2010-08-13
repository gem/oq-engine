'''
Created on Aug 12, 2010

@author: apm
'''
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base

def dbconnect(conn_str):
    """connects to a given database based on the connection string
    
    For a postgresql database:
    conn_str = 'postgresql://<username>:<password>@<hostname>/<databasename>'
    """
    
    engine = create_engine (conn_str, echo=True)
    return engine
    
