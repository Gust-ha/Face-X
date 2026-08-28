import threading
import time
from pathlib import Path
from queue import Empty, Full, Queue

import cv2
import face_recognition

from central.ocorrencias import reconhecer_e_registrar_ocorrencia
from central.reconhecimento import (
    carregar_participantes,
    reconhecer_encoding,
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

CAMERA_ID = 1

CAMERAS_DISPONIVEIS = [
    {
        "nome": "Integrated_Webcam_HD",
        "device": "/dev/video0",
    },
    {
        "nome": "Web Camera (USB)",
        "device": "/dev/video2",
    },
]


# ============================================================
# DETECÇÃO FACIAL
# ============================================================

ESCALA_DETECCAO = 0.5

INTERVALO_DETECCAO = 0.35

UPSAMPLE = 0

MODELO_DETECCAO = "hog"


# ============================================================
# RECONHECIMENTO
# ============================================================

TOLERANCIA_RECONHECIMENTO = 0.60

# Tempo mínimo entre tentativas de reconhecimento.
#
# A câmera pode detectar rostos várias vezes por segundo,
# mas o reconhecimento pesado será executado com menor
# frequência.
INTERVALO_RECONHECIMENTO = 1.5

# Largura máxima utilizada para calcular o encoding.
#
# Reduz bastante o custo do face_encodings sem alterar
# significativamente o funcionamento para rostos próximos
# da câmera.
LARGURA_MAX_ENCODING = 240


# ============================================================
# OCORRÊNCIAS
# ============================================================

INTERVALO_NOVA_OCORRENCIA = 5.0

CAPTURES_DIR = Path("captures")


# ============================================================
# ESTADO GLOBAL
# ============================================================

executando = True

frame_para_processar = None

localizacoes_rosto = []

resultado_reconhecimento = None

participantes_cache = []

ultima_ocorrencia = {}

ultimo_reconhecimento = 0.0

reconhecimento_em_execucao = False


# ============================================================
# LOCKS
# ============================================================

lock_frame = threading.Lock()

lock_resultado = threading.Lock()

lock_reconhecimento = threading.Lock()

lock_ocorrencia = threading.Lock()


# ============================================================
# FILA DE RECONHECIMENTO
# ============================================================

# Apenas UM reconhecimento pode ficar aguardando.
#
# Se o reconhecimento estiver ocupado, o novo frame é
# descartado. Isso evita acumular trabalho.
fila_reconhecimento = Queue(maxsize=1)


# ============================================================
# SELEÇÃO DA CÂMERA
# ============================================================

def selecionar_camera():
    print()
    print("========================================")
    print("X-FACE - SELEÇÃO DE CÂMERA")
    print("========================================")

    for indice, camera in enumerate(CAMERAS_DISPONIVEIS):
        print(
            f"[{indice}] "
            f"{camera['nome']} "
            f"-> {camera['device']}"
        )

    print()

    while True:

        escolha = input(
            "Selecione a câmera [0-1]: "
        ).strip()

        try:
            indice = int(escolha)
        except ValueError:
            print(
                "Digite somente o número da câmera."
            )
            continue

        if 0 <= indice < len(CAMERAS_DISPONIVEIS):

            camera = CAMERAS_DISPONIVEIS[indice]

            print()
            print(
                f"Câmera selecionada: "
                f"{camera['nome']}"
            )

            print(
                f"Dispositivo: "
                f"{camera['device']}"
            )

            return camera["device"]

        print(
            "Opção inválida."
        )


# ============================================================
# ABERTURA DA CÂMERA
# ============================================================

def abrir_camera(device):

    camera = cv2.VideoCapture(
        device,
        cv2.CAP_V4L2,
    )

    if not camera.isOpened():

        raise RuntimeError(
            f"Não foi possível abrir a câmera {device}."
        )

    # Tenta diminuir o buffer interno.
    try:
        camera.set(
            cv2.CAP_PROP_BUFFERSIZE,
            1,
        )
    except Exception:
        pass

    # Resolução moderada.
    #
    # Isso ajuda bastante no desempenho do HOG.
    try:
        camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            640,
        )

        camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            480,
        )
    except Exception:
        pass

    return camera


# ============================================================
# DETECÇÃO FACIAL
# ============================================================

