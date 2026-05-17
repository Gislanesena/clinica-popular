"""
Análise de dados da clínica — Pandas
Gera relatório de indicadores para gestão.
"""
import pandas as pd  # Leitura e agregação dos CSVs gerados no treino
from pathlib import Path  # Localiza pasta ml/data/

DATA = Path(__file__).parent / "data"


def relatorio():
    espera = pd.read_csv(DATA / "dataset_espera.csv")
    noshow = pd.read_csv(DATA / "dataset_noshow.csv")

    print("=" * 50)
    print("RELATÓRIO ANALÍTICO — CLÍNICA POPULAR")
    print("=" * 50)

    print("\n--- Tempo de Espera ---")
    print(espera.groupby("prioridade")["tempo_espera_min"].agg(["mean", "median", "count"]))

    print("\n--- Por Especialidade ---")
    esp_map = {0: "Clínico Geral", 1: "Pediatria", 2: "Enfermagem"}
    espera["esp_nome"] = espera["especialidade"].map(esp_map)
    print(espera.groupby("esp_nome")["tempo_espera_min"].mean().round(1))

    print("\n--- Horários de Pico ---")
    pico = espera.groupby("hora")["tempo_espera_min"].mean()
    print(f"Hora com maior espera: {pico.idxmax()}h ({pico.max():.0f} min médio)")

    print("\n--- No-show ---")
    taxa = noshow["faltou"].mean() * 100
    print(f"Taxa geral de faltas: {taxa:.1f}%")
    alto_risco = noshow[noshow["faltas_anteriores"] >= 2]["faltou"].mean() * 100
    print(f"Taxa (2+ faltas anteriores): {alto_risco:.1f}%")

    print("\n--- Recomendações ---")
    if taxa > 25:
        print("• Reforçar confirmação por SMS/WhatsApp")
    if pico.max() > 40:
        print(f"• Reforçar equipe às {pico.idxmax()}h")
    print("• Priorizar idosos e gestantes na fila (já implementado)")


if __name__ == "__main__":
    relatorio()
