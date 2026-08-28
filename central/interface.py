import os
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk, ImageOps
from sqlalchemy import text

from database.connection import engine

from central.ocorrencias import (
    buscar_ocorrencias_pendentes,
    confirmar_ocorrencia,
    descartar_ocorrencia,
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

LARGURA_JANELA = 1280
ALTURA_JANELA = 720

INTERVALO_ATUALIZACAO_MS = 1000

LARGURA_IMAGEM = 330
ALTURA_IMAGEM = 230


# ============================================================
# CORES — TEMA ESCURO
# ============================================================

COR_FUNDO = "#111827"
COR_PAINEL = "#1f2937"
COR_PAINEL_2 = "#111827"
COR_BORDA = "#374151"

COR_TEXTO = "#f9fafb"
COR_TEXTO_SECUNDARIO = "#9ca3af"

COR_VERDE = "#22c55e"
COR_VERMELHO = "#ef4444"
COR_AZUL = "#3b82f6"
COR_AMARELO = "#f59e0b"


# ============================================================
# ESTADO
# ============================================================

ocorrencias_atuais = []
ocorrencia_selecionada = None

imagem_referencia_tk = None
imagem_frame_tk = None

atualizacao_agendada = None
encerrando = False


# ============================================================
# RAIZ DO PROJETO
# ============================================================

RAIZ_PROJETO = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ============================================================
# CAMINHO ABSOLUTO
# ============================================================

def caminho_absoluto(caminho):
    """
    Converte caminhos relativos do banco em caminhos absolutos.

    Exemplos aceitos:

        captures/foto.jpg

    ou:

        /home/usuario/X-Face/captures/foto.jpg
    """

    if not caminho:
        return None

    caminho = str(caminho).strip()

    if not caminho:
        return None

    if os.path.isabs(caminho):
        return caminho

    return os.path.join(
        RAIZ_PROJETO,
        caminho
    )


# ============================================================
# IMAGEM — SEM CORTE
# ============================================================

def carregar_imagem(caminho):
    """
    Carrega uma imagem e encaixa exatamente dentro da área
    disponível, preservando a proporção.

    NÃO utiliza crop.

    A imagem inteira sempre permanece visível.
    """

    caminho = caminho_absoluto(caminho)

    if not caminho:
        return None

    if not os.path.isfile(caminho):
        print(
            "[INTERFACE] Imagem não encontrada:",
            caminho
        )
        return None

    try:
        imagem = Image.open(caminho)
        imagem = imagem.convert("RGB")

        # ----------------------------------------------------
        # ImageOps.contain:
        #
        # - mantém proporção;
        # - não corta;
        # - não distorce;
        # - encaixa a imagem inteira na área.
        # ----------------------------------------------------

        imagem = ImageOps.contain(
            imagem,
            (
                LARGURA_IMAGEM,
                ALTURA_IMAGEM
            ),
            method=Image.Resampling.LANCZOS
        )

        # ----------------------------------------------------
        # Cria uma área fixa.
        #
        # Isso evita que o Tkinter redimensione ou corte
        # a imagem quando o painel muda de tamanho.
        # ----------------------------------------------------

        tela = Image.new(
            "RGB",
            (
                LARGURA_IMAGEM,
                ALTURA_IMAGEM
            ),
            "#0b1220"
        )

        x = (
            LARGURA_IMAGEM
            - imagem.width
        ) // 2

        y = (
            ALTURA_IMAGEM
            - imagem.height
        ) // 2

        tela.paste(
            imagem,
            (
                x,
                y
            )
        )

        return ImageTk.PhotoImage(
            tela
        )

    except Exception as erro:

        print(
            "[INTERFACE] Erro ao carregar imagem:",
            caminho,
            erro
        )

        return None


# ============================================================
# BUSCAR FOTO DE REFERÊNCIA
# ============================================================

def buscar_face_reference(occurrence_id):
    """
    Fallback para versões de ocorrencias.py que ainda não
    retornam face_reference em buscar_ocorrencias_pendentes().
    """

    if occurrence_id is None:
        return None

    query = text(
        """
        SELECT
            p.face_reference
        FROM occurrences o
        JOIN participants p
            ON p.id = o.participant_id
        WHERE o.id = :occurrence_id
        """
    )

    try:

        with engine.connect() as connection:

            resultado = connection.execute(
                query,
                {
                    "occurrence_id": occurrence_id
                }
            ).mappings().first()

        if resultado is None:
            return None

        return resultado.get(
            "face_reference"
        )

    except Exception as erro:

        print(
            "[INTERFACE] "
            "Erro ao buscar foto de referência:",
            erro
        )

        return None


# ============================================================
# MOSTRAR FOTO DE REFERÊNCIA
# ============================================================

def mostrar_imagem_referencia(caminho):
    global imagem_referencia_tk

    imagem_referencia_tk = carregar_imagem(
        caminho
    )

    if imagem_referencia_tk is None:

        referencia_label.config(
            image="",
            text=(
                "Imagem de referência\n"
                "não encontrada"
            ),
            fg=COR_TEXTO_SECUNDARIO
        )

        referencia_label.image = None

        return

    referencia_label.config(
        image=imagem_referencia_tk,
        text=""
    )

    referencia_label.image = (
        imagem_referencia_tk
    )


# ============================================================
# MOSTRAR FRAME
# ============================================================

def mostrar_imagem_frame(caminho):
    global imagem_frame_tk

    imagem_frame_tk = carregar_imagem(
        caminho
    )

    if imagem_frame_tk is None:

        frame_label.config(
            image="",
            text=(
                "Frame da ocorrência\n"
                "não encontrado"
            ),
            fg=COR_TEXTO_SECUNDARIO
        )

        frame_label.image = None

        return

    frame_label.config(
        image=imagem_frame_tk,
        text=""
    )

    frame_label.image = (
        imagem_frame_tk
    )


# ============================================================
# LIMPAR DETALHES
# ============================================================

def limpar_detalhes():

    global ocorrencia_selecionada
    global imagem_referencia_tk
    global imagem_frame_tk

    ocorrencia_selecionada = None

    nome_var.set("-")
    idade_var.set("-")
    status_var.set("-")
    crime_var.set("-")
    similaridade_var.set("-")
    camera_var.set("-")
    local_var.set("-")
    ocorrencia_status_var.set("-")
    detected_at_var.set("-")

    referencia_label.config(
        image="",
        text="Nenhuma ocorrência selecionada",
        fg=COR_TEXTO_SECUNDARIO
    )

    frame_label.config(
        image="",
        text="Nenhuma ocorrência selecionada",
        fg=COR_TEXTO_SECUNDARIO
    )

    imagem_referencia_tk = None
    imagem_frame_tk = None

    referencia_label.image = None
    frame_label.image = None


# ============================================================
# MOSTRAR OCORRÊNCIA
# ============================================================

def mostrar_ocorrencia(ocorrencia):

    global ocorrencia_selecionada

    ocorrencia_selecionada = ocorrencia

    nome_var.set(
        str(
            ocorrencia.get(
                "name",
                "-"
            )
        )
    )

    idade = ocorrencia.get(
        "age"
    )

    if idade is None:
        idade_var.set("-")
    else:
        idade_var.set(
            f"{idade} anos"
        )

    status_var.set(
        str(
            ocorrencia.get(
                "status",
                "-"
            )
        )
    )

    crime = ocorrencia.get(
        "crime"
    )

    crime_var.set(
        str(crime)
        if crime
        else "Nenhuma informação"
    )

    similaridade = ocorrencia.get(
        "similarity"
    )

    try:

        similaridade_var.set(
            f"{float(similaridade):.2f}%"
        )

    except (
        TypeError,
        ValueError
    ):

        similaridade_var.set("-")

    camera_var.set(
        str(
            ocorrencia.get(
                "camera",
                "-"
            )
        )
    )

    local_var.set(
        str(
            ocorrencia.get(
                "location",
                "-"
            )
        )
    )

    ocorrencia_status_var.set(
        str(
            ocorrencia.get(
                "occurrence_status",
                "PENDING"
            )
        )
    )

    detected_at_var.set(
        str(
            ocorrencia.get(
                "detected_at",
                "-"
            )
        )
    )

    # --------------------------------------------------------
    # FOTO DE REFERÊNCIA
    # --------------------------------------------------------

    face_reference = ocorrencia.get(
        "face_reference"
    )

    if not face_reference:

        face_reference = (
            buscar_face_reference(
                ocorrencia.get(
                    "occurrence_id"
                )
            )
        )

    mostrar_imagem_referencia(
        face_reference
    )

    # --------------------------------------------------------
    # FRAME DA CÂMERA
    # --------------------------------------------------------

    mostrar_imagem_frame(
        ocorrencia.get(
            "frame_path"
        )
    )


# ============================================================
# SELEÇÃO PELA LISTA
# ============================================================

def selecionar_ocorrencia(event=None):

    global ocorrencia_selecionada

    selecao = lista.curselection()

    if not selecao:
        return

    indice = selecao[0]

    if indice < 0:
        return

    if indice >= len(
        ocorrencias_atuais
    ):
        return

    ocorrencia_selecionada = (
        ocorrencias_atuais[indice]
    )

    mostrar_ocorrencia(
        ocorrencia_selecionada
    )


# ============================================================
# ATUALIZAÇÃO DA LISTA
# ============================================================

def atualizar_lista(
    ocorrencias,
    id_selecionado=None
):
    """
    Atualiza somente a lista visual.

    A ocorrência selecionada é preservada quando possível.
    """

    lista.delete(
        0,
        tk.END
    )

    indice_selecionado = None

    for indice, ocorrencia in enumerate(
        ocorrencias
    ):

        occurrence_id = (
            ocorrencia.get(
                "occurrence_id",
                "-"
            )
        )

        nome = (
            ocorrencia.get(
                "name",
                "-"
            )
        )

        similaridade = (
            ocorrencia.get(
                "similarity"
            )
        )

        try:

            similaridade_texto = (
                f"{float(similaridade):.2f}%"
            )

        except (
            TypeError,
            ValueError
        ):

            similaridade_texto = "-"

        camera = (
            ocorrencia.get(
                "camera",
                "-"
            )
        )

        texto = (
            f"ID {occurrence_id}  |  "
            f"{nome}  |  "
            f"{similaridade_texto}  |  "
            f"{camera}"
        )

        lista.insert(
            tk.END,
            texto
        )

        if (
            id_selecionado is not None
            and occurrence_id == id_selecionado
        ):
            indice_selecionado = indice

    if not ocorrencias:
        limpar_detalhes()
        return

    if indice_selecionado is None:

        # Nova ocorrência ou ocorrência selecionada
        # que já não existe mais.
        indice_selecionado = 0

    lista.selection_clear(
        0,
        tk.END
    )

    lista.selection_set(
        indice_selecionado
    )

    lista.activate(
        indice_selecionado
    )

    lista.see(
        indice_selecionado
    )

    selecionar_ocorrencia()


# ============================================================
# ATUALIZAÇÃO AUTOMÁTICA
# ============================================================

def atualizar_central():

    global ocorrencias_atuais
    global atualizacao_agendada

    if encerrando:
        return

    # --------------------------------------------------------
    # Guarda o ID que estava selecionado.
    # --------------------------------------------------------

    id_selecionado = None

    if ocorrencia_selecionada is not None:

        id_selecionado = (
            ocorrencia_selecionada.get(
                "occurrence_id"
            )
        )

    try:

        novas_ocorrencias = (
            buscar_ocorrencias_pendentes()
        )

        ocorrencias_atuais = list(
            novas_ocorrencias
        )

        # ----------------------------------------------------
        # Atualiza contador.
        # ----------------------------------------------------

        quantidade = len(
            ocorrencias_atuais
        )

        if quantidade == 0:

            contador_var.set(
                "0 ocorrências ativas"
            )

            status_bar_var.set(
                "Aguardando novas ocorrências..."
            )

        elif quantidade == 1:

            contador_var.set(
                "1 ocorrência ativa"
            )

            status_bar_var.set(
                "Central conectada — "
                "monitoramento ativo"
            )

        else:

            contador_var.set(
                f"{quantidade} ocorrências ativas"
            )

            status_bar_var.set(
                "Central conectada — "
                "monitoramento ativo"
            )

        # ----------------------------------------------------
        # Atualiza lista.
        # ----------------------------------------------------

        atualizar_lista(
            ocorrencias_atuais,
            id_selecionado
        )

    except Exception as erro:

        print(
            "[INTERFACE] "
            "Erro ao consultar ocorrências:",
            erro
        )

        status_bar_var.set(
            "Erro ao consultar PostgreSQL — "
            "tentando novamente..."
        )

    # --------------------------------------------------------
    # Agenda próxima atualização.
    # --------------------------------------------------------

    if not encerrando:

        atualizacao_agendada = root.after(
            INTERVALO_ATUALIZACAO_MS,
            atualizar_central
        )


# ============================================================
# CONFIRMAR OCORRÊNCIA
# ============================================================

def confirmar():

    if ocorrencia_selecionada is None:

        messagebox.showwarning(
            "Nenhuma ocorrência",
            "Selecione uma ocorrência na lista."
        )

        return

    occurrence_id = (
        ocorrencia_selecionada.get(
            "occurrence_id"
        )
    )

    if occurrence_id is None:
        return

    try:

        confirmar_ocorrencia(
            occurrence_id
        )

        print(
            "[CENTRAL] "
            f"Ocorrência {occurrence_id} "
            "confirmada."
        )

        status_bar_var.set(
            f"Ocorrência {occurrence_id} "
            "confirmada."
        )

        atualizar_central()

    except Exception as erro:

        messagebox.showerror(
            "Erro",
            (
                "Não foi possível confirmar "
                "a ocorrência.\n\n"
                f"{erro}"
            )
        )


# ============================================================
# DESCARTAR OCORRÊNCIA
# ============================================================

def descartar():

    if ocorrencia_selecionada is None:

        messagebox.showwarning(
            "Nenhuma ocorrência",
            "Selecione uma ocorrência na lista."
        )

        return

    occurrence_id = (
        ocorrencia_selecionada.get(
            "occurrence_id"
        )
    )

    if occurrence_id is None:
        return

    resposta = messagebox.askyesno(
        "Descartar ocorrência",
        (
            "Deseja realmente descartar "
            f"a ocorrência {occurrence_id}?"
        )
    )

    if not resposta:
        return

    try:

        descartar_ocorrencia(
            occurrence_id
        )

        print(
            "[CENTRAL] "
            f"Ocorrência {occurrence_id} "
            "descartada."
        )

        status_bar_var.set(
            f"Ocorrência {occurrence_id} "
            "descartada."
        )

        atualizar_central()

    except Exception as erro:

        messagebox.showerror(
            "Erro",
            (
                "Não foi possível descartar "
                "a ocorrência.\n\n"
                f"{erro}"
            )
        )


# ============================================================
# FECHAMENTO
# ============================================================

def fechar_central():

    global encerrando
    global atualizacao_agendada

    if encerrando:
        return

    encerrando = True

    # Cancela atualização pendente.
    if atualizacao_agendada is not None:

        try:

            root.after_cancel(
                atualizacao_agendada
            )

        except Exception:
            pass

        atualizacao_agendada = None

    try:
        root.destroy()

    except Exception:
        pass


# ============================================================
# JANELA PRINCIPAL
# ============================================================

root = tk.Tk()

root.title(
    "X-FACE — CENTRAL DE VERIFICAÇÃO"
)

root.geometry(
    f"{LARGURA_JANELA}x{ALTURA_JANELA}"
)

root.minsize(
    1100,
    650
)

root.configure(
    bg=COR_FUNDO
)

root.protocol(
    "WM_DELETE_WINDOW",
    fechar_central
)

root.bind(
    "<Escape>",
    lambda event: fechar_central()
)


# ============================================================
# VARIÁVEIS DA INTERFACE
# ============================================================

nome_var = tk.StringVar(
    value="-"
)

idade_var = tk.StringVar(
    value="-"
)

status_var = tk.StringVar(
    value="-"
)

crime_var = tk.StringVar(
    value="-"
)

similaridade_var = tk.StringVar(
    value="-"
)

camera_var = tk.StringVar(
    value="-"
)

local_var = tk.StringVar(
    value="-"
)

ocorrencia_status_var = tk.StringVar(
    value="-"
)

detected_at_var = tk.StringVar(
    value="-"
)

contador_var = tk.StringVar(
    value="0 ocorrências ativas"
)

status_bar_var = tk.StringVar(
    value="Inicializando Central..."
)


# ============================================================
# CABEÇALHO
# ============================================================

cabecalho = tk.Frame(
    root,
    bg=COR_FUNDO
)

cabecalho.pack(
    fill="x",
    padx=20,
    pady=(15, 8)
)


titulo = tk.Label(
    cabecalho,
    text="X-FACE",
    bg=COR_FUNDO,
    fg=COR_TEXTO,
    font=(
        "DejaVu Sans",
        22,
        "bold"
    )
)

titulo.pack(
    side="left"
)


subtitulo = tk.Label(
    cabecalho,
    text="  CENTRAL DE VERIFICAÇÃO",
    bg=COR_FUNDO,
    fg=COR_TEXTO_SECUNDARIO,
    font=(
        "DejaVu Sans",
        13
    )
)

subtitulo.pack(
    side="left",
    pady=(5, 0)
)


contador_label = tk.Label(
    cabecalho,
    textvariable=contador_var,
    bg=COR_FUNDO,
    fg=COR_AZUL,
    font=(
        "DejaVu Sans",
        11,
        "bold"
    )
)

contador_label.pack(
    side="right",
    pady=(7, 0)
)


# ============================================================
# ÁREA PRINCIPAL
# ============================================================

principal = tk.Frame(
    root,
    bg=COR_FUNDO
)

principal.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=5
)


