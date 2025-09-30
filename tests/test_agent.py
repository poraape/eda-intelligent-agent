# tests/test_agent.py
# Suíte de testes para o núcleo lógico do agente (EDAAgentPro).

import pandas as pd
from unittest.mock import MagicMock, patch

# Os fixtures `agent_instance` e `sample_csv_content` são injetados a partir do conftest.py

def test_load_csv_file(agent_instance, sample_csv_content):
    """
    Testa o carregamento bem-sucedido de um arquivo CSV.
    Esta função não depende da API Gemini.
    """
    mock_file = MagicMock()
    mock_file.name = "test.csv"
    mock_file.getvalue.return_value = sample_csv_content.encode('utf-8')

    success, message = agent_instance.load_file(mock_file)
    
    assert success is True
    assert "carregado" in message
    assert isinstance(agent_instance.df, pd.DataFrame)
    assert agent_instance.df.shape == (4, 5)
    assert agent_instance.filename == "test.csv"

def test_pre_analysis(agent_instance, sample_csv_content):
    """
    Testa a funcionalidade de pré-análise.
    Esta função não depende da API Gemini.
    """
    # Setup: Carregar dados no agente
    mock_file = MagicMock()
    mock_file.name = "test.csv"
    mock_file.getvalue.return_value = sample_csv_content.encode('utf-8')
    agent_instance.load_file(mock_file)

    # Execução
    result = agent_instance.pre_analysis()

    # Asserções
    assert result is not None
    assert "schema" in result
    assert "suggested_queries" in result
    assert len(result['suggested_queries']) > 0
    assert result['schema'].shape == (5, 3) # 5 colunas, 3 propriedades (Nome, Tipo, Nulos)

# Usamos @patch para interceptar a chamada à API Gemini
@patch('google.generativeai.GenerativeModel.generate_content')
def test_answer_query_with_gemini_mock(mock_generate_content, agent_instance, sample_csv_content):
    """
    Testa a integração com a API Gemini usando um mock.
    Verifica se o agente consegue extrair, executar o código retornado e produzir o resultado correto.
    """
    # 1. Configuração do Mock:
    # Criamos um objeto de resposta falso que simula a resposta da API Gemini.
    mock_response = MagicMock()
    # A resposta simulada contém um bloco de código Python.
    mock_response.text = """
    Claro, aqui está o código para calcular a média de idade:
    ```python
    result = df['Idade'].mean()
    ```
    """
    # Configuramos o mock para retornar nosso objeto falso quando for chamado.
    mock_generate_content.return_value = mock_response

    # 2. Setup do Teste:
    # Carregamos os dados no agente para que `df` exista.
    mock_file = MagicMock()
    mock_file.name = "test.csv"
    mock_file.getvalue.return_value = sample_csv_content.encode('utf-8')
    agent_instance.load_file(mock_file)

    # 3. Execução:
    # Chamamos o método que, internamente, tentaria chamar a API Gemini.
    response = agent_instance.answer_query("Qual a média de idade?")

    # 4. Asserções:
    # Verificamos se a função mockada (generate_content) foi chamada exatamente uma vez.
    mock_generate_content.assert_called_once()
    
    # Verificamos se o resultado final está correto.
    # O agente deve ter executado `df['Idade'].mean()` e retornado o valor.
    # Média de (28, 35, 22, 45) é 32.5.
    assert response['type'] == 'text'
    assert response['content'] == "32.5"