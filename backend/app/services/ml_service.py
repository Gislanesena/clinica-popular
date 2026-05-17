# ml_service.py — predição de tempo de espera e risco de falta 

from pathlib import Path
from datetime import datetime
import joblib  # Carrega modelos .pkl treinados
import numpy as np
from ..core.config import settings

PRIORIDADE_MAP = {"emergencia": 0, "gestante": 1, "idoso": 2, "pcd": 3, "normal": 4}
ESPECIALIDADE_MAP = {
    "Clínico Geral": 0, "Pediatria": 1, "Enfermagem": 2, "Ginecologia": 3
}


class MLService:
    """Encapsula modelos scikit-learn ou heurísticas se .pkl não existir."""

    def __init__(self):
        base = Path(__file__).resolve().parents[3] / "ml" / "models"
        if not base.exists():
            base = Path("/app/ml/models")
        self.wait_model = None
        self.noshow_model = None
        self._load_models(base)

    def _load_models(self, base: Path):
        wait_path = base / "modelo_espera.pkl"
        noshow_path = base / "modelo_noshow.pkl"
        if wait_path.exists():
            self.wait_model = joblib.load(wait_path)
        if noshow_path.exists():
            self.noshow_model = joblib.load(noshow_path)

    def _features_espera(
        self, prioridade: str, especialidade: str, hora: int, dia_semana: int, fila_tamanho: int
    ) -> np.ndarray:
        return np.array([[
            PRIORIDADE_MAP.get(prioridade, 4),
            ESPECIALIDADE_MAP.get(especialidade, 0),
            hora,
            dia_semana,
            fila_tamanho,
        ]])

    def prever_tempo_espera(
        self,
        prioridade: str = "normal",
        especialidade: str = "Clínico Geral",
        fila_tamanho: int = 1,
    ) -> int:
        """Minutos estimados até ser chamado."""
        now = datetime.now()
        if self.wait_model:
            X = self._features_espera(
                prioridade, especialidade, now.hour, now.weekday(), fila_tamanho
            )
            pred = float(self.wait_model.predict(X)[0])
            return max(5, int(round(pred)))
        base = 20 + fila_tamanho * 8
        bonus = PRIORIDADE_MAP.get(prioridade, 4) * -3
        return max(5, base + bonus)

    def prever_noshow(
        self,
        dia_semana: int,
        hora: int,
        idade: int,
        faltas_anteriores: int = 0,
        confirmado: int = 0,
    ) -> float:
        """Probabilidade de o paciente faltar à consulta (0 a 1)."""
        if self.noshow_model:
            X = np.array([[dia_semana, hora, idade, faltas_anteriores, confirmado]])
            prob = float(self.noshow_model.predict_proba(X)[0][1])
            return round(min(0.99, max(0.01, prob)), 4)
        score = 0.2
        if hora < 9 or hora > 16:
            score += 0.15
        if idade < 25:
            score += 0.1
        score += faltas_anteriores * 0.12
        if not confirmado:
            score += 0.2
        return round(min(0.95, score), 4)

    def risco_label(self, prob: float) -> str:
        if prob >= 0.6:
            return "alto"
        if prob >= 0.35:
            return "medio"
        return "baixo"


ml_service = MLService()
