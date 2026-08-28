from sqlalchemy import text

from database.connection import engine
from central.reconhecimento import reconhecer_imagem


# ============================================================
# BUSCAR OCORRÊNCIAS PENDENTES
# ============================================================

def buscar_ocorrencias_pendentes():
    """
    Busca todas as ocorrências PENDING.

    Retorna também a foto de referência do participante,
    permitindo que a Central mostre:

        foto de referência
        +
        frame capturado
    """

    query = text("""
        SELECT
            o.id AS occurrence_id,
            o.participant_id,
            o.camera_id,

            p.name,
            p.age,
            p.status,
            p.crime,
            p.face_reference,

            c.name AS camera,
            c.location,

            o.similarity,
            o.detected_at,
            o.status AS occurrence_status,
            o.frame_path

        FROM occurrences o

        JOIN participants p
            ON o.participant_id = p.id

        JOIN cameras c
            ON o.camera_id = c.id

        WHERE o.status = 'PENDING'

        ORDER BY o.detected_at ASC
    """)

    with engine.connect() as connection:
        result = connection.execute(query)

        return result.mappings().all()


# ============================================================
# RESUMO DAS OCORRÊNCIAS
# ============================================================

def buscar_resumo_ocorrencias():
    """
    Retorna a quantidade de ocorrências por status.
    """

    query = text("""
        SELECT
            COUNT(*) FILTER (
                WHERE status = 'PENDING'
            ) AS pending,

            COUNT(*) FILTER (
                WHERE status = 'CONFIRMED'
            ) AS confirmed,

            COUNT(*) FILTER (
                WHERE status = 'DISCARDED'
            ) AS discarded

        FROM occurrences
    """)

    with engine.connect() as connection:
        resultado = connection.execute(query).mappings().one()

        return dict(resultado)


# ============================================================
# BUSCAR UMA OCORRÊNCIA
# ============================================================

def buscar_ocorrencia(occurrence_id):
    """
    Busca uma ocorrência específica.
    """

    query = text("""
        SELECT
            o.id AS occurrence_id,
            o.participant_id,
            o.camera_id,

            p.name,
            p.age,
            p.status,
            p.crime,
            p.face_reference,

            c.name AS camera,
            c.location,

            o.similarity,
            o.detected_at,
            o.status AS occurrence_status,
            o.frame_path

        FROM occurrences o

        JOIN participants p
            ON o.participant_id = p.id

        JOIN cameras c
            ON o.camera_id = c.id

        WHERE o.id = :occurrence_id
    """)

    with engine.connect() as connection:
        resultado = connection.execute(
            query,
            {
                "occurrence_id": occurrence_id
            }
        )

        ocorrencia = resultado.mappings().first()

        if ocorrencia is None:
            return None

        return dict(ocorrencia)


# ============================================================
# REGISTRAR NOVA OCORRÊNCIA
# ============================================================

def registrar_ocorrencia(
    participant_id,
    camera_id,
    similarity,
    frame_path
):
    """
    Registra uma nova ocorrência.

    Toda ocorrência nova começa como PENDING.
    """

    query = text("""
        INSERT INTO occurrences (
            participant_id,
            camera_id,
            similarity,
            status,
            frame_path
        )

        VALUES (
            :participant_id,
            :camera_id,
            :similarity,
            'PENDING',
            :frame_path
        )

        RETURNING id
    """)

    with engine.begin() as connection:

        resultado = connection.execute(
            query,
            {
                "participant_id": participant_id,
                "camera_id": camera_id,
                "similarity": similarity,
                "frame_path": str(frame_path)
            }
        )

        return resultado.scalar()


# ============================================================
# VERIFICAR OCORRÊNCIA ATIVA
# ============================================================

def verificar_ocorrencia_ativa(
    participant_id,
    camera_id
):
    """
    Impede que o mesmo participante gere várias
    ocorrências PENDING simultaneamente na mesma câmera.
    """

    query = text("""
        SELECT
            id,
            participant_id,
            camera_id,
            similarity,
            status,
            frame_path,
            detected_at

        FROM occurrences

        WHERE participant_id = :participant_id
          AND camera_id = :camera_id
          AND status = 'PENDING'

        ORDER BY detected_at DESC

        LIMIT 1
    """)

    with engine.connect() as connection:

        resultado = connection.execute(
            query,
            {
                "participant_id": participant_id,
                "camera_id": camera_id
            }
        )

        ocorrencia = resultado.mappings().first()

        if ocorrencia is None:
            return None

        return dict(ocorrencia)


# ============================================================
# RECONHECER E REGISTRAR
# ============================================================

