import json
from pathlib import Path

import face_recognition
import numpy as np
from sqlalchemy import text

from database.connection import engine


PARTICIPANT_ID = 1
IMAGE_PATH = Path.home() / "Downloads" / "foragido.jpg"


def main():
    # ---------------------------------------------------------
    # 1. Buscar encoding no PostgreSQL
    # ---------------------------------------------------------
    print("Buscando encoding no PostgreSQL...")

    with engine.connect() as connection:
        participante = connection.execute(
            text("""
                SELECT
                    id,
                    name,
                    face_encoding
                FROM participants
                WHERE id = :id
            """),
            {"id": PARTICIPANT_ID}
        ).mappings().first()

    if participante is None:
        raise RuntimeError(
            f"Participante {PARTICIPANT_ID} não encontrado."
        )

    if not participante["face_encoding"]:
        raise RuntimeError(
            "O participante não possui face_encoding."
        )

    print(f"Participante: {participante['name']}")

    # ---------------------------------------------------------
    # 2. Converter JSON armazenado para numpy array
    # ---------------------------------------------------------
    encoding_banco = np.array(
        json.loads(participante["face_encoding"]),
        dtype=np.float64
    )

    print(
        f"Encoding recuperado do banco: "
        f"{len(encoding_banco)} dimensões"
    )

    if len(encoding_banco) != 128:
        raise RuntimeError(
            f"Encoding inválido: "
            f"{len(encoding_banco)} dimensões."
        )

    # ---------------------------------------------------------
    # 3. Carregar imagem de teste
    # ---------------------------------------------------------
    print(f"Carregando imagem: {IMAGE_PATH}")

    if not IMAGE_PATH.exists():
        raise FileNotFoundError(
            f"Imagem não encontrada: {IMAGE_PATH}"
        )

    imagem = face_recognition.load_image_file(
        str(IMAGE_PATH)
    )

    # ---------------------------------------------------------
    # 4. Detectar rosto usando CNN
    # ---------------------------------------------------------
    print("Detectando rosto...")

    localizacoes = face_recognition.face_locations(
        imagem,
        model="cnn"
    )

    print(f"Rostos encontrados: {len(localizacoes)}")

    if len(localizacoes) != 1:
        raise RuntimeError(
            f"Esperado exatamente 1 rosto, "
            f"mas foram encontrados {len(localizacoes)}."
        )

    # ---------------------------------------------------------
    # 5. Gerar encoding da imagem
    # ---------------------------------------------------------
    print("Gerando encoding da imagem...")

    encoding_imagem = face_recognition.face_encodings(
        imagem,
        known_face_locations=localizacoes
    )[0]

    print(
        f"Encoding da imagem: "
        f"{len(encoding_imagem)} dimensões"
    )

    # ---------------------------------------------------------
    # 6. Comparar
    # ---------------------------------------------------------
    distancia = face_recognition.face_distance(
        [encoding_banco],
        encoding_imagem
    )[0]

    tolerancia = 0.6

    corresponde = distancia <= tolerancia

    print()
    print("========================================")
    print("RESULTADO DA COMPARAÇÃO")
    print("========================================")
    print(f"Participante : {participante['name']}")
    print(f"Distância    : {distancia:.6f}")
    print(f"Tolerância   : {tolerancia:.2f}")
    print(f"Correspondência: {'SIM' if corresponde else 'NÃO'}")
    print("========================================")


if __name__ == "__main__":
    main()
