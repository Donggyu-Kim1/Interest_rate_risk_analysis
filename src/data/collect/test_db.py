import pymysql

try:
    conn = pymysql.connect(user="root", passwd="3406", host="localhost", charset="utf8")

    print("MySQL 연결 성공")
    mycursor = conn.cursor()

except pymysql.Error as e:
    print("Error:", e)

finally:
    if "conn" in locals() and conn:
        conn.close()
        print("MySQL 연결 종료")
