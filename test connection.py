import pyodbc

conn = pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=tcp:sql-rt-iprd-liveparams-prod.database.windows.net,1433;"
    r"DATABASE=LiveParameters-Prod;"
    r"Authentication=ActiveDirectoryInteractive;"
    r"Encrypt=yes;",
    timeout=30
)

print("Connected successfully")

conn.close()