# ============================================================
# PAINEL ESQUERDO — OCORRÊNCIAS
# ============================================================

painel_lista = tk.Frame(
    principal,
    bg=COR_PAINEL,
    highlightbackground=COR_BORDA,
    highlightthickness=1,
    width=390
)

painel_lista.pack(
    side="left",
    fill="y",
    padx=(0, 10)
)

painel_lista.pack_propagate(
    False
)


lista_titulo = tk.Label(
    painel_lista,
    text="OCORRÊNCIAS ATIVAS",
    bg=COR_PAINEL,
    fg=COR_TEXTO,
    font=(
        "DejaVu Sans",
        11,
        "bold"
    )
)

lista_titulo.pack(
    anchor="w",
    padx=14,
    pady=(14, 8)
)


lista_frame = tk.Frame(
    painel_lista,
    bg=COR_PAINEL
)

lista_frame.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=(0, 12)
)


scrollbar = tk.Scrollbar(
    lista_frame
)

scrollbar.pack(
    side="right",
    fill="y"
)


lista = tk.Listbox(
    lista_frame,
    width=39,
    height=25,
    bg=COR_PAINEL_2,
    fg=COR_TEXTO,
    selectbackground=COR_AZUL,
    selectforeground=COR_TEXTO,
    highlightthickness=0,
    borderwidth=0,
    font=(
        "DejaVu Sans",
        9
    ),
    activestyle="none",
    yscrollcommand=scrollbar.set
)