def detectar_rostos(frame):

    if frame is None:
        return []

    if len(frame.shape) != 3:
        return []

    altura, largura = frame.shape[:2]

    largura_reduzida = int(
        largura * ESCALA_DETECCAO
    )

    altura_reduzida = int(
        altura * ESCALA_DETECCAO
    )

    if (
        largura_reduzida <= 0
        or altura_reduzida <= 0
    ):
        return []

    frame_reduzido = cv2.resize(
        frame,
        (
            largura_reduzida,
            altura_reduzida,
        ),
        interpolation=cv2.INTER_AREA,
    )

    frame_rgb = cv2.cvtColor(
        frame_reduzido,
        cv2.COLOR_BGR2RGB,
    )

    locais = face_recognition.face_locations(
        frame_rgb,
        number_of_times_to_upsample=UPSAMPLE,
        model=MODELO_DETECCAO,
    )

    if not locais:
        return []

    fator = 1.0 / ESCALA_DETECCAO

    locais_originais = []

    for top, right, bottom, left in locais:

        top = int(top * fator)
        right = int(right * fator)
        bottom = int(bottom * fator)
        left = int(left * fator)

        top = max(
            0,
            min(top, altura - 1),
        )

        bottom = max(
            0,
            min(bottom, altura - 1),
        )

        left = max(
            0,
            min(left, largura - 1),
        )

        right = max(
            0,
            min(right, largura - 1),
        )

        if (
            right > left
            and bottom > top
        ):
            locais_originais.append(
                (
                    top,
                    right,
                    bottom,
                    left,
                )
            )

    return locais_originais


# ============================================================
# PREPARAÇÃO DO ROSTO
# ============================================================

def preparar_rosto_para_encoding(
    frame,
    localizacao,
):
    """
    Recorta somente o rosto.

    Depois reduz o tamanho do recorte antes do
    cálculo do encoding.

    Isso evita executar reconhecimento pesado
    sobre o frame inteiro.
    """

    if frame is None:
        return None

    top, right, bottom, left = localizacao

    altura, largura = frame.shape[:2]

    top = max(
        0,
        min(top, altura),
    )

    bottom = max(
        0,
        min(bottom, altura),
    )

    left = max(
        0,
        min(left, largura),
    )

    right = max(
        0,
        min(right, largura),
    )

    if (
        bottom <= top
        or right <= left
    ):
        return None

    rosto = frame[
        top:bottom,
        left:right,
    ]

    if rosto.size == 0:
        return None

    altura_rosto, largura_rosto = rosto.shape[:2]

    if largura_rosto > LARGURA_MAX_ENCODING:

        escala = (
            LARGURA_MAX_ENCODING
            / float(largura_rosto)
        )

        nova_largura = LARGURA_MAX_ENCODING

        nova_altura = max(
            1,
            int(altura_rosto * escala),
        )

        rosto = cv2.resize(
            rosto,
            (
                nova_largura,
                nova_altura,
            ),
            interpolation=cv2.INTER_AREA,
        )

    return rosto


# ============================================================
# RECONHECIMENTO
# ============================================================

def reconhecer_rosto(
    frame,
    localizacao,
):
    """
    Executa o reconhecimento somente no rosto
    detectado.

    Não procura outro rosto dentro do recorte.
    """

    rosto = preparar_rosto_para_encoding(
        frame,
        localizacao,
    )

    if rosto is None:
        return None

    rosto_rgb = cv2.cvtColor(
        rosto,
        cv2.COLOR_BGR2RGB,
    )

    altura, largura = rosto_rgb.shape[:2]

    if (
        largura < 20
        or altura < 20
    ):
        return None

    # O rosto já foi localizado pelo HOG.
    #
    # Portanto informamos diretamente a região inteira
    # para evitar uma nova busca facial.
    localizacao_interna = (
        0,
        largura,
        altura,
        0,
    )

    encodings = face_recognition.face_encodings(
        rosto_rgb,
        known_face_locations=[
            localizacao_interna
        ],
        num_jitters=1,
        model="small",
    )

    if not encodings:
        return None

    encoding = encodings[0]

    resultado = reconhecer_encoding(
        encoding,
        participantes=participantes_cache,
        tolerancia=TOLERANCIA_RECONHECIMENTO,
    )

    if resultado is None:
        return {
            "matched": False,
            "localizacao": localizacao,
        }

    return {
        "matched": True,
        "localizacao": localizacao,
        "resultado": resultado,
    }


# ============================================================
# SALVAR FRAME
# ============================================================

