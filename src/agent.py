# src/agent.py
import io
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from typing import List, Dict, Any, Optional, Tuple

from src.config import settings
from src.utils import handle_zip_file

class EDAAgentPro:
    """
    Facade orquestradora que utiliza a API Gemini para interpretar
    perguntas e gerar código Python para análise de dados.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("A chave da API Gemini é necessária.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(settings['llm']['model_name'])
        
        self.df: Optional[pd.DataFrame] = None
        self.filename: Optional[str] = None
        self.is_sampled: bool = False
        self.original_shape: Optional[Tuple[int, int]] = None
        self.memory_log: List[Dict[str, Any]] = []

    def load_file(self, uploaded_file) -> Tuple[bool, str]:
        """
        Carrega e valida um arquivo (CSV ou ZIP), aplicando a lógica de amostragem adaptativa.
        """
        try:
            self.filename = uploaded_file.name
            file_content = uploaded_file.getvalue()
            
            if self.filename.lower().endswith('.csv'):
                self.df = pd.read_csv(io.BytesIO(file_content))
            elif self.filename.lower().endswith('.zip'):
                result = handle_zip_file(file_content)
                if result:
                    self.filename, self.df = result
                else:
                    return False, "Nenhum arquivo CSV encontrado no ZIP."
            else:
                return False, "Formato de arquivo não suportado. Use CSV ou ZIP."

            self.original_shape = self.df.shape
            threshold = settings['file_limits']['sampling_threshold_rows']
            if len(self.df) > threshold:
                self.is_sampled = True
                sample_size = settings['file_limits']['sampling_rows']
                self.df = self.df.sample(n=sample_size, random_state=42)
                msg = (f"Arquivo '{self.filename}' carregado. "
                       f"Dataset grande ({self.original_shape[0]} linhas), "
                       f"usando uma amostra de {len(self.df)} linhas.")
            else:
                self.is_sampled = False
                msg = f"Arquivo '{self.filename}' ({self.original_shape[0]} linhas) carregado."
            
            self._log_interaction("load_file", {"filename": self.filename}, msg)
            return True, msg
        except Exception as e:
            return False, f"Erro ao processar o arquivo: {str(e)}"

    def pre_analysis(self) -> Optional[Dict[str, Any]]:
        """Gera um resumo inicial do dataset e sugere queries."""
        if self.df is None:
            return None

        schema = pd.DataFrame({
            'Coluna': self.df.columns,
            'Tipo de Dado': self.df.dtypes.astype(str),
            'Valores Nulos (%)': (self.df.isnull().sum() * 100 / len(self.df)).round(2)
        })

        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()

        result = {
            "filename": self.filename,
            "original_shape": self.original_shape,
            "is_sampled": self.is_sampled,
            "sampled_shape": self.df.shape if self.is_sampled else None,
            "schema": schema,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "suggested_queries": self._generate_suggested_queries(numeric_cols, categorical_cols)
        }
        self._log_interaction("pre_analysis", {}, result)
        return result

    def _generate_suggested_queries(self, numeric_cols: List[str], categorical_cols: List[str]) -> List[str]:
        """Gera uma lista de perguntas relevantes com base nos tipos de coluna."""
        queries = []
        if len(numeric_cols) > 0:
            queries.append(f"Qual a distribuição da coluna '{numeric_cols[0]}'?")
        if len(categorical_cols) > 0:
            queries.append(f"Mostre a contagem de categorias em '{categorical_cols[0]}'.")
        if len(numeric_cols) > 1:
            queries.append(f"Existe correlação entre as colunas numéricas?")
        
        return queries[:settings['analysis']['num_suggested_queries']]

    def answer_query(self, question: str) -> Dict[str, Any]:
        """
        Usa o Gemini para gerar e executar código Python para responder a uma pergunta.
        """
        if self.df is None:
            return {"type": "error", "content": "Nenhum dado carregado."}

        prompt = self._build_prompt(question)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    max_output_tokens=settings['llm']['max_output_tokens'],
                    temperature=settings['llm']['temperature'],
                )
            )
            
            generated_code = self._extract_python_code(response.text)

            if generated_code:
                result = self._execute_code(generated_code)
                self._log_interaction("answer_query", {"question": question, "code": generated_code}, result)
                return result
            else:
                return {"type": "text", "content": response.text}

        except Exception as e:
            error_msg = f"Ocorreu um erro ao interagir com a API Gemini ou executar o código: {str(e)}"
            self._log_interaction("answer_query", {"question": question}, {"type": "error", "content": error_msg})
            return {"type": "error", "content": error_msg}

    def _build_prompt(self, question: str) -> str:
        """Constrói o prompt para o Gemini."""
        # Usar io.StringIO para capturar a saída de df.info()
        buffer = io.StringIO()
        self.df.info(buf=buffer)
        schema_info = buffer.getvalue()

        return f"""
        Você é um analista de dados especialista. Sua tarefa é ajudar um usuário a analisar um DataFrame do pandas chamado `df`.

        **Contexto do DataFrame (`df`):**
        - Primeiras 5 linhas:
        {self.df.head().to_string()}
        - Esquema e tipos de dados:
        {schema_info}

        **Tarefa:**
        Com base na pergunta do usuário, gere um único bloco de código Python para realizar a análise.
        - Use a variável `df` para se referir ao DataFrame.
        - Para visualizações, use a biblioteca `plotly.express`. O resultado deve ser um objeto de figura do Plotly atribuído a uma variável `fig`.
        - Para resultados tabulares ou textuais, atribua o resultado a uma variável `result` (pode ser um DataFrame, Série ou string).
        - **NÃO** inclua `print()` ou `st.write()`. Apenas gere o código que cria a variável `fig` ou `result`.
        - Responda APENAS com o bloco de código Python dentro de ```python ... ```.

        **Pergunta do Usuário:**
        {question}
        """

    def _extract_python_code(self, text: str) -> Optional[str]:
        """Extrai o código de um bloco de markdown."""
        if "```python" in text:
            return text.split("```python\n")[1].split("```").strip()
        return None

    def _execute_code(self, code: str) -> Dict[str, Any]:
        """
        Executa o código gerado em um ambiente controlado.
        AVISO: `exec` é poderoso e deve ser usado com cautela.
        """
        local_scope = {}
        global_scope = {
            'df': self.df,
            'pd': pd,
            'px': px
        }
        
        exec(code, global_scope, local_scope)

        if 'fig' in local_scope:
            return {"type": "plot", "content": local_scope['fig']}
        elif 'result' in local_scope:
            content = local_scope['result']
            if isinstance(content, (pd.DataFrame, pd.Series)):
                return {"type": "table", "content": content}
            else:
                return {"type": "text", "content": str(content)}
        else:
            return {"type": "text", "content": "O código foi executado, mas não produziu um resultado visível ('fig' ou 'result')."}
            
    def _log_interaction(self, action: str, params: Dict, result: Any):
        self.memory_log.append({"action": action, "params": params, "result": result})