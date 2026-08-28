import os
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

from central.ocorrencias import (
    buscar_ocorrencias_pendentes,
    confirmar_ocorrencia,
    descartar_ocorrencia,
)


# ============================================================
# CONFIGURAÇÃO DA JANELA
# ============================================================

LARGURA_JANELA = 1280
ALTURA_JANELA = 720

INTERVALO_ATUALIZACAO = 2000  # 2 segundos

LARGURA_IMAGEM = 440
ALTURA_IMAGEM = 260


# ============================================================
# JANELA PRINCIPAL
# ============================================================

janela = tk.Tk()

janela.title("X-Face — Central de Ocorrências")

janela.geometry(
    f"{LARGURA_JANELA}x{ALTURA_JANELA}"
)

janela.minsize(
    1100,
    650
)

janela.configure(
    bg="#202124"
)


# ============================================================
# VARIÁVEIS
# ============================================================

ocorrencias_atuais = []

ocorrencia_selecionada = None

imagem_captura_tk = None
imagem_referencia_tk = None

ultimo_frame_path = None
ultima_face_reference = None
ultimo_occurrence_id = None


nome_var = tk.StringVar(value="-")
idade_var = tk.StringVar(value="-")
status_var = tk.StringVar(value="-")
crime_var = tk.StringVar(value="-")
similaridade_var = tk.StringVar(value="-")
camera_var = tk.StringVar(value="-")
local_var = tk.StringVar(value="-")
ocorrencia_status_var = tk.StringVar(value="-")
data_var = tk.StringVar(value="-")


# ============================================================
# TÍTULO
# ============================================================

titulo = tk.Label(
    janela,
    text="X-FACE — CENTRAL DE OCORRÊNCIAS",
    font=("Arial", 18, "bold"),
    bg="#202124",
    fg="white"
)

titulo.pack(
    pady=(8, 4)
)


# ============================================================
# ÁREA PRINCIPAL
# ============================================================

area_principal = tk.Frame(
    janela,
    bg="#202124"
)

area_principal.pack(
    fill="both",
    expand=True,
    padx=12,
    pady=4
)


# ============================================================
# LISTA DE OCORRÊNCIAS
# ============================================================

painel_lista = tk.Frame(
    area_principal,
    bg="#292a2d",
    width=280
)

painel_lista.pack(
    side="left",
    fill="y",
    padx=(0, 10)
)

painel_lista.pack_propagate(False)


tk.Label(
    painel_lista,
    text="OCORRÊNCIAS PENDENTES",
    font=("Arial", 11, "bold"),
    bg="#292a2d",
    fg="white"
).pack(
    pady=(10, 6)
)


lista = tk.Listbox(
    painel_lista,
    font=("Arial", 10),
    bg="#171717",
    fg="white",
    selectbackground="#3f51b5",
    selectforeground="white",
    activestyle="none",
    borderwidth=0,
    highlightthickness=0
)

lista.pack(
    fill="both",
    expand=True,
    padx=8,
    pady=(0, 8)
)


lista.bind(
    "<<ListboxSelect>>",
    lambda event: selecionar_ocorrencia()
)


# ============================================================
# PAINEL CENTRAL
# ============================================================

painel_central = tk.Frame(
    area_principal,
    bg="#202124"
)

painel_central.pack(
    side="left",
    fill="both",
    expand=True
)


# ============================================================
# ÁREA DAS IMAGENS
# ============================================================

painel_imagens = tk.Frame(
    painel_central,
    bg="#202124"
)

painel_imagens.pack(
    fill="x",
    pady=(0, 6)
)


# ------------------------------------------------------------
# CAPTURA
# ------------------------------------------------------------

painel_captura = tk.Frame(
    painel_imagens,
    bg="#292a2d"
)

painel_captura.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(0, 5)
)


tk.Label(
    painel_captura,
    text="CAPTURA DA CÂMERA",
    font=("Arial", 10, "bold"),
    bg="#292a2d",
    fg="white"
).pack(
    pady=(5, 2)
)


label_captura = tk.Label(
    painel_captura,
    text="Nenhuma captura",
    bg="#111111",
    fg="#aaaaaa",
    width=1,
    height=1
)

label_captura.pack(
    fill="both",
    expand=True,
    padx=6,
    pady=(0, 6)
)


# ------------------------------------------------------------
# FOTO CADASTRADA
# ------------------------------------------------------------

painel_referencia = tk.Frame(
    painel_imagens,
    bg="#292a2d"
)

painel_referencia.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(5, 0)
)


