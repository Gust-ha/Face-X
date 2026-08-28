import json

import cv2
import face_recognition
import numpy as np
from sqlalchemy import text

from database.connection import engine


TOLERANCIA_PADRAO = 0.60
MODELO_DETECCAO_PADRAO = "hog"

def carregar_participantes():
    """
    Carrega do PostgreSQL todos os participantes que possuem
    encoding facial cadastrado.
    """

    query = text("""
        SELECT
            id,
            name,
            age,
            status,
            crime,
            face_reference,
            face_encoding
        FROM participants
        WHERE face_encoding IS NOT NULL
          AND face_encoding <> ''
        ORDER BY id
    """)

    with engine.connect() as connection:
        result = connection.execute(query)

        participantes = []

        for row in result.mappings():
            try:
                encoding = np.array(
                    json.loads(row["face_encoding"]),
                    dtype=np.float64
                )
            except (json.JSONDecodeError, TypeError) as erro:
                print(
                    f"Aviso: encoding inválido para "
                    f"participante {row['id']}: {erro}"
                )
                continue

            if encoding.shape != (128,):
                print(
                    f"Aviso: encoding do participante "
                    f"{row['id']} possui dimensão "
                    f"{encoding.shape}, esperado (128,)"
                )
                continue

            participantes.append({
                "id": row["id"],
                "name": row["name"],
                "age": row["age"],
                "status": row["status"],
                "crime": row["crime"],
                "face_reference": row["face_reference"],
                "encoding": encoding,
            })

        return participantes


def gerar_encoding(imagem, model="hog"):
    """
    Recebe uma imagem em memória e retorna os encodings faciais.

    imagem pode ser:
    - imagem RGB como numpy array
    - frame BGR vindo do OpenCV
    """

    if imagem is None:
        raise ValueError("Imagem/frame inválido.")

    # Se vier do OpenCV, converte BGR -> RGB.
    if len(imagem.shape) == 3:
        imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)
    else:
        imagem_rgb = imagem

    localizacoes = face_recognition.face_locations(
        imagem_rgb,
        model=model
    )

    if not localizacoes:
        return [], localizacoes

    encodings = face_recognition.face_encodings(
        imagem_rgb,
        known_face_locations=localizacoes
    )

    return encodings, localizacoes


def reconhecer_encoding(
    encoding,
    participantes=None,
    tolerancia=TOLERANCIA_PADRAO
):
    """
    Compara um encoding contra todos os participantes do PostgreSQL.
    """

    if participantes is None:
        participantes = carregar_participantes()

    if not participantes:
        return None

    encodings_conhecidos = [
        participante["encoding"]
        for participante in participantes
    ]

    distancias = face_recognition.face_distance(
        encodings_conhecidos,
        encoding
    )

    melhor_indice = int(np.argmin(distancias))
    melhor_distancia = float(distancias[melhor_indice])

    participante = participantes[melhor_indice]

    matched = melhor_distancia <= tolerancia

    # Indicador visual simples.
    # A decisão real é feita pela distância/tolerância.
    similarity = max(
        0.0,
        min(
            100.0,
            (1.0 - melhor_distancia) * 100.0
        )
    )

    if not matched:
        return None

    return {
        "id": participante["id"],
        "name": participante["name"],
        "age": participante["age"],
        "status": participante["status"],
        "crime": participante["crime"],
        "face_reference": participante["face_reference"],
        "distance": melhor_distancia,
        "similarity": similarity,
        "matched": True,
    }


def reconhecer_frame(
    frame,
    tolerancia=TOLERANCIA_PADRAO,
    participantes=None,
    model=MODELO_DETECCAO_PADRAO
):
    """
    Reconhece diretamente um frame OpenCV.

    Não salva o frame no disco.

    Retorna:
        {
            "resultado": resultado,
            "localizacoes": localizacoes,
            "encoding": encoding
        }

    ou None quando nenhum rosto reconhecido for encontrado.
    """

    encodings, localizacoes = gerar_encoding(
        frame,
        model=model
    )

    if not encodings:
        return None

    if participantes is None:
        participantes = carregar_participantes()

    melhor_resultado = None
    melhor_encoding = None
    melhor_localizacao = None

    for encoding, localizacao in zip(
        encodings,
        localizacoes
    ):
        resultado = reconhecer_encoding(
            encoding,
            participantes=participantes,
            tolerancia=tolerancia
        )

        if resultado is None:
            continue

        if (
            melhor_resultado is None
            or resultado["distance"]
            < melhor_resultado["distance"]
        ):
            melhor_resultado = resultado
            melhor_encoding = encoding
            melhor_localizacao = localizacao

    if melhor_resultado is None:
        return None

    return {
        "resultado": melhor_resultado,
        "encoding": melhor_encoding,
        "localizacao": melhor_localizacao,
        "localizacoes": localizacoes,
    }


def reconhecer_imagem(
    imagem_path,
    tolerancia=TOLERANCIA_PADRAO
):
    """
    Mantém compatibilidade com os testes antigos.

    Carrega uma imagem do disco e usa a mesma lógica
    de reconhecimento.
    """

    imagem = face_recognition.load_image_file(
        str(imagem_path)
    )

    resultado = reconhecer_frame(
        imagem,
        tolerancia=tolerancia
    )

    if resultado is None:
        return None

    return resultado["resultado"]
