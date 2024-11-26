import pymysql
from config.config_db import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_CHARSET

try:
    conn = pymysql.connect(
        user=DB_USER, passwd=DB_PASSWORD, host=DB_HOST, charset=DB_CHARSET
    )

    print("MySQL 연결 성공")
    mycursor = conn.cursor()

except pymysql.Error as e:
    print("Error:", e)

finally:
    if "conn" in locals() and conn:
        conn.close()
        print("MySQL 연결 종료")