def salvar_frame_ocorrencia(frame):

    CAPTURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    caminho = (
        CAPTURES_DIR
        / (
            f"captura_{timestamp}_"
            f"{time.time_ns()}.jpg"
        )
    )

    sucesso = cv2.imwrite(
        str(caminho),
        frame,
    )

    if not sucesso:

        raise RuntimeError(
            f"Não foi possível salvar "
            f"o frame: {caminho}"
        )

    return caminho


# ============================================================
# CONTROLE DE OCORRÊNCIAS
# ============================================================

def pode_registrar_ocorrencia(
    participant_id,
):
    agora = time.time()

    with lock_ocorrencia:

        ultima = ultima_ocorrencia.get(
            participant_id
        )

        if ultima is not None:

            if (
                agora - ultima
                < INTERVALO_NOVA_OCORRENCIA
            ):
                return False

        ultima_ocorrencia[
            participant_id
        ] = agora

        return True


# ============================================================
# THREAD DE RECONHECIMENTO
# ============================================================

def trabalhador_reconhecimento():

    global executando
    global resultado_reconhecimento
    global ultimo_reconhecimento
    global reconhecimento_em_execucao

    while executando:

        try:

            item = fila_reconhecimento.get(
                timeout=0.2
            )

        except Empty:

            continue

        if item is None:

            continue

        frame, localizacao = item

        with lock_reconhecimento:

            reconhecimento_em_execucao = True

        try:

            resultado = reconhecer_rosto(
                frame,
                localizacao,
            )

            if resultado is None:
                continue

            if not resultado.get(
                "matched",
                False,
            ):

                with lock_reconhecimento:

                    resultado_reconhecimento = {
                        "matched": False,
                        "localizacao": localizacao,
                    }

                continue

            participante = resultado[
                "resultado"
            ]

            with lock_reconhecimento:

                resultado_reconhecimento = {
                    "matched": True,
                    "localizacao": localizacao,
                    "name": participante["name"],
                    "similarity": participante[
                        "similarity"
                    ],
                }

                ultimo_reconhecimento = (
                    time.time()
                )

            participant_id = participante["id"]

            print()
            print("----------------------------------------")
            print("RECONHECIMENTO FACIAL")
            print("----------------------------------------")
            print(
                f"Pessoa: "
                f"{participante['name']}"
            )
            print(
                f"Similaridade: "
                f"{participante['similarity']:.2f}%"
            )

            # ------------------------------------------------
            # Evita ocorrência duplicada.
            # ------------------------------------------------

            if not pode_registrar_ocorrencia(
                participant_id
            ):

                print(
                    "[OCORRÊNCIAS] "
                    "Ocorrência duplicada."
                )

                continue

            # ------------------------------------------------
            # Salva o frame somente quando existe
            # reconhecimento válido.
            # ------------------------------------------------

            caminho = salvar_frame_ocorrencia(
                frame
            )

            print(
                f"Frame: {caminho}"
            )

            print(
                "[OCORRÊNCIAS] "
                "Enviando reconhecimento..."
            )

            # ------------------------------------------------
            # Integração com central.ocorrencias
            # ------------------------------------------------

            try:

                ocorrencia = (
                    reconhecer_e_registrar_ocorrencia(
                        imagem_path=str(caminho),
                        camera_id=CAMERA_ID,
                        tolerancia=(
                            TOLERANCIA_RECONHECIMENTO
                        ),
                    )
                )

            except Exception as erro:

                print(
                    "[OCORRÊNCIAS] "
                    f"Erro ao registrar: {erro}"
                )

                continue

            if ocorrencia is None:

                print(
                    "[OCORRÊNCIAS] "
                    "Nenhuma ocorrência criada."
                )

                continue

            if ocorrencia.get(
                "duplicate"
            ):

                print(
                    "[OCORRÊNCIAS] "
                    "Ocorrência duplicada."
                )

                print(
                    "Occurrence ID: "
                    f"{ocorrencia.get('occurrence_id')}"
                )

                continue

            print()
            print("========================================")
            print("NOVA OCORRÊNCIA REGISTRADA")
            print("========================================")

            print(
                "Occurrence ID: "
                f"{ocorrencia.get('occurrence_id')}"
            )

            print(
                "Pessoa: "
                f"{ocorrencia.get('name')}"
            )

            print(
                "Similaridade: "
                f"{ocorrencia.get('similarity', 0):.2f}%"
            )

            print(
                "Status: "
                f"{ocorrencia.get('occurrence_status')}"
            )

            print(
                "Frame: "
                f"{ocorrencia.get('frame_path')}"
            )

            print("========================================")
            print()

        except Exception as erro:

            print(
                "[RECONHECIMENTO] "
                f"Erro: {erro}"
            )

        finally:

            with lock_reconhecimento:

                reconhecimento_em_execucao = False

            try:

                fila_reconhecimento.task_done()

            except Exception:

                pass


