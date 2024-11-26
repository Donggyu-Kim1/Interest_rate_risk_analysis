from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 데이터베이스 설정 가져오기
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_CHARSET = os.getenv("DB_CHARSET")
