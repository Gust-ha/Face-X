from database.connection import engine
from sqlalchemy import text

with engine.begin() as connection:
    connection.execute(
        text("ALTER TABLE participants ADD COLUMN face_encoding TEXT")
    )

print("Coluna face_encoding criada")
