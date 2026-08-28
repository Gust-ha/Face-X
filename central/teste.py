from central.ocorrencias import buscar_ocorrencias_pendentes


ocorrencias = buscar_ocorrencias_pendentes()

for ocorrencia in ocorrencias:
    print("ID:", ocorrencia["occurrence_id"])
    print("Nome:", ocorrencia["name"])
    print("Idade:", ocorrencia["age"])
    print("Status:", ocorrencia["status"])
    print("Crime:", ocorrencia["crime"])
    print("Câmera:", ocorrencia["camera"])
    print("Local:", ocorrencia["location"])
    print("Similaridade:", ocorrencia["similarity"])
    print("Status da ocorrência:", ocorrencia["occurrence_status"])
    print("Frame:", ocorrencia["frame_path"])