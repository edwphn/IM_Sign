# _database.py

import pyodbc
import asyncio
from _logger import logger
from functools import partial
from _config import DB_SERVER_URL, DB_NAME, DB_USER, DB_PASSWORD


CONNECTION_STRING = 'DRIVER={ODBC Driver 17 for SQL Server};' \
                    f'SERVER={DB_SERVER_URL};' \
                    f'DATABASE={DB_NAME};' \
                    f'UID={DB_USER};' \
                    f'PWD={DB_PASSWORD}'


# -------------- Async query mechanism --------------
async def fetch_sql(sql, params=None):
    connection = pyodbc.connect(CONNECTION_STRING, autocommit=True)
    results = []
    try:
        with connection.cursor() as cursor:
            if params:
                await run_in_executor(cursor.execute, sql, params)
            else:
                await run_in_executor(cursor.execute, sql)
            results = await run_in_executor(cursor.fetchall)
    finally:
        connection.close()
    return results[0]


async def run_in_executor(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(func, *args))


async def execute_query(sql, params=None):
    connection = pyodbc.connect(CONNECTION_STRING, autocommit=True)
    try:
        with connection.cursor() as cursor:
            if params:
                await run_in_executor(cursor.execute, sql, params)
            else:
                await run_in_executor(cursor.execute, sql)
    finally:
        connection.close()


# -------------- Sync queries --------------
def execute_sql_sync(sql, params=None):
    try:
        with pyodbc.connect(CONNECTION_STRING, autocommit=True) as connection:
            with connection.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
    except pyodbc.Error as e:
        logger.error(f"Error executing SQL command: {e}")
        raise


def fetch_sql_sync(sql, params=None):
    try:
        with pyodbc.connect(CONNECTION_STRING, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params) if params else cursor.execute(sql)
                return cursor.fetchall() if cursor.description else None
    except pyodbc.Error as e:
        logger.error(f"Error executing SQL command: {e}")
        raise


# -------------- queries templates --------------
insert_Documents = """
INSERT INTO Documents (UUID, SignTimestamp, FileName, OriginalDocId, FileSize, RecordTime, Sender)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

insert_DocumentsHistory = """
INSERT INTO DocumentsHistory (UUID, Status, Message, RecordTime)
VALUES (?, ?, ?, ?)
"""

check_file_status = """
SELECT TOP 1 Status, Message FROM DocumentsHistory WHERE UUID = ? ORDER BY ID DESC
"""

create_Documents = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Documents' AND type = 'U')
BEGIN
    CREATE TABLE Documents (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        UUID uniqueidentifier NOT NULL UNIQUE,
        SignTimestamp DATETIME2 NULL,
        FileName NVARCHAR(500) NULL,
        OriginalDocId NVARCHAR(500) NULL,
        FileSize INT NULL,
        RecordTime DATETIME NOT NULL DEFAULT GETDATE(),
        Sender NVARCHAR(255) NULL
    );
END 
"""

create_DocumentsHistory = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DocumentsHistory' AND type = 'U')
AND EXISTS (SELECT * FROM sys.tables WHERE name = 'Documents' AND type = 'U')
BEGIN
    CREATE TABLE DocumentsHistory (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        UUID uniqueidentifier NOT NULL,
        Status NVARCHAR(50) NOT NULL,
        Message NVARCHAR(MAX) NULL,
        RecordTime DATETIME NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (UUID) REFERENCES Documents(UUID)
    );
END
"""

create_Certificates = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Certificates' AND type = 'U')
BEGIN
    CREATE TABLE Certificates (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        Valid BIT NOT NULL,
        CertName NVARCHAR(50) NOT NULL,
        Expiration DATETIME NOT NULL,
        Issuer NVARCHAR(MAX) NULL,
        Subject NVARCHAR(MAX) NULL,
        RecordTime DATETIME NOT NULL DEFAULT GETDATE(),
        CertificateData VARBINARY(MAX)
    );
END
"""
