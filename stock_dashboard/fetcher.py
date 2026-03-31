"""
Módulo responsável por buscar cotações de ações e criptomoedas.

Utiliza a biblioteca yfinance para obter dados do Yahoo Finance,
incluindo preço atual e histórico de preços.
"""

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf


# Mapeamento de criptomoedas para seus tickers no Yahoo Finance
CRYPTO_MAP: dict[str, str] = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "ADA": "ADA-USD",
    "XRP": "XRP-USD",
    "DOT": "DOT-USD",
    "DOGE": "DOGE-USD",
    "AVAX": "AVAX-USD",
    "MATIC": "MATIC-USD",
    "LINK": "LINK-USD",
}

# Sufixo para ações brasileiras na B3
B3_SUFFIXES: list[str] = ["3", "4", "5", "6", "11"]


def _resolve_ticker(symbol: str) -> str:
    """
    Resolve o ticker para o formato correto do Yahoo Finance.

    - Criptomoedas (BTC, ETH, etc.) são mapeadas para BTC-USD, ETH-USD...
    - Ações brasileiras (PETR4, VALE3, etc.) recebem o sufixo .SA
    - Ações americanas (AAPL, MSFT, etc.) permanecem inalteradas

    Args:
        symbol: Símbolo do ativo (ex: AAPL, PETR4, BTC)

    Returns:
        Ticker formatado para o Yahoo Finance
    """
    upper = symbol.upper().strip()

    # Verifica se é uma criptomoeda conhecida
    if upper in CRYPTO_MAP:
        return CRYPTO_MAP[upper]

    # Verifica se é uma ação brasileira (termina com número típico da B3)
    if len(upper) >= 5 and upper[-1].isdigit():
        # Ações brasileiras como PETR4, VALE3, BBDC4, etc.
        if not upper.endswith(".SA"):
            return f"{upper}.SA"

    # Ações americanas ou já formatadas
    return upper


def get_asset_type(symbol: str) -> str:
    """
    Identifica o tipo do ativo a partir do símbolo.

    Args:
        symbol: Símbolo do ativo

    Returns:
        Tipo do ativo: 'crypto', 'br_stock' ou 'us_stock'
    """
    upper = symbol.upper().strip()

    if upper in CRYPTO_MAP:
        return "crypto"

    if len(upper) >= 5 and upper[-1].isdigit():
        return "br_stock"

    return "us_stock"


def fetch_current_price(symbol: str) -> dict:
    """
    Busca a cotação atual de um ativo.

    Args:
        symbol: Símbolo do ativo (ex: AAPL, PETR4, BTC)

    Returns:
        Dicionário com informações da cotação:
        {
            'symbol': str,
            'name': str,
            'price': float,
            'currency': str,
            'change': float,
            'change_percent': float,
            'market_cap': float,
            'volume': int,
            'timestamp': str,
            'asset_type': str
        }

    Raises:
        ValueError: Se o ticker for inválido ou não encontrado
        ConnectionError: Se não for possível conectar à API
    """
    ticker = _resolve_ticker(symbol)

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Verifica se o ticker é válido
        if not info or info.get("regularMarketPrice") is None:
            # Tenta buscar pela história recente como fallback
            hist = stock.history(period="1d")
            if hist.empty:
                raise ValueError(
                    f"Ticker '{symbol}' não encontrado. "
                    "Verifique se o símbolo está correto."
                )
            price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Open"].iloc[0])
            change = price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0.0

            return {
                "symbol": symbol.upper(),
                "name": info.get("shortName", symbol.upper()),
                "price": price,
                "currency": info.get("currency", "USD"),
                "change": round(change, 4),
                "change_percent": round(change_pct, 2),
                "market_cap": info.get("marketCap", 0),
                "volume": info.get("volume", 0),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "asset_type": get_asset_type(symbol),
            }

        price = info.get("regularMarketPrice", 0)
        prev_close = info.get("regularMarketPreviousClose", price)
        change = price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0.0

        return {
            "symbol": symbol.upper(),
            "name": info.get("shortName", info.get("longName", symbol.upper())),
            "price": float(price),
            "currency": info.get("currency", "USD"),
            "change": round(float(change), 4),
            "change_percent": round(float(change_pct), 2),
            "market_cap": info.get("marketCap", 0),
            "volume": info.get("volume", 0),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "asset_type": get_asset_type(symbol),
        }

    except ValueError:
        raise
    except Exception as e:
        if "HTTPError" in str(type(e).__name__) or "ConnectionError" in str(
            type(e).__name__
        ):
            raise ConnectionError(
                "Não foi possível conectar ao Yahoo Finance. "
                "Verifique sua conexão com a internet."
            ) from e
        raise ValueError(
            f"Erro ao buscar cotação de '{symbol}': {e}"
        ) from e


def fetch_history(symbol: str, days: int = 30) -> pd.DataFrame:
    """
    Busca o histórico de preços de um ativo nos últimos N dias.

    Args:
        symbol: Símbolo do ativo (ex: AAPL, PETR4, BTC)
        days: Número de dias de histórico (padrão: 30)

    Returns:
        DataFrame com colunas: Date, Open, High, Low, Close, Volume

    Raises:
        ValueError: Se o ticker for inválido ou sem dados
        ConnectionError: Se não for possível conectar à API
    """
    ticker = _resolve_ticker(symbol)

    try:
        stock = yf.Ticker(ticker)

        # Calcula as datas de início e fim
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Busca o histórico
        hist = stock.history(start=start_date, end=end_date)

        if hist.empty:
            raise ValueError(
                f"Nenhum dado histórico encontrado para '{symbol}'. "
                "Verifique se o símbolo está correto."
            )

        # Reseta o índice para ter a coluna Date acessível
        if "Date" not in hist.columns:
            hist = hist.reset_index()
        else:
            hist = hist.reset_index(drop=True)

        # Seleciona e renomeia colunas relevantes
        columns_to_keep = ["Date", "Open", "High", "Low", "Close", "Volume"]
        available_cols = [col for col in columns_to_keep if col in hist.columns]
        hist = hist[available_cols].copy()

        # Converte a coluna Date para string sem timezone
        if "Date" in hist.columns:
            hist["Date"] = pd.to_datetime(hist["Date"]).dt.strftime("%Y-%m-%d")

        # Arredonda valores numéricos
        numeric_cols = ["Open", "High", "Low", "Close"]
        for col in numeric_cols:
            if col in hist.columns:
                hist[col] = hist[col].round(4)

        return hist

    except ValueError:
        raise
    except Exception as e:
        if "HTTPError" in str(type(e).__name__) or "ConnectionError" in str(
            type(e).__name__
        ):
            raise ConnectionError(
                "Não foi possível conectar ao Yahoo Finance. "
                "Verifique sua conexão com a internet."
            ) from e
        raise ValueError(
            f"Erro ao buscar histórico de '{symbol}': {e}"
        ) from e


def search_ticker(query: str) -> list[dict]:
    """
    Busca tickers que correspondem a uma consulta.

    Args:
        query: Termo de busca (nome da empresa ou ticker parcial)

    Returns:
        Lista de dicionários com tickers encontrados
    """
    try:
        results = yf.Ticker(query).info
        if results and results.get("shortName"):
            return [
                {
                    "symbol": query.upper(),
                    "name": results.get("shortName", ""),
                    "type": get_asset_type(query),
                }
            ]
        return []
    except Exception:
        return []
