from _database import fetch_sql_sync

query = "SELECT * FROM DocumentsHistory WHERE UUID = '7001697E-A8FF-4572-A9D1-A5CF86D9CAAE'"

result = fetch_sql_sync(query)

for row in result:
    print(row)