def reconhecer_e_registrar_ocorrencia(
    imagem_path,
    camera_id,
    tolerancia=0.60
):
    """
    Fluxo:

        imagem
           ↓
        reconhecimento
           ↓
        PostgreSQL
           ↓
        verifica duplicidade
           ↓
        cria PENDING
           ↓
        Central atualiza automaticamente
    """

    resultado = reconhecer_imagem(
        imagem_path,
        tolerancia=tolerancia
    )

    if resultado is None:
        return None

    # --------------------------------------------------------
    # Verifica ocorrência PENDING existente.
    # --------------------------------------------------------

    ocorrencia_existente = verificar_ocorrencia_ativa(
        participant_id=resultado["id"],
        camera_id=camera_id
    )

    if ocorrencia_existente is not None:

        return {
            "duplicate": True,

            "occurrence_id":
                ocorrencia_existente["id"],

            "participant_id":
                resultado["id"],

            "name":
                resultado["name"],

            "age":
                resultado["age"],

            "status":
                resultado["status"],

            "crime":
                resultado["crime"],

            "face_reference":
                resultado.get("face_reference"),

            "distance":
                resultado["distance"],

            "similarity":
                resultado["similarity"],

            "frame_path":
                ocorrencia_existente["frame_path"],

            "detected_at":
                ocorrencia_existente["detected_at"],

            "camera_id":
                camera_id,

            "occurrence_status":
                "PENDING"
        }

    # --------------------------------------------------------
    # Cria nova ocorrência.
    # --------------------------------------------------------

    occurrence_id = registrar_ocorrencia(
        participant_id=resultado["id"],
        camera_id=camera_id,
        similarity=resultado["similarity"],
        frame_path=str(imagem_path)
    )

    # --------------------------------------------------------
    # Busca a ocorrência criada.
    # --------------------------------------------------------

    ocorrencia = buscar_ocorrencia(
        occurrence_id
    )

    if ocorrencia is None:

        return {
            "duplicate": False,

            "occurrence_id":
                occurrence_id,

            "participant_id":
                resultado["id"],

            "name":
                resultado["name"],

            "age":
                resultado["age"],

            "status":
                resultado["status"],

            "crime":
                resultado["crime"],

            "face_reference":
                resultado.get("face_reference"),

            "distance":
                resultado["distance"],

            "similarity":
                resultado["similarity"],

            "frame_path":
                str(imagem_path),

            "camera_id":
                camera_id,

            "occurrence_status":
                "PENDING"
        }

    return {
        "duplicate": False,

        "occurrence_id":
            occurrence_id,

        "participant_id":
            resultado["id"],

        "name":
            resultado["name"],

        "age":
            resultado["age"],

        "status":
            resultado["status"],

        "crime":
            resultado["crime"],

        "face_reference":
            resultado.get("face_reference"),

        "distance":
            resultado["distance"],

        "similarity":
            resultado["similarity"],

        "frame_path":
            ocorrencia["frame_path"],

        "detected_at":
            ocorrencia["detected_at"],

        "camera_id":
            ocorrencia["camera_id"],

        "occurrence_status":
            ocorrencia["occurrence_status"],

        "camera":
            ocorrencia["camera"],

        "location":
            ocorrencia["location"]
    }


# ============================================================
# ALTERAR STATUS
# ============================================================

def atualizar_status_ocorrencia(
    occurrence_id,
    novo_status
):
    """
    Altera uma ocorrência PENDING para:

        CONFIRMED
        ou
        DISCARDED
    """

    if novo_status not in (
        "CONFIRMED",
        "DISCARDED"
    ):
        raise ValueError(
            "Status inválido. "
            "Use CONFIRMED ou DISCARDED."
        )

    query = text("""
        UPDATE occurrences

        SET status = :status

        WHERE id = :occurrence_id
          AND status = 'PENDING'

        RETURNING id, status
    """)

    with engine.begin() as connection:

        resultado = connection.execute(
            query,
            {
                "occurrence_id": occurrence_id,
                "status": novo_status
            }
        )

        ocorrencia = resultado.mappings().first()

        if ocorrencia is None:

            raise RuntimeError(
                f"A ocorrência {occurrence_id} "
                "não está mais PENDING "
                "ou não existe."
            )

        return dict(ocorrencia)


# ============================================================
# CONFIRMAR
# ============================================================

def confirmar_ocorrencia(
    occurrence_id
):
    """
    Confirma uma ocorrência.
    """

    return atualizar_status_ocorrencia(
        occurrence_id,
        "CONFIRMED"
    )


# ============================================================
# DESCARTAR
# ============================================================

def descartar_ocorrencia(
    occurrence_id
):
    """
    Descarta uma ocorrência.
    """

    return atualizar_status_ocorrencia(
        occurrence_id,
        "DISCARDED"
    )


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    ocorrencias = buscar_ocorrencias_pendentes()

    print()
    print("========================================")
    print("X-FACE - OCORRÊNCIAS PENDENTES")
    print("========================================")

    if not ocorrencias:

        print("Nenhuma ocorrência PENDING.")

    else:

        for ocorrencia in ocorrencias:

            print(
                f"ID: {ocorrencia['occurrence_id']}"
            )

            print(
                f"Nome: {ocorrencia['name']}"
            )

            print(
                f"Similaridade: "
                f"{float(ocorrencia['similarity']):.2f}%"
            )

            print(
                f"Câmera: {ocorrencia['camera']}"
            )

            print(
                f"Frame: {ocorrencia['frame_path']}"
            )

            print(
                f"Referência: "
                f"{ocorrencia['face_reference']}"
            )

            print("----------------------------------------")
