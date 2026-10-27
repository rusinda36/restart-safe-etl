import pyodbc

SERVER = r".\SQLEXPRESS"
DATABASE = "RestartSafeETL"

drivers = pyodbc.drivers()

if "ODBC Driver 18 for SQL Server" in drivers:
    driver = "ODBC Driver 18 for SQL Server"
elif "ODBC Driver 17 for SQL Server" in drivers:
    driver = "ODBC Driver 17 for SQL Server"
else:
    raise RuntimeError("SQL Server ODBC driver not found")

connection_string = (
    f"DRIVER={{{driver}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

with pyodbc.connect(connection_string) as connection:
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            @@SERVERNAME AS ServerName,
            DB_NAME() AS DatabaseName,
            SUSER_SNAME() AS LoginName
    """)

    row = cursor.fetchone()

    print("Connection successful")
    print(f"Server: {row.ServerName}")
    print(f"Database: {row.DatabaseName}")
    print(f"Login: {row.LoginName}")