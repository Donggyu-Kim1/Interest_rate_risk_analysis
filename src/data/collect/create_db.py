import pymysql

try:
    conn = pymysql.connect(user="root", passwd="3406", host="localhost", charset="utf8")

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