lista.pack(
    side="left",
    fill="both",
    expand=True
)

scrollbar.config(
    command=lista.yview
)

lista.bind(
    "<<ListboxSelect>>",
    selecionar_ocorrencia
)


# ============================================================
# PAINEL DIREITO
# ============================================================

painel_direito = tk.Frame(
    principal,
    bg=COR_FUNDO
)

painel_direito.pack(
    side="left",
    fill="both",
    expand=True
)


# ============================================================
# ÁREA DAS DUAS IMAGENS
# ============================================================

imagens = tk.Frame(
    painel_direito,
    bg=COR_FUNDO
)

imagens.pack(
    fill="x",
    pady=(0, 10)
)


# ============================================================
# FOTO DE REFERÊNCIA
# ============================================================

referencia_container = tk.Frame(
    imagens,
    bg=COR_PAINEL,
    highlightbackground=COR_BORDA,
    highlightthickness=1
)

referencia_container.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(0, 5)
)


tk.Label(
    referencia_container,
    text="FOTO DE REFERÊNCIA",
    bg=COR_PAINEL,
    fg=COR_TEXTO,
    font=(
        "DejaVu Sans",
        10,
        "bold"
    )
).pack(
    anchor="w",
    padx=12,
    pady=(10, 5)
)


referencia_label = tk.Label(
    referencia_container,
    bg=COR_PAINEL_2,
    fg=COR_TEXTO_SECUNDARIO,
    text="Nenhuma ocorrência selecionada",
    font=(
        "DejaVu Sans",
        10
    ),
    width=LARGURA_IMAGEM,
    height=ALTURA_IMAGEM
)

