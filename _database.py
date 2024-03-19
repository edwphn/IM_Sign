import pyodbc
import asyncio
from functools import partial
from config_loader import config_vars, SCRIPT_DIR


insert_Documents = """
INSERT INTO Documents (UUID, SignTimestamp, FileName, OriginalDocId, FileSize, RecordTime, Sender)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

insert_DocumentsHistory = """
INSERT INTO DocumentsHistory (UUID, Status, Message, RecordTime)
VALUES (?, ?, ?, ?)
"""


async def execute_sql_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        sql_command = file.read()
        await execute_sql(sql_command)


async def run_in_executor(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(func, *args))


async def execute_sql(sql, params=None):
    connection = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={config_vars["DATABASE"]["SERVER"]};'
        f'DATABASE={config_vars["DATABASE"]["NAME"]};'
        f'UID={config_vars["DATABASE"]["USER"]};'
        f'PWD={config_vars["DATABASE"]["PASSWORD"]}',
        autocommit=True
    )
    try:
        with connection.cursor() as cursor:
            if params:
                await run_in_executor(cursor.execute, sql, params)
            else:
                await run_in_executor(cursor.execute, sql)
    finally:
        connection.close()


async def create_tables():
    await execute_sql_from_file('create_Documents.sql')
    await execute_sql_from_file('create_DocumentsHistory.sql')


import pyodbc

def execute_sql_sync(sql, params=None):
    try:
        connection = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            f'SERVER={config_vars["DATABASE"]["SERVER"]};'
            f'DATABASE={config_vars["DATABASE"]["NAME"]};'
            f'UID={config_vars["DATABASE"]["USER"]};'
            f'PWD={config_vars["DATABASE"]["PASSWORD"]}',
            autocommit=True
        )

    except pyodbc.Error as e:
        print(f"Error connecting to the database: {e}")
        raise

    try:
        cursor = connection.cursor()
        if params is not None:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

    finally:
        cursor.close()
        connection.close()

