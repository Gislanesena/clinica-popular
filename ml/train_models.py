"""
Treinamento dos modelos de Machine Learning
- Tempo de espera na fila (Regressão)
- Probabilidade de falta / no-show (Classificação)
"""
import os  # Operações com sistema de arquivos
from pathlib import Path  # Caminhos das pastas data/ e models/
import numpy as np  # Arrays numéricos para features
import pandas as pd  # Tabelas de dados (datasets)
from sklearn.model_selection import train_test_split  # Separa treino e teste
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier  # Modelos ML
from sklearn.metrics import mean_absolute_error, roc_auc_score, classification_report  # Métricas
import joblib  # Salva modelos em .pkl

RNG = 42
BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
MODELS_DIR = BASE / "models"
MODELS_DIR.mkdir(exist_ok=True)


def gerar_dados_espera(n=800) -> pd.DataFrame:
    """Gera dataset sintético baseado em padrões de clínicas populares."""
    np.random.seed(RNG)
    prioridades = [0, 1, 2, 3, 4]
    especialidades = [0, 1, 2]
    rows = []
    for _ in range(n):
        pri = np.random.choice(prioridades, p=[0.02, 0.08, 0.25, 0.05, 0.60])
        esp = np.random.choice(especialidades)
        hora = np.random.randint(7, 18)
        dia = np.random.randint(0, 6)
        fila = np.random.randint(1, 15)
        base = 15 + fila * 6 + (4 - min(pri, 4)) * -4 + esp * 3
        if 11 <= hora <= 14:
            base += 10
        tempo = max(5, base + np.random.normal(0, 8))
        rows.append({
            "prioridade": pri,
            "especialidade": esp,
            "hora": hora,
            "dia_semana": dia,
            "fila_tamanho": fila,
            "tempo_espera_min": tempo,
        })
    return pd.DataFrame(rows)


def gerar_dados_noshow(n=600) -> pd.DataFrame:
    np.random.seed(RNG + 1)
    rows = []
    for _ in range(n):
        dia = np.random.randint(0, 6)
        hora = np.random.randint(7, 18)
        idade = np.random.randint(18, 85)
        faltas_ant = np.random.poisson(0.8)
        confirmado = np.random.choice([0, 1], p=[0.35, 0.65])
        logit = -1.5 + faltas_ant * 0.5 + (1 - confirmado) * 0.8
        if hora < 9:
            logit += 0.4
        if idade < 30:
            logit += 0.3
        if dia == 5:
            logit += 0.5
        prob = 1 / (1 + np.exp(-logit))
        faltou = 1 if np.random.random() < prob else 0
        rows.append({
            "dia_semana": dia,
            "hora": hora,
            "idade": idade,
            "faltas_anteriores": faltas_ant,
            "confirmado": confirmado,
            "faltou": faltou,
        })
    return pd.DataFrame(rows)


def treinar_espera(df: pd.DataFrame):
    features = ["prioridade", "especialidade", "hora", "dia_semana", "fila_tamanho"]
    X = df[features]
    y = df["tempo_espera_min"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RNG)
    model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=RNG)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    print(f"[Espera] MAE: {mae:.2f} minutos")
    path = MODELS_DIR / "modelo_espera.pkl"
    joblib.dump(model, path)
    print(f"Modelo salvo: {path}")
    return model, mae


def treinar_noshow(df: pd.DataFrame):
    features = ["dia_semana", "hora", "idade", "faltas_anteriores", "confirmado"]
    X = df[features]
    y = df["faltou"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RNG, stratify=y)
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=RNG)
    model.fit(X_train, y_train)
    prob = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, prob)
    print(f"[No-show] AUC-ROC: {auc:.3f}")
    print(classification_report(y_test, model.predict(X_test), target_names=["compareceu", "faltou"]))
    path = MODELS_DIR / "modelo_noshow.pkl"
    joblib.dump(model, path)
    print(f"Modelo salvo: {path}")
    return model, auc


def main():
    print("=== Treinamento ML — Clínica Popular ===\n")
    df_espera = gerar_dados_espera()
    df_espera.to_csv(DATA_DIR / "dataset_espera.csv", index=False)
    treinar_espera(df_espera)

    print()
    df_noshow = gerar_dados_noshow()
    df_noshow.to_csv(DATA_DIR / "dataset_noshow.csv", index=False)
    treinar_noshow(df_noshow)

    print("\n=== Análise resumida da clínica (dados sintéticos) ===")
    print(f"Tempo médio de espera: {df_espera['tempo_espera_min'].mean():.1f} min")
    print(f"Taxa de falta: {df_noshow['faltou'].mean()*100:.1f}%")
    print(f"Horário de pico: {df_espera.groupby('hora')['tempo_espera_min'].mean().idxmax()}h")


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    main()
