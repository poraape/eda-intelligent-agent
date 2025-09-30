# ARCHITECT-X: Agente EDA com Gemini

Este projeto implementa um sistema de Análise Exploratória de Dados (EDA) inteligente, potencializado pela API Google Gemini. Ele funciona como um copiloto de análise, permitindo o upload de arquivos CSV (ou ZIP) e transformando perguntas em linguagem natural em código Python executável para gerar insights, tabelas e visualizações.

## ✨ Funcionalidades-Chave

- **Upload Flexível:** Aceita arquivos `.csv` e `.zip` de até 200MB.
- **Inteligência Artificial (Gemini):** Interpreta perguntas complexas em linguagem natural e gera o código de análise correspondente.
- **Pré-Análise Automática:** Ao carregar um arquivo, o agente exibe o esquema dos dados e sugere perguntas iniciais.
- **Code Interpreter:** Executa o código gerado pelo Gemini em um ambiente seguro para produzir resultados (gráficos, tabelas, texto).
- **Lógica Adaptativa:** Para datasets grandes (>100k linhas), o agente utiliza uma amostragem inteligente para manter a interface rápida.
- **Interface Minimalista:** UI limpa e profissional construída com Streamlit.

## 🏛️ Arquitetura

O sistema utiliza uma arquitetura de **Agente LLM com Ferramentas (Code Interpreter)**.

- **Interface (Streamlit):** `main_app.py` é responsável pela UI e gerenciamento de estado da sessão.
- **Núcleo Lógico (Python + Gemini):** A classe `EDAAgentPro` em `src/agent.py` é a fachada que:
    1.  Constrói um prompt detalhado com o contexto dos dados.
    2.  Chama a API Gemini para gerar código Python.
    3.  Executa o código recebido de forma segura para obter o resultado.
- **Configuração:** O arquivo `config.yaml` permite ajustar parâmetros como modelo do LLM e limites de arquivo.
- **Segurança:** A chave da API é gerenciada via variáveis de ambiente (`.env`) e secrets do ambiente de deploy.

## 🛠️ Stack Tecnológica

- **Linguagem:** Python 3.11+
- **LLM:** Google Gemini API (`gemini-1.5-flash`)
- **Interface:** Streamlit
- **Análise de Dados:** Pandas
- **Visualização:** Plotly
- **Deployment:** Docker, Hugging Face Spaces

## 🚀 Como Executar Localmente

1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd eda-intelligent-agent
    ```

2.  **Configure suas credenciais:**
    - Renomeie o arquivo `.env.example` para `.env`.
    - Abra o arquivo `.env` e insira sua chave da API Gemini.
    ```
    GEMINI_API_KEY="SUA_API_KEY_AQUI"
    ```

3.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

4.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Execute a aplicação Streamlit:**
    ```bash
    streamlit run main_app.py
    ```
    A aplicação estará disponível em `http://localhost:8501`.

## 🚢 Deploy no Hugging Face Spaces

1.  Crie uma conta no [Hugging Face](https://huggingface.co/).
2.  Crie um novo "Space", selecionando "Streamlit" como o SDK e usando o template de Docker.
3.  Conecte o Space ao seu repositório GitHub.
4.  Vá para as configurações do Space, clique em "Secrets" e adicione um novo segredo:
    - **Name:** `GEMINI_API_KEY`
    - **Secret value:** Cole sua chave da API Gemini aqui.
5.  O Hugging Face irá construir e implantar a aplicação. A chave será lida automaticamente pelo `main_app.py`.

---
*Este projeto foi arquitetado e gerado pelo ARCHITECT-X.*