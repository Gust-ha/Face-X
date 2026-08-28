from central.ocorrencias import registrar_ocorrencia


ocorrencia_id = registrar_ocorrencia(
    participant_id=1,
    camera_id=1,
    similarity=95.50,
    frame_path="captures/teste_novo_gustavo.jpg"
)

print("Ocorrência registrada!")
print("ID da ocorrência:", ocorrencia_id)