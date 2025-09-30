# main_app.py
import streamlit as st
import os
from dotenv import load_dotenv
from src.agent import EDAAgentPro
from src.config import settings

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configuração da Página ---
st.set_page_config(
    page_title=settings['ui']['app_title'],
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Estilo CSS Customizado (Minimalista) ---
st.markdown("""
<style>
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    /* Hiding Streamlit's default header and footer */
    #MainMenu, footer {
        visibility: hidden;
    }
    header {
        visibility: hidden;
    }
    /* Styling for the cards */
    .st-emotion-cache-1r6slb0 {
        border: 1px solid #e6e6e6;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)


# --- Gerenciamento de Estado da Sessão ---
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'pre_analysis_done' not in st.session_state:
    st.session_state.pre_analysis_done = False

# --- Barra Lateral (Sidebar) ---
with st.sidebar:
    st.header(settings['ui']['sidebar_header'])
    
    gemini_api_key = st.text_input(
        "Gemini API Key", 
        type="password", 
        help="Obtenha sua chave em aistudio.google.com",
        value=os.getenv("GEMINI_API_KEY", "")
    )

    if gemini_api_key and not st.session_state.agent:
        try:
            st.session_state.agent = EDAAgentPro(api_key=gemini_api_key)
            st.toast("Agente inicializado com sucesso!", icon="🤖")
        except Exception as e:
            st.error(f"Falha ao inicializar o agente: {e}")
    
    if st.session_state.agent:
        uploaded_file = st.file_uploader(
            "Faça o upload de um arquivo CSV ou ZIP",
            type=["csv", "zip"],
            help=f"Limite de {settings['file_limits']['max_file_size_mb']}MB"
        )

        if st.button("Limpar e Resetar"):
            st.session_state.agent = EDAAgentPro(api_key=gemini_api_key)
            st.session_state.messages = []
            st.session_state.pre_analysis_done = False
            st.rerun()
    
    st.info("Seus dados são processados em memória e apagados ao final da sessão.")
    st.warning("A execução de código gerado por IA pode ter riscos. Use com cautela.")

# --- Lógica Principal ---
st.title(settings['ui']['app_title'])
st.markdown("---")

if not st.session_state.agent:
    st.warning("Por favor, insira sua chave da API Gemini na barra lateral para começar.")
    st.stop()

agent: EDAAgentPro = st.session_state.agent

if 'uploaded_file' not in locals():
    uploaded_file = None

if uploaded_file and not agent.df:
    with st.spinner("Processando arquivo..."):
        success, message = agent.load_file(uploaded_file)
        if success:
            st.toast(message, icon="✅")
            pre_analysis_result = agent.pre_analysis()
            st.session_state.messages.append({"role": "assistant", "content": pre_analysis_result})
            st.session_state.pre_analysis_done = True
            st.rerun()
        else:
            st.error(message)
            st.stop()

# --- Exibição da Pré-Análise e Histórico de Chat ---
if st.session_state.pre_analysis_done:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            content = message["content"]
            if isinstance(content, dict) and "schema" in content:
                st.subheader("🔍 Pré-Análise Automática")
                if content['is_sampled']:
                    st.warning(f"Dataset grande! Análise baseada em uma amostra de {content['sampled_shape']} linhas (Original: {content['original_shape']} linhas).")
                st.dataframe(content['schema'])
                st.subheader("💡 Queries Sugeridas")
                for query in content['suggested_queries']:
                    if st.button(query, use_container_width=True):
                        st.session_state.user_query = query
                        st.rerun()
            elif isinstance(content, dict) and "type" in content:
                if content['type'] == 'text': st.write(content['content'])
                elif content['type'] == 'table': st.dataframe(content['content'])
                elif content['type'] == 'plot': st.plotly_chart(content['content'], use_container_width=True)
                elif content['type'] == 'error': st.error(content['content'])
            else:
                st.write(content)

# --- Campo de Input do Usuário ---
if st.session_state.pre_analysis_done:
    query_to_process = st.session_state.pop('user_query', None) or st.chat_input("Faça uma pergunta sobre os dados...")

    if query_to_process:
        st.session_state.messages.append({"role": "user", "content": query_to_process})
        with st.chat_message("user"): st.write(query_to_process)
        with st.spinner("🤖 Gemini está pensando e gerando código..."):
            response = agent.answer_query(query_to_process)
            st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
else:
    if st.session_state.agent:
        st.info("Faça o upload de um arquivo para iniciar a análise.")