# ============================================================
# THREAD DE DETECÇÃO
# ============================================================

def trabalhador_deteccao():

    global executando
    global frame_para_processar
    global localizacoes_rosto

    ultimo_processamento = 0.0

    while executando:

        agora = time.time()

        if (
            agora - ultimo_processamento
            < INTERVALO_DETECCAO
        ):

            time.sleep(0.01)

            continue

        ultimo_processamento = agora

        with lock_frame:

            if frame_para_processar is None:

                frame = None

            else:

                frame = frame_para_processar.copy()

        if frame is None:

            continue

        try:

            locais = detectar_rostos(
                frame
            )

            with lock_resultado:

                localizacoes_rosto = locais

            if not locais:

                continue

            # ------------------------------------------------
            # Controla a frequência do reconhecimento.
            # ------------------------------------------------

            with lock_reconhecimento:

                tempo_desde_reconhecimento = (
                    time.time()
                    - ultimo_reconhecimento
                )

                ocupado = (
                    reconhecimento_em_execucao
                )

            if ocupado:

                continue

            if (
                tempo_desde_reconhecimento
                < INTERVALO_RECONHECIMENTO
            ):

                continue

            # ------------------------------------------------
            # Usa somente o primeiro rosto detectado.
            # ------------------------------------------------

            localizacao = locais[0]

            try:

                fila_reconhecimento.put_nowait(
                    (
                        frame,
                        localizacao,
                    )
                )

            except Full:

                # O reconhecimento anterior ainda
                # está aguardando/processando.
                pass

        except Exception as erro:

            print(
                "[DETECÇÃO] "
                f"Erro: {erro}"
            )

            with lock_resultado:

                localizacoes_rosto = []


# ============================================================
# DESENHO
# ============================================================

