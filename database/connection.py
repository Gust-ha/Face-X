from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg://xface_user:xface_dev_2026@localhost/xface"

engine = create_engine(DATABASE_URL)
