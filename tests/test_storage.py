"""
Testes automatizados para o módulo storage.

Cobre as funções de salvar, carregar, listar e remover
dados CSV localmente.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from stock_dashboard.storage import (
    save_history,
    load_history,
    list_saved_assets,
    delete_history,
    _get_filename,
)


@pytest.fixture
def temp_data_dir():
    """Cria um diretório temporário para testes e remove ao final."""
    tmp = Path(tempfile.mkdtemp())
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def sample_df():
    """Cria um DataFrame de exemplo para testes."""
    return pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "Open": [100.0, 101.0, 102.0],
            "High": [101.0, 102.0, 103.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [100.5, 101.5, 102.5],
            "Volume": [1000000, 1100000, 1200000],
        }
    )


class TestGetFilename:
    """Testes para geração de nomes de arquivo."""

    def test_simple_symbol(self):
        """Verifica nome de arquivo para símbolo simples."""
        assert _get_filename("AAPL") == "AAPL_history.csv"

    def test_special_characters(self):
        """Verifica tratamento de caracteres especiais."""
        assert _get_filename("BTC/USD") == "BTC_USD_history.csv"

    def test_case_conversion(self):
        """Verifica conversão para maiúsculas."""
        assert _get_filename("aapl") == "AAPL_history.csv"


class TestSaveHistory:
    """Testes para salvamento de histórico em CSV."""

    def test_save_new_file(self, temp_data_dir, sample_df):
        """Verifica salvamento de novo arquivo CSV."""
        filepath = save_history(sample_df, "AAPL", data_dir=temp_data_dir)

        assert Path(filepath).exists()
        loaded = pd.read_csv(filepath)
        assert len(loaded) == 3

    def test_save_merge_existing(self, temp_data_dir, sample_df):
        """Verifica merge com dados existentes sem duplicação."""
        # Salva dados iniciais
        save_history(sample_df, "AAPL", data_dir=temp_data_dir)

        # Cria novos dados com sobreposição
        new_df = pd.DataFrame(
            {
                "Date": ["2024-01-03", "2024-01-04"],
                "Open": [102.0, 103.0],
                "High": [103.0, 104.0],
                "Low": [101.0, 102.0],
                "Close": [102.5, 103.5],
                "Volume": [1200000, 1300000],
            }
        )

        filepath = save_history(new_df, "AAPL", data_dir=temp_data_dir)
        loaded = pd.read_csv(filepath)

        # Deve ter 4 registros (sem duplicar 2024-01-03)
        assert len(loaded) == 4


class TestLoadHistory:
    """Testes para carregamento de histórico do CSV."""

    def test_load_existing(self, temp_data_dir, sample_df):
        """Verifica carregamento de arquivo existente."""
        save_history(sample_df, "AAPL", data_dir=temp_data_dir)
        result = load_history("AAPL", data_dir=temp_data_dir)

        assert result is not None
        assert len(result) == 3

    def test_load_nonexistent(self, temp_data_dir):
        """Verifica retorno None para arquivo inexistente."""
        result = load_history("XXXYZ", data_dir=temp_data_dir)
        assert result is None


class TestListAndDelete:
    """Testes para listagem e remoção de dados."""

    def test_list_saved_assets(self, temp_data_dir, sample_df):
        """Verifica listagem de ativos salvos."""
        save_history(sample_df, "AAPL", data_dir=temp_data_dir)
        save_history(sample_df, "MSFT", data_dir=temp_data_dir)

        assets = list_saved_assets(data_dir=temp_data_dir)
        symbols = [a["symbol"] for a in assets]

        assert len(assets) == 2
        assert "AAPL" in symbols
        assert "MSFT" in symbols

    def test_delete_existing(self, temp_data_dir, sample_df):
        """Verifica remoção de dados existentes."""
        save_history(sample_df, "AAPL", data_dir=temp_data_dir)
        result = delete_history("AAPL", data_dir=temp_data_dir)

        assert result is True
        assert load_history("AAPL", data_dir=temp_data_dir) is None

    def test_delete_nonexistent(self, temp_data_dir):
        """Verifica retorno False ao remover ativo inexistente."""
        result = delete_history("XXXYZ", data_dir=temp_data_dir)
        assert result is False