tk.Label(
    painel_referencia,
    text="FOTO CADASTRADA",
    font=("Arial", 10, "bold"),
    bg="#292a2d",
    fg="white"
).pack(
    pady=(5, 2)
)


label_referencia = tk.Label(
    painel_referencia,
    text="Nenhuma referência",
    bg="#111111",
    fg="#aaaaaa",
    width=1,
    height=1
)

label_referencia.pack(
    fill="both",
    expand=True,
    padx=6,
    pady=(0, 6)
)


# ============================================================
# PAINEL DE INFORMAÇÕES
# ============================================================

painel_info = tk.Frame(
    painel_central,
    bg="#292a2d"
)

painel_info.pack(
    fill="x",
    pady=(0, 5)
)


# ============================================================
# FUNÇÃO DE CAMPO
# ============================================================

def campo(parent, texto, variavel, coluna, linha):
    tk.Label(
        parent,
        text=texto,
        font=("Arial", 9, "bold"),
        bg="#292a2d",
        fg="#bdbdbd",
        anchor="w"
    ).grid(
        row=linha,
        column=coluna * 2,
        sticky="w",
        padx=(10, 3),
        pady=2
    )

    tk.Label(
        parent,
        textvariable=variavel,
        font=("Arial", 9),
        bg="#292a2d",
        fg="white",
        anchor="w"
    ).grid(
        row=linha,
        column=coluna * 2 + 1,
        sticky="w",
        padx=(0, 10),
        pady=2
    )


# ============================================================
# CAMPOS
# ============================================================

campo(
    painel_info,
    "Pessoa:",
    nome_var,
    0,
    0
)

campo(
    painel_info,
    "Idade:",
    idade_var,
    1,
    0
)

campo(
    painel_info,
    "Similaridade:",
    similaridade_var,
    2,
    0
)

campo(
    painel_info,
    "Status:",
    status_var,
    0,
    1
)

campo(
    painel_info,
    "Crime:",
    crime_var,
    1,
    1
)

campo(
    painel_info,
    "Ocorrência:",
    ocorrencia_status_var,
    2,
    1
)

campo(
    painel_info,
    "Câmera:",
    camera_var,
    0,
    2
)

campo(
    painel_info,
    "Local:",
    local_var,
    1,
    2
)

campo(
    painel_info,
    "Detectado:",
    data_var,
    2,
    2
)


# ============================================================
# BOTÕES
# ============================================================

painel_botoes = tk.Frame(
    painel_central,
    bg="#202124"
)

painel_botoes.pack(
    fill="x",
    pady=(2, 2)
)


botao_atualizar = tk.Button(
    painel_botoes,
    text="ATUALIZAR",
    font=("Arial", 9, "bold"),
    width=14,
    command=lambda: atualizar_central(forcar=True)
)

botao_atualizar.pack(
    side="left",
    padx=4
)


botao_confirmar = tk.Button(
    painel_botoes,
    text="CONFIRMAR",
    font=("Arial", 9, "bold"),
    width=14,
    command=lambda: confirmar()
)

botao_confirmar.pack(
    side="left",
    padx=4
)


botao_descartar = tk.Button(
    painel_botoes,
    text="DESCARTAR",
    font=("Arial", 9, "bold"),
    width=14,
    command=lambda: descartar()
)

botao_descartar.pack(
    side="left",
    padx=4
)


# ============================================================
# REDIMENSIONAMENTO PROPORCIONAL
# ============================================================

def redimensionar_imagem(
    imagem,
    largura_max,
    altura_max
):
    """
    Redimensiona mantendo a proporção original.

    A imagem nunca é cortada.
    """

    imagem = imagem.copy()

    imagem.thumbnail(
        (
            largura_max,
            altura_max
        ),
        Image.Resampling.LANCZOS
    )

    return imagem


# ============================================================
# CARREGAR IMAGEM
# ============================================================

def carregar_imagem(
    caminho,
    largura_max=LARGURA_IMAGEM,
    altura_max=ALTURA_IMAGEM
):
    """
    Carrega uma imagem do disco e redimensiona sem cortar.
    """

    if not caminho:
        return None

    caminho = os.path.expanduser(
        str(caminho)
    )

    if not os.path.isfile(caminho):
        return None

    try:

        imagem = Image.open(caminho)

        imagem = redimensionar_imagem(
            imagem,
            largura_max,
            altura_max
        )

        return ImageTk.PhotoImage(
            imagem
        )

    except Exception as erro:

        print(
            f"Erro ao carregar imagem "
            f"{caminho}: {erro}"
        )

        return None


