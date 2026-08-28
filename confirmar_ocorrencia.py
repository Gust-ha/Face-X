from database.connection import engine
from sqlalchemy import text


OCORRENCIA_ID = 6


with engine.begin() as connection:
    connection.execute(
        text("""
            UPDATE occurrences
            SET status = 'CONFIRMED'
            WHERE id = :id
        """),
        {"id": OCORRENCIA_ID}
    )

print(f"Ocorrência {OCORRENCIA_ID} confirmada.")
