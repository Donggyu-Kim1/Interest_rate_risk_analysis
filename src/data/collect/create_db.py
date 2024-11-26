import pymysql
from config.config_db import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_CHARSET

try:
    conn = pymysql.connect(
        user=DB_USER, passwd=DB_PASSWORD, host=DB_HOST, charset=DB_CHARSET
    )

    mycursor = conn.cursor()

    # 데이터베이스 생성
    mycursor.execute("CREATE DATABASE IF NOT EXISTS woori_bond_db")
    print("woori_bond_db 데이터베이스 생성 완료")

except pymysql.Error as e:
    print("Error:", e)

finally:
    if "conn" in locals() and conn:
        conn.close()
        print("MySQL 연결 종료")