# ============================================================
# LIMPAR IMAGENS
# ============================================================

def limpar_imagens():

    global imagem_captura_tk
    global imagem_referencia_tk

    imagem_captura_tk = None
    imagem_referencia_tk = None

    label_captura.configure(
        image="",
        text="Nenhuma captura"
    )

    label_referencia.configure(
        image="",
        text="Nenhuma referência"
    )


# ============================================================
# MOSTRAR IMAGENS
# ============================================================

def mostrar_imagens(ocorrencia):
    """
    Exibe:

    1. frame_path:
       captura feita pela câmera;

    2. face_reference:
       imagem cadastrada do participante.

    As imagens são carregadas somente quando necessário.
    """

    global imagem_captura_tk
    global imagem_referencia_tk
    global ultimo_frame_path
    global ultima_face_reference

    frame_path = ocorrencia.get(
        "frame_path"
    )

    face_reference = ocorrencia.get(
        "face_reference"
    )

    # --------------------------------------------------------
    # CAPTURA
    # --------------------------------------------------------

    if frame_path != ultimo_frame_path:

        imagem_captura_tk = carregar_imagem(
            frame_path
        )

        if imagem_captura_tk is not None:

            label_captura.configure(
                image=imagem_captura_tk,
                text=""
            )

        else:

            label_captura.configure(
                image="",
                text="Captura não encontrada"
            )

        ultimo_frame_path = frame_path

    # --------------------------------------------------------
    # REFERÊNCIA
    # --------------------------------------------------------

    if face_reference != ultima_face_reference:

        imagem_referencia_tk = carregar_imagem(
            face_reference
        )

        if imagem_referencia_tk is not None:

            label_referencia.configure(
                image=imagem_referencia_tk,
                text=""
            )

        else:

            label_referencia.configure(
                image="",
                text="Foto cadastrada não encontrada"
            )

        ultima_face_reference = face_reference


# ============================================================
# MOSTRAR DADOS DA OCORRÊNCIA
# ============================================================

def mostrar_ocorrencia(ocorrencia):

    global ocorrencia_selecionada
    global ultimo_occurrence_id

    ocorrencia_selecionada = ocorrencia

    occurrence_id = ocorrencia[
        "occurrence_id"
    ]

    ultimo_occurrence_id = occurrence_id

    nome_var.set(
        ocorrencia.get(
            "name",
            "-"
        )
    )

    idade = ocorrencia.get(
        "age"
    )

    idade_var.set(
        f"{idade} anos"
        if idade is not None
        else "-"
    )

    status_var.set(
        ocorrencia.get(
            "status",
            "-"
        )
        or "-"
    )

    crime_var.set(
        ocorrencia.get(
            "crime",
            "-"
        )
        or "-"
    )

    similaridade = ocorrencia.get(
        "similarity"
    )

    if similaridade is not None:

        similaridade_var.set(
            f"{float(similaridade):.2f}%"
        )

    else:

        similaridade_var.set("-")

    camera_var.set(
        ocorrencia.get(
            "camera",
            "-"
        )
        or "-"
    )

    local_var.set(
        ocorrencia.get(
            "location",
            "-"
        )
        or "-"
    )

    ocorrencia_status_var.set(
        ocorrencia.get(
            "occurrence_status",
            "-"
        )
        or "-"
    )

    detected_at = ocorrencia.get(
        "detected_at"
    )

    if detected_at:

        data_var.set(
            detected_at.strftime(
                "%d/%m/%Y %H:%M:%S"
            )
        )

    else:

        data_var.set("-")

    mostrar_imagens(
        ocorrencia
    )


# ============================================================
# LIMPAR DADOS
# ============================================================

def limpar_dados():

    global ocorrencia_selecionada
    global ultimo_occurrence_id
    global ultimo_frame_path
    global ultima_face_reference

    ocorrencia_selecionada = None

    ultimo_occurrence_id = None

    ultimo_frame_path = None

    ultima_face_reference = None

    nome_var.set("-")
    idade_var.set("-")
    status_var.set("-")
    crime_var.set("-")
    similaridade_var.set("-")
    camera_var.set("-")
    local_var.set("-")
    ocorrencia_status_var.set("-")
    data_var.set("-")

    limpar_imagens()


# ============================================================
# ATUALIZAR CENTRAL
# ============================================================