referencia_label.pack(
    padx=10,
    pady=(0, 10)
)


# ============================================================
# FRAME CAPTURADO
# ============================================================

frame_container = tk.Frame(
    imagens,
    bg=COR_PAINEL,
    highlightbackground=COR_BORDA,
    highlightthickness=1
)

frame_container.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(5, 0)
)


tk.Label(
    frame_container,
    text="FRAME CAPTURADO",
    bg=COR_PAINEL,
    fg=COR_TEXTO,
    font=(
        "DejaVu Sans",
        10,
        "bold"
    )
).pack(
    anchor="w",
    padx=12,
    pady=(10, 5)
)


frame_label = tk.Label(
    frame_container,
    bg=COR_PAINEL_2,
    fg=COR_TEXTO_SECUNDARIO,
    text="Nenhuma ocorrência selecionada",
    font=(
        "DejaVu Sans",
        10
    ),
    width=LARGURA_IMAGEM,
    height=ALTURA_IMAGEM
)

frame_label.pack(
    padx=10,
    pady=(0, 10)
)


# ============================================================
# INFORMAÇÕES DO PROCURADO
# ============================================================

informacoes = tk.Frame(
    painel_direito,
    bg=COR_PAINEL,
    highlightbackground=COR_BORDA,
    highlightthickness=1
)

