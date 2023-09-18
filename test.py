import pandas as pd
import mysql.connector as conn


try:
    mydb = conn.connect(host = "app.lagoonmed.eu",database="gp",user="root",password="P@xtibi2021!")
    mf = pd.read_sql("select * from gps",mydb)
except Exception as e:
    print(e)

mydb.close()
