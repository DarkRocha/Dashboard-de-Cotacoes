"""
Stock Dashboard - Dashboard de cotações financeiras no terminal.

Um dashboard CLI que busca preços de ações e criptomoedas em tempo real,
exibe histórico em gráfico e salva os dados localmente.
"""

__version__ = "1.0.0"
__author__ = "Gabriel"

# Corrige problema de SSL com curl_cffi quando o caminho do projeto
# contém caracteres especiais (ex: 'Cotações').
# Copia o certificado para um caminho ASCII-safe no temp do sistema.
import os as _os
import shutil as _shutil
import tempfile as _tempfile

import certifi as _certifi

_cert_source = _certifi.where()
_cert_dest = _os.path.join(_tempfile.gettempdir(), "cacert.pem")
if not _os.path.exists(_cert_dest) or _os.path.getmtime(_cert_source) > _os.path.getmtime(_cert_dest):
    _shutil.copy2(_cert_source, _cert_dest)
_os.environ["CURL_CA_BUNDLE"] = _cert_dest
_os.environ["REQUESTS_CA_BUNDLE"] = _cert_dest