informacoes.pack(
    fill="both",
    expand=True,
    pady=(0, 10)
)


info_titulo = tk.Label(
    informacoes,
    text="INFORMAÇÕES DO PROCURADO",
    bg=COR_PAINEL,
    fg=COR_TEXTO,
    font=(
        "DejaVu Sans",
        11,
        "bold"
    )
)

info_titulo.grid(
    row=0,
    column=0,
    columnspan=4,
    sticky="w",
    padx=15,
    pady=(12, 8)
)


def criar_campo(
    linha,
    coluna,
    titulo_campo,
    variavel
):

    tk.Label(
        informacoes,
        text=titulo_campo,
        bg=COR_PAINEL,
        fg=COR_TEXTO_SECUNDARIO,
        font=(
            "DejaVu Sans",
            9
        )
    ).grid(
        row=linha,
        column=coluna,
        sticky="w",
        padx=(15, 5),
        pady=3
    )

    tk.Label(
        informacoes,
        textvariable=variavel,
        bg=COR_PAINEL,
        fg=COR_TEXTO,
        font=(
            "DejaVu Sans",
            10,
            "bold"
        )
    ).grid(
        row=linha,
        column=coluna + 1,
        sticky="w",
        padx=(0, 20),
        pady=3
    )


criar_campo(
    1,
    0,
    "Nome:",
    nome_var
)