def atualizar_central(forcar=False):
    """
    Atualiza a lista de ocorrências PENDING.

    Não recarrega as imagens se a ocorrência selecionada
    continuar sendo a mesma.
    """

    global ocorrencias_atuais
    global ocorrencia_selecionada

    try:

        novas_ocorrencias = list(
            buscar_ocorrencias_pendentes()
        )

    except Exception as erro:

        print(
            f"Erro ao atualizar central: {erro}"
        )

        janela.after(
            INTERVALO_ATUALIZACAO,
            atualizar_central
        )

        return

    # --------------------------------------------------------
    # IDENTIFICAR ID ATUAL
    # --------------------------------------------------------

    id_atual = None

    if ocorrencia_selecionada:

        id_atual = ocorrencia_selecionada.get(
            "occurrence_id"
        )

    # --------------------------------------------------------
    # ATUALIZAR LISTA
    # --------------------------------------------------------

    ids_novos = [
        ocorrencia["occurrence_id"]
        for ocorrencia in novas_ocorrencias
    ]

    ids_antigos = [
        ocorrencia["occurrence_id"]
        for ocorrencia in ocorrencias_atuais
    ]

    lista_mudou = (
        ids_novos != ids_antigos
    )

    if lista_mudou or forcar:

        lista.delete(
            0,
            tk.END
        )

        for ocorrencia in novas_ocorrencias:

            texto = (
                f"#{ocorrencia['occurrence_id']}  "
                f"{ocorrencia['name']}  "
                f"| {float(ocorrencia['similarity']):.1f}%"
            )

            lista.insert(
                tk.END,
                texto
            )

    ocorrencias_atuais = novas_ocorrencias

    # --------------------------------------------------------
    # SE NÃO EXISTIR OCORRÊNCIA
    # --------------------------------------------------------

    if not novas_ocorrencias:

        limpar_dados()

        janela.after(
            INTERVALO_ATUALIZACAO,
            atualizar_central
        )

        return

    # --------------------------------------------------------
    # TENTAR MANTER A OCORRÊNCIA SELECIONADA
    # --------------------------------------------------------

    indice_selecionado = 0

    if id_atual is not None:

        for indice, ocorrencia in enumerate(
            novas_ocorrencias
        ):

            if (
                ocorrencia["occurrence_id"]
                == id_atual
            ):
                indice_selecionado = indice
                break

    # --------------------------------------------------------
    # SELECIONAR NA LISTA
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # MOSTRAR
    # --------------------------------------------------------

    ocorrencia = novas_ocorrencias[
        indice_selecionado
    ]

    # Só atualiza a interface se for uma ocorrência
    # diferente ou se o operador pediu atualização manual.
    if (
        id_atual != ocorrencia["occurrence_id"]
        or forcar
    ):

        mostrar_ocorrencia(
            ocorrencia
        )

    # --------------------------------------------------------
    # PRÓXIMA ATUALIZAÇÃO
    # --------------------------------------------------------

    janela.after(
        INTERVALO_ATUALIZACAO,
        atualizar_central
    )


# ============================================================
# SELECIONAR OCORRÊNCIA
# ============================================================

def selecionar_ocorrencia():

    selecao = lista.curselection()

    if not selecao:
        return

    indice = selecao[0]

    if indice >= len(
        ocorrencias_atuais
    ):
        return

    ocorrencia = ocorrencias_atuais[
        indice
    ]

    mostrar_ocorrencia(
        ocorrencia
    )


# ============================================================
# CONFIRMAR
# ============================================================

def confirmar():

    if ocorrencia_selecionada is None:

        messagebox.showwarning(
            "Nenhuma ocorrência",
            "Selecione uma ocorrência para confirmar."
        )

        return

    occurrence_id = ocorrencia_selecionada[
        "occurrence_id"
    ]

    confirmar_ocorrencia(
        occurrence_id
    )

    # Atualiza imediatamente.
    atualizar_central(
        forcar=True
    )


# ============================================================
# DESCARTAR
# ============================================================

def descartar():

    if ocorrencia_selecionada is None:

        messagebox.showwarning(
            "Nenhuma ocorrência",
            "Selecione uma ocorrência para descartar."
        )

        return

    occurrence_id = ocorrencia_selecionada[
        "occurrence_id"
    ]

    resposta = messagebox.askyesno(
        "Descartar ocorrência",
        (
            f"Tem certeza que deseja descartar "
            f"a ocorrência #{occurrence_id}?"
        )
    )

    if not resposta:
        return

    descartar_ocorrencia(
        occurrence_id
    )

    # Atualiza imediatamente.
    atualizar_central(
        forcar=True
    )


# ============================================================
# INICIALIZAÇÃO
# ============================================================

atualizar_central(
    forcar=True
)


# ============================================================
# EXECUÇÃO
# ============================================================

janela.mainloop()
