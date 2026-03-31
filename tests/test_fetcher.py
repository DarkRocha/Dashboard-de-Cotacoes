"""
Testes automatizados para o módulo fetcher.

Cobre as funções principais de busca de cotações e histórico,
incluindo cenários de sucesso e tratamento de erros.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from stock_dashboard.fetcher import (
    _resolve_ticker,
    get_asset_type,
    fetch_current_price,
    fetch_history,
)


# ============================================================
# Testes para _resolve_ticker
# ============================================================


class TestResolveTicker:
    """Testes para a resolução de tickers."""

    def test_crypto_btc(self):
        """Verifica se BTC é resolvido para BTC-USD."""
        assert _resolve_ticker("BTC") == "BTC-USD"

    def test_crypto_eth(self):
        """Verifica se ETH é resolvido para ETH-USD."""
        assert _resolve_ticker("ETH") == "ETH-USD"

    def test_crypto_case_insensitive(self):
        """Verifica que a resolução é case-insensitive."""
        assert _resolve_ticker("btc") == "BTC-USD"
        assert _resolve_ticker("Eth") == "ETH-USD"

    def test_brazilian_stock(self):
        """Verifica se ações brasileiras recebem sufixo .SA."""
        assert _resolve_ticker("PETR4") == "PETR4.SA"
        assert _resolve_ticker("VALE3") == "VALE3.SA"
        assert _resolve_ticker("BBDC4") == "BBDC4.SA"

    def test_brazilian_stock_already_formatted(self):
        """Verifica que ações já com .SA não são duplicadas."""
        assert _resolve_ticker("PETR4.SA") == "PETR4.SA"

    def test_us_stock_unchanged(self):
        """Verifica que ações americanas permanecem inalteradas."""
        assert _resolve_ticker("AAPL") == "AAPL"
        assert _resolve_ticker("MSFT") == "MSFT"
        assert _resolve_ticker("GOOGL") == "GOOGL"

    def test_whitespace_handling(self):
        """Verifica que espaços são removidos."""
        assert _resolve_ticker("  AAPL  ") == "AAPL"
        assert _resolve_ticker(" BTC ") == "BTC-USD"


# ============================================================
# Testes para get_asset_type
# ============================================================


class TestGetAssetType:
    """Testes para identificação do tipo de ativo."""

    def test_crypto_type(self):
        """Verifica identificação de criptomoedas."""
        assert get_asset_type("BTC") == "crypto"
        assert get_asset_type("ETH") == "crypto"
        assert get_asset_type("SOL") == "crypto"

    def test_brazilian_stock_type(self):
        """Verifica identificação de ações brasileiras."""
        assert get_asset_type("PETR4") == "br_stock"
        assert get_asset_type("VALE3") == "br_stock"
        assert get_asset_type("ITUB4") == "br_stock"

    def test_us_stock_type(self):
        """Verifica identificação de ações americanas."""
        assert get_asset_type("AAPL") == "us_stock"
        assert get_asset_type("MSFT") == "us_stock"
        assert get_asset_type("TSLA") == "us_stock"


# ============================================================
# Testes para fetch_current_price (com mock)
# ============================================================


class TestFetchCurrentPrice:
    """Testes para busca de cotação atual com dados mockados."""

    @patch("stock_dashboard.fetcher.yf.Ticker")
    def test_fetch_price_success(self, mock_ticker_class):
        """Verifica busca de cotação com dados válidos."""
        # Configura o mock
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "shortName": "Apple Inc.",
            "regularMarketPrice": 175.50,
            "regularMarketPreviousClose": 174.00,
            "currency": "USD",
            "marketCap": 2800000000000,
            "volume": 55000000,
        }
        mock_ticker_class.return_value = mock_ticker

        result = fetch_current_price("AAPL")

        assert result["symbol"] == "AAPL"
        assert result["name"] == "Apple Inc."
        assert result["price"] == 175.50
        assert result["currency"] == "USD"
        assert result["asset_type"] == "us_stock"
        assert result["change"] == pytest.approx(1.50, abs=0.01)

    @patch("stock_dashboard.fetcher.yf.Ticker")
    def test_fetch_price_invalid_ticker(self, mock_ticker_class):
        """Verifica tratamento de ticker inválido."""
        mock_ticker = MagicMock()
        mock_ticker.info = {"regularMarketPrice": None}
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker

        with pytest.raises(ValueError, match="não encontrado"):
            fetch_current_price("XXXYZ123")

    @patch("stock_dashboard.fetcher.yf.Ticker")
    def test_fetch_price_crypto(self, mock_ticker_class):
        """Verifica busca de cotação de criptomoeda."""
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "shortName": "Bitcoin USD",
            "regularMarketPrice": 65000.00,
            "regularMarketPreviousClose": 64500.00,
            "currency": "USD",
            "marketCap": 1300000000000,
            "volume": 30000000000,
        }
        mock_ticker_class.return_value = mock_ticker

        result = fetch_current_price("BTC")

        assert result["symbol"] == "BTC"
        assert result["price"] == 65000.00
        assert result["asset_type"] == "crypto"


# ============================================================
# Testes para fetch_history (com mock)
# ============================================================


class TestFetchHistory:
    """Testes para busca de histórico de preços com dados mockados."""

    @patch("stock_dashboard.fetcher.yf.Ticker")
    def test_fetch_history_success(self, mock_ticker_class):
        """Verifica busca de histórico com dados válidos."""
        # Cria DataFrame de exemplo simulando retorno do yfinance
        mock_data = pd.DataFrame(
            {
                "Date": pd.date_range("2024-01-01", periods=5, freq="D"),
                "Open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "High": [101.0, 102.0, 103.0, 104.0, 105.0],
                "Low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "Close": [100.5, 101.5, 102.5, 103.5, 104.5],
                "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
            }
        )
        mock_data.index = mock_data["Date"]

        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_data
        mock_ticker_class.return_value = mock_ticker

        result = fetch_history("AAPL", days=5)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert "Close" in result.columns
        assert "Date" in result.columns

    @patch("stock_dashboard.fetcher.yf.Ticker")
    def test_fetch_history_empty(self, mock_ticker_class):
        """Verifica tratamento quando não há dados históricos."""
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker

        with pytest.raises(ValueError, match="Nenhum dado histórico"):
            fetch_history("INVALIDTICKER")
