import json
from pathlib import Path

import face_recognition
from sqlalchemy import text

from database.connection import engine


PARTICIPANT_ID = 1
IMAGE_PATH = Path.home() / "Downloads" / "foragido.jpg"


def main():
    print(f"Imagem: {IMAGE_PATH}")

    if not IMAGE_PATH.exists():
        raise FileNotFoundError(
            f"Imagem não encontrada: {IMAGE_PATH}"
        )

    print("Carregando imagem...")
    imagem = face_recognition.load_image_file(str(IMAGE_PATH))

    print("Detectando rosto...")
    localizacoes = face_recognition.face_locations(
    imagem,
    model="cnn"
)

    print(f"Rostos encontrados: {len(localizacoes)}")

    if len(localizacoes) == 0:
        raise RuntimeError(
            "Nenhum rosto foi encontrado na imagem."
        )

    if len(localizacoes) > 1:
        raise RuntimeError(
            "Mais de um rosto foi encontrado. "
            "O cadastro exige exatamente um rosto."
        )

    print("Gerando encoding facial...")
    encodings = face_recognition.face_encodings(
        imagem,
        known_face_locations=localizacoes
    )

    if len(encodings) != 1:
        raise RuntimeError(
            "Não foi possível gerar exatamente um encoding facial."
        )

    encoding = encodings[0]

    print(f"Dimensões do encoding: {len(encoding)}")

    if len(encoding) != 128:
        raise RuntimeError(
            f"Encoding inesperado: {len(encoding)} dimensões."
        )

    encoding_json = json.dumps(encoding.tolist())

    with engine.begin() as connection:
        participante = connection.execute(
            text("""
                SELECT id, name
                FROM participants
                WHERE id = :id
            """),
            {"id": PARTICIPANT_ID}
        ).mappings().first()

        if participante is None:
            raise RuntimeError(
                f"Participante {PARTICIPANT_ID} não encontrado."
            )

        print(
            f"Participante encontrado: "
            f"{participante['id']} - {participante['name']}"
        )

        connection.execute(
            text("""
                UPDATE participants
                SET
                    face_reference = :face_reference,
                    face_encoding = :face_encoding
                WHERE id = :id
            """),
            {
                "id": PARTICIPANT_ID,
                "face_reference": str(IMAGE_PATH),
                "face_encoding": encoding_json,
            }
        )

    print()
    print("========================================")
    print("ENCODING CADASTRADO COM SUCESSO")
    print("========================================")
    print(f"Participante : {participante['name']}")
    print(f"ID           : {PARTICIPANT_ID}")
    print(f"Dimensões    : {len(encoding)}")
    print(f"Imagem       : {IMAGE_PATH}")


if __name__ == "__main__":
    main()
