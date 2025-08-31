import os
import dotenv
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker

dotenv.load_dotenv()

db_host = os.getenv("DB_HOST")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_database = os.getenv("DB_DATABASE")
db_port = os.getenv("DB_PORT")
if not db_port is None:
    db_port = int(db_port)
    

ca_path = os.path.abspath("isrgrootx1.pem")

def get_db_engine():
    connect_args = {}
    if ca_path:
        connect_args = {
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "ssl_ca": ca_path,
        }
    return create_engine(
        URL.create(
            drivername="mysql+pymysql",
            username=db_username,
            password=db_password,
            host=db_host,
            port=db_port,
            database=db_database,
        ),
        connect_args=connect_args,
    )

engine = get_db_engine()
session = sessionmaker(bind=engine)

