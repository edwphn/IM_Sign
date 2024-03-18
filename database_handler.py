import pyodbc
import asyncio
from functools import partial

DATABASE_URL = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.0.0.56;DATABASE=Kofax_custom;UID=sql3_servis;PWD=A3eURK7sAbj9CjTM"

async def execute_sql_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        sql_command = file.read()
        await execute_sql(sql_command)

insert_Sign_PDF = """
INSERT INTO Sign_PDF (UUID, SignTimestamp, FileName, OriginalDocId, FileSize, RecordTime, Sender)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

insert_Sign_PDF_history = """
INSERT INTO Sign_PDF_history (UUID, Status, Message, RecordTime)
VALUES (?, ?, ?, ?)
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

async def create_tables():
    await execute_sql_from_file('create_Sign_PDF.sql')
    await execute_sql_from_file('create_Sign_PDF_history.sql')
