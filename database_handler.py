import pyodbc
import asyncio
from functools import partial
from uuid import uuid4
from datetime import datetime

# Database connection parameters
DATABASE_URL = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=test;UID=sa;PWD=k4714m.900625"

# SQL command for creating a table
sql_command = """
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'PDF_Sign_Journal')
BEGIN
    CREATE TABLE PDF_Sign_Journal (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        Insert_Time DATETIME NOT NULL DEFAULT(GETUTCDATE()),
        UUID UNIQUEIDENTIFIER NOT NULL,
        File_Name NVARCHAR(255) NOT NULL,
        Requester NVARCHAR(255) NOT NULL,
        Sign_Timestamp DATETIME2,
        Status NVARCHAR(255),
        Err_Msg NVARCHAR(MAX),
        Additional_Info NVARCHAR(MAX)
    );
END
"""

# SQL command for inserting data
insert_sql = """
INSERT INTO PDF_Sign_Journal (Insert_Time, UUID, File_Name, Requester, Sign_Timestamp, Status)
VALUES (?, ?, ?, ?, ?, ?)
"""

async def run_in_executor(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(func, *args))

async def execute_sql(sql, params=None):
    connection = pyodbc.connect(DATABASE_URL, autocommit=True)
    try:
        with connection.cursor() as cursor:
            if params:
                await run_in_executor(cursor.execute, sql, params)
            else:
                await run_in_executor(cursor.execute, sql)
    finally:
        connection.close()

async def create_table():
    await execute_sql(sql_command)

async def insert_data():
    # Example data
    now = datetime.utcnow()
    uuid = uuid4()
    file_name = "example.pdf"
    requester = "requester@example.com"
    status = "Signed"
    # Execute INSERT operation
    await execute_sql(insert_sql, (now, uuid, file_name, requester, now, status))
