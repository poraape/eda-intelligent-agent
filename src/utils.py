# src/utils.py
import io
import zipfile
import pandas as pd
from typing import Optional, Tuple

def handle_zip_file(file_content: bytes) -> Optional[Tuple[str, pd.DataFrame]]:
    """
    Processa um arquivo ZIP em memória de forma segura.

    Extrai o primeiro arquivo .csv encontrado, evitando a extração para o disco
    para mitigar riscos de segurança como "Path Traversal".

    Args:
        file_content: O conteúdo do arquivo ZIP em bytes.

    Returns:
        Uma tupla contendo o nome do arquivo CSV e o DataFrame, ou None se nenhum CSV for encontrado.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(file_content)) as z:
            # Encontra o primeiro arquivo .csv na lista de arquivos do ZIP
            csv_filename = next((name for name in z.namelist() if name.lower().endswith('.csv')), None)
            
            if csv_filename:
                with z.open(csv_filename) as csv_file:
                    # Tenta ler com diferentes encodings comuns
                    try:
                        df = pd.read_csv(csv_file)
                        return csv_filename, df
                    except UnicodeDecodeError:
                        # Volta ao início do arquivo para tentar outro encoding
                        z.open(csv_filename).seek(0)
                        df = pd.read_csv(z.open(csv_filename), encoding='latin1')
                        return csv_filename, df
    except zipfile.BadZipFile:
        return None
    return None