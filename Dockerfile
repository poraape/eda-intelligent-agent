# Dockerfile
# Usa uma imagem base oficial do Python
FROM python:3.11-slim

# Define o diretório de trabalho no contêiner
WORKDIR /app

# Copia os arquivos de dependências
COPY requirements.txt ./

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação para o diretório de trabalho
COPY . .

# Expõe a porta que o Streamlit usa
EXPOSE 8501

# Define uma variável de ambiente para o Streamlit
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Comando para rodar a aplicação quando o contêiner iniciar
ENTRYPOINT ["streamlit", "run", "main_app.py", "--server.port=8501", "--server.address=0.0.0.0"]