criar_campo(
    1,
    2,
    "Idade:",
    idade_var
)

criar_campo(
    2,
    0,
    "Status:",
    status_var
)

criar_campo(
    2,
    2,
    "Crime:",
    crime_var
)

criar_campo(
    3,
    0,
    "Similaridade:",
    similaridade_var
)

criar_campo(
    3,
    2,
    "Câmera:",
    camera_var
)

criar_campo(
    4,
    0,
    "Local:",
    local_var
)

criar_campo(
    4,
    2,
    "Ocorrência:",
    ocorrencia_status_var
)

criar_campo(
    5,
    0,
    "Detectado em:",
    detected_at_var
)


# ============================================================
# BOTÕES
# ============================================================

botoes = tk.Frame(
    painel_direito,
    bg=COR_FUNDO
)

botoes.pack(
    fill="x"
)


botao_confirmar = tk.Button(
    botoes,
    text="CONFIRMAR",
    command=confirmar,
    bg=COR_VERDE,
    fg="white",
    activebackground=COR_VERDE,
    activeforeground="white",
    relief="flat",
    bd=0,
    padx=25,
    pady=9,
    font=(
        "DejaVu Sans",
        10,
        "bold"
    ),
    cursor="hand2"
)

botao_confirmar.pack(
    side="left",
    padx=(0, 8)
)


botao_descartar = tk.Button(
    botoes,
    text="DESCARTAR",
    command=descartar,
    bg=COR_VERMELHO,
    fg="white",
    activebackground=COR_VERMELHO,
    activeforeground="white",
    relief="flat",
    bd=0,
    padx=25,
    pady=9,
    font=(
        "DejaVu Sans",
        10,
        "bold"
    ),
    cursor="hand2"
)

botao_descartar.pack(
    side="left"
)


# ============================================================
# BARRA DE STATUS
# ============================================================

status_bar = tk.Label(
    root,
    textvariable=status_bar_var,
    bg=COR_PAINEL,
    fg=COR_TEXTO_SECUNDARIO,
    anchor="w",
    font=(
        "DejaVu Sans",
        9
    ),
    padx=12,
    pady=5
)

status_bar.pack(
    fill="x",
    side="bottom"
)


# ============================================================
# INICIALIZAÇÃO
# ============================================================

print()
print("========================================")
print("X-FACE - CENTRAL DE VERIFICAÇÃO")
print("========================================")
print("Tema: escuro")
print("Janela: 1280x720")
print("Duas imagens: ATIVADO")
print("Imagens: SEM CORTE")
print("Atualização automática: ATIVADA")
print("Intervalo: 1 segundo")
print("Seleção: lista de ocorrências")
print("Botão Próximo: REMOVIDO")
print("========================================")
print()


# Primeira consulta rápida.
root.after(
    100,
    atualizar_central
)


# ============================================================
# EXECUÇÃO
# ============================================================

root.mainloop()
