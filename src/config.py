# src/config.py
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

def load_config() -> dict:
    """Carrega as configurações do arquivo config.yaml."""
    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        # Fallback para configurações padrão se o arquivo não existir
        return {
            "file_limits": {
                "max_file_size_mb": 200,
                "sampling_threshold_rows": 100000,
                "sampling_rows": 50000,
            },
            "analysis": {"num_suggested_queries": 5},
            "llm": {
                "model_name": "gemini-1.5-flash",
                "temperature": 0.0,
                "max_output_tokens": 2048,
            },
            "ui": {"app_title": "Agente EDA com Gemini", "sidebar_header": "Configurações"},
        }

# Carrega a configuração uma vez quando o módulo é importado
settings = load_config()