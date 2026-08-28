import tkinter as tk
from tkinter import messagebox

from central.ocorrencias import buscar_ocorrencias_pendentes


def atualizar_central():
    ocorrencias = buscar_ocorrencias_pendentes()

    lista.delete(0, tk.END)

    for ocorrencia in ocorrencias:
        texto = (
            f"ID {ocorrencia['occurrence_id']} | "
            f"{ocorrencia['name']} | "
            f"{ocorrencia['similarity']}%"
        )

        lista.insert(tk.END, texto)

    if ocorrencias:
        mostrar_ocorrencia(ocorrencias[0])
    else:
        limpar_dados()


def mostrar_ocorrencia(ocorrencia):
    nome_var.set(ocorrencia["name"])
    idade_var.set(f"{ocorrencia['age']} anos")
    status_var.set(ocorrencia["status"])
    crime_var.set(ocorrencia["crime"] or "Nenhuma ocorrência")
    similaridade_var.set(f"{ocorrencia['similarity']}%")
    camera_var.set(ocorrencia["camera"])
    local_var.set(ocorrencia["location"])
    ocorrencia_status_var.set(ocorrencia["occurrence_status"])
    frame_var.set(ocorrencia["frame_path"])


def limpar_dados():
    nome_var.set("-")
    idade_var.set("-")
    status_var.set("-")
    crime_var.set("-")
    similaridade_var.set("-")
    camera_var.set("-")
    local_var.set("-")
    ocorrencia_status_var.set("-")
    frame_var.set("-")


def confirmar():
    messagebox.showinfo(
        "Confirmação",
        "Ocorrência marcada para confirmação."
    )


def descartar():
    messagebox.showinfo(
        "Ocorrência descartada",
        "Ocorrência marcada para descarte."
    )


# -------------------------------------------------
# JANELA PRINCIPAL
# -------------------------------------------------

janela = tk.Tk()

janela.title("X-Face — Central de Verificação")
janela.geometry("900x600")


# -------------------------------------------------
# TÍTULO
# -------------------------------------------------

titulo = tk.Label(
    janela,
    text="X-FACE — CENTRAL DE VERIFICAÇÃO",
    font=("Arial", 20, "bold")
)

titulo.pack(pady=15)


# -------------------------------------------------
# LISTA DE OCORRÊNCIAS
# -------------------------------------------------

lista = tk.Listbox(
    janela,
    width=80,
    height=6
)

lista.pack(pady=10)


# -------------------------------------------------
# DADOS
# -------------------------------------------------

dados = tk.Frame(janela)
dados.pack(pady=10)


nome_var = tk.StringVar()
idade_var = tk.StringVar()
status_var = tk.StringVar()
crime_var = tk.StringVar()
similaridade_var = tk.StringVar()
camera_var = tk.StringVar()
local_var = tk.StringVar()
ocorrencia_status_var = tk.StringVar()
frame_var = tk.StringVar()


def campo(texto, variavel, linha):
    tk.Label(
        dados,
        text=texto,
        font=("Arial", 11, "bold")
    ).grid(
        row=linha,
        column=0,
        sticky="w",
        padx=10,
        pady=3
    )

    tk.Label(
        dados,
        textvariable=variavel,
        font=("Arial", 11)
    ).grid(
        row=linha,
        column=1,
        sticky="w",
        padx=10,
        pady=3
    )


campo("Nome:", nome_var, 0)
campo("Idade:", idade_var, 1)
campo("Status:", status_var, 2)
campo("Crime:", crime_var, 3)
campo("Similaridade:", similaridade_var, 4)
campo("Câmera:", camera_var, 5)
campo("Localização:", local_var, 6)
campo("Ocorrência:", ocorrencia_status_var, 7)
campo("Frame:", frame_var, 8)


# -------------------------------------------------
# BOTÕES
# -------------------------------------------------

botoes = tk.Frame(janela)
botoes.pack(pady=20)


tk.Button(
    botoes,
    text="ATUALIZAR",
    width=18,
    command=atualizar_central
).grid(
    row=0,
    column=0,
    padx=10
)


tk.Button(
    botoes,
    text="CONFIRMAR",
    width=18,
    command=confirmar
).grid(
    row=0,
    column=1,
    padx=10
)


tk.Button(
    botoes,
    text="DESCARTAR",
    width=18,
    command=descartar
).grid(
    row=0,
    column=2,
    padx=10
)


# -------------------------------------------------
# INICIALIZAÇÃO
# -------------------------------------------------

atualizar_central()

janela.mainloop()

    print("DEBUG: atualizar_central iniciou")

    ocorrencias = buscar_ocorrencias_pendentes()

    print("DEBUG: ocorrencias =", ocorrencias)
