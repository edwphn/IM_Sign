from config_loader import config_vars
import pyodbc

connection_string = 'DRIVER={ODBC Driver 17 for SQL Server};' \
                    f'SERVER={config_vars["DATABASE"]["SERVER"]};' \
                    f'DATABASE={config_vars["DATABASE"]["NAME"]};' \
                    f'UID={config_vars["DATABASE"]["USER"]};' \
                    f'PWD={config_vars["DATABASE"]["PASSWORD"]}'

print(connection_string)


def execute_sql_select_sync(sql):
    try:
        connection = pyodbc.connect(connection_string, autocommit=True)
        cursor = connection.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        return results[0]

    except pyodbc.Error as e:
        print(f'Error executing SQL SELECT operation: {e}')
        raise

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


check_file_status = """
SELECT Status, Message FROM DocumentsHistory
WHERE UUID = '6525c30d-5f10-4e85-88c9-a05272487c33'
"""

signed = execute_sql_select_sync(check_file_status)

if signed:
    print(signed[0])
    print(signed[1])
else:
    print('No signed')
