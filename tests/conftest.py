# tests/conftest.py
# Arquivo de configuração para o pytest, onde definimos os fixtures.

import pytest
import pandas as pd
from src.agent import EDAAgentPro

@pytest.fixture
def sample_csv_content() -> str:
    """
    Retorna o conteúdo de um CSV de teste como uma string.
    Este fixture é usado para simular um arquivo carregado.
    """
    return "ID,Nome,Idade,Cidade,Salario\n1,Ana,28,Recife,5000\n2,Bruno,35,Salvador,8000\n3,Carla,22,Recife,3500\n4,Daniel,45,Salvador,12000"

@pytest.fixture
def agent_instance() -> EDAAgentPro:
    """
    Retorna uma instância limpa do EDAAgentPro.
    Usa uma chave de API falsa, pois as chamadas reais à API serão mockadas nos testes.
    """
    return EDAAgentPro(api_key="fake-api-key-for-testing")