def desenhar_deteccoes(
    frame,
    locais,
    resultado,
):
    for localizacao in locais:

        top, right, bottom, left = (
            localizacao
        )

        cor = (
            0,
            255,
            0,
        )

        texto = "Rosto detectado"

        if (
            resultado is not None
            and resultado.get("matched")
            and resultado.get("localizacao")
            == localizacao
        ):

            cor = (
                0,
                0,
                255,
            )

            nome = resultado.get(
                "name"
            )

            if nome:

                texto = (
                    f"RECONHECIDO: "
                    f"{nome}"
                )

            else:

                texto = "RECONHECIDO"

        cv2.rectangle(
            frame,
            (left, top),
            (right, bottom),
            cor,
            2,
        )

        texto_y = top - 10

        if texto_y < 20:

            texto_y = bottom + 25

        cv2.putText(
            frame,
            texto,
            (
                left,
                texto_y,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            cor,
            2,
            cv2.LINE_AA,
        )


# ============================================================
# STATUS
# ============================================================

def desenhar_status(
    frame,
    fps,
    camera_device,
):

    texto = (
        f"X-Face | "
        f"Camera {CAMERA_ID} | "
        f"FPS: {fps:.1f}"
    )

    cv2.putText(
        frame,
        texto,
        (15, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (
            255,
            255,
            255,
        ),
        2,
        cv2.LINE_AA,
    )

    texto_camera = (
        f"Dispositivo: "
        f"{camera_device}"
    )

    cv2.putText(
        frame,
        texto_camera,
        (15, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        (
            255,
            255,
            255,
        ),
        1,
        cv2.LINE_AA,
    )


# ============================================================
# EXECUÇÃO
# ============================================================

def executar_camera():

    global executando
    global frame_para_processar
    global localizacoes_rosto
    global resultado_reconhecimento
    global participantes_cache
    global ultimo_reconhecimento
    global reconhecimento_em_execucao

    # --------------------------------------------------------
    # Carrega participantes uma única vez.
    # --------------------------------------------------------

    try:

        participantes_cache = (
            carregar_participantes()
        )

        print(
            f"Participantes carregados: "
            f"{len(participantes_cache)}"
        )

    except Exception as erro:

        print(
            "[BANCO] Erro ao carregar "
            f"participantes: {erro}"
        )

        participantes_cache = []

    # --------------------------------------------------------
    # Seleciona câmera.
    # --------------------------------------------------------

    camera_device = selecionar_camera()

    camera = abrir_camera(
        camera_device
    )

    executando = True

    # --------------------------------------------------------
    # Limpa estado.
    # --------------------------------------------------------

    with lock_frame:

        frame_para_processar = None

    with lock_resultado:

        localizacoes_rosto = []

    with lock_reconhecimento:

        resultado_reconhecimento = None

        ultimo_reconhecimento = 0.0

        reconhecimento_em_execucao = False

    # --------------------------------------------------------
    # Threads.
    # --------------------------------------------------------

    thread_deteccao = threading.Thread(
        target=trabalhador_deteccao,
        daemon=True,
        name="XFace-Deteccao",
    )

    thread_reconhecimento = threading.Thread(
        target=trabalhador_reconhecimento,
        daemon=True,
        name="XFace-Reconhecimento",
    )

    thread_deteccao.start()

    thread_reconhecimento.start()

    # --------------------------------------------------------
    # Terminal.
    # --------------------------------------------------------

    print()
    print("========================================")
    print("X-FACE - MONITORAMENTO DA CÂMERA")
    print("========================================")
    print(
        f"Câmera lógica: {CAMERA_ID}"
    )
    print(
        f"Dispositivo: {camera_device}"
    )
    print(
        "Detecção facial: HOG"
    )
    print(
        "Escala de detecção: 50%"
    )
    print(
        "Reconhecimento: thread separada"
    )
    print(
        "Reconhecimento limitado por intervalo"
    )
    print(
        "Ocorrências: central.ocorrencias"
    )
    print(
        "Pressione Q ou ESC para sair."
    )
    print()

    contador_frames = 0

    inicio_fps = time.time()

    fps = 0.0

    try:

        while True:

            sucesso, frame = camera.read()

            if not sucesso:

                print(
                    "Erro ao capturar "
                    "frame da câmera."
                )

                break

            # ------------------------------------------------
            # O detector recebe somente o último frame.
            # ------------------------------------------------

            with lock_frame:

                frame_para_processar = (
                    frame.copy()
                )

            # ------------------------------------------------
            # Obtém resultados sem bloquear.
            # ------------------------------------------------

            with lock_resultado:

                locais = list(
                    localizacoes_rosto
                )

            with lock_reconhecimento:

                resultado = (
                    resultado_reconhecimento
                )

            # ------------------------------------------------
            # Frame exclusivo para exibição.
            # ------------------------------------------------

            frame_exibicao = frame.copy()

            desenhar_deteccoes(
                frame_exibicao,
                locais,
                resultado,
            )

            # ------------------------------------------------
            # FPS.
            # ------------------------------------------------

            contador_frames += 1

            agora = time.time()

            intervalo_fps = (
                agora - inicio_fps
            )

            if intervalo_fps >= 1.0:

                fps = (
                    contador_frames
                    / intervalo_fps
                )

                contador_frames = 0

                inicio_fps = agora

            desenhar_status(
                frame_exibicao,
                fps,
                camera_device,
            )

            # ------------------------------------------------
            # Exibição.
            # ------------------------------------------------

            cv2.imshow(
                "X-Face - Camera",
                frame_exibicao,
            )

            tecla = (
                cv2.waitKey(1)
                & 0xFF
            )

            if tecla in (
                ord("q"),
                ord("Q"),
                27,
            ):

                break

    finally:

        print()
        print(
            "Encerrando monitoramento..."
        )

        executando = False

        with lock_frame:

            frame_para_processar = None

        # ----------------------------------------------------
        # Remove trabalho pendente.
        # ----------------------------------------------------

        try:

            while True:

                fila_reconhecimento.get_nowait()

                fila_reconhecimento.task_done()

        except Empty:

            pass

        # ----------------------------------------------------
        # Libera câmera.
        # ----------------------------------------------------

        camera.release()

        # ----------------------------------------------------
        # Fecha OpenCV.
        # ----------------------------------------------------

        cv2.destroyAllWindows()

        # ----------------------------------------------------
        # Aguarda threads por pouco tempo.
        # ----------------------------------------------------

        thread_deteccao.join(
            timeout=1.0
        )

        thread_reconhecimento.join(
            timeout=1.0
        )

        print(
            "Câmera encerrada."
        )


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":
    executar_camera()
