# predict.py — testa modelos ML pela linha de comando

import joblib  # Carrega arquivos .pkl
from pathlib import Path  # Caminhos multiplataforma

MODELS = Path(__file__).parent / "models"


def main():
    espera = joblib.load(MODELS / "modelo_espera.pkl")
    noshow = joblib.load(MODELS / "modelo_noshow.pkl")

    # Features: prioridade, especialidade, hora, dia_semana, tamanho_fila
    X_espera = [[2, 0, 10, 1, 5]]
    tempo = espera.predict(X_espera)[0]
    print(f"Tempo estimado de espera: {tempo:.0f} minutos")

    # Features: dia_semana, hora, idade, faltas, confirmado
    X_noshow = [[1, 8, 28, 2, 0]]
    prob = noshow.predict_proba(X_noshow)[0][1]
    print(f"Probabilidade de falta: {prob*100:.1f}%")


if __name__ == "__main__":
    main()
