"""
Módulo responsável por gerar gráficos no terminal.

Utiliza a biblioteca plotext para renderizar gráficos de preços
diretamente no terminal, com suporte a cores e formatação.
"""

import plotext as plt
import pandas as pd


def plot_price_history(
    df: pd.DataFrame,
    symbol: str,
    title: str | None = None,
    width: int = 80,
    height: int = 25,
) -> None:
    """
    Exibe um gráfico de preços no terminal usando plotext.

    Renderiza o histórico de preços de fechamento como um gráfico
    de linhas diretamente no terminal.

    Args:
        df: DataFrame com colunas 'Date' e 'Close'
        symbol: Símbolo do ativo para o título
        title: Título personalizado (opcional)
        width: Largura do gráfico em caracteres
        height: Altura do gráfico em linhas
    """
    if df.empty:
        print("⚠️  Sem dados para exibir o gráfico.")
        return

    # Limpa o gráfico anterior
    plt.clear_figure()

    # Prepara os dados
    dates = df["Date"].tolist()
    closes = df["Close"].tolist()

    # Configura o tamanho do gráfico
    plt.plotsize(width, height)

    # Plota o gráfico de linhas
    plt.plot(
        closes,
        label=f"{symbol.upper()} - Fechamento",
        marker="braille",
    )

    # Configura o título
    chart_title = title or f"📈 Histórico de Preços - {symbol.upper()}"
    plt.title(chart_title)

    # Configura os eixos
    plt.xlabel("Dias")
    plt.ylabel("Preço")

    # Adiciona rótulos do eixo X (datas) de forma espaçada
    if len(dates) > 0:
        step = max(1, len(dates) // 8)  # Mostra no máximo ~8 rótulos
        xticks_pos = list(range(0, len(dates), step))
        xticks_labels = [dates[i] for i in xticks_pos]
        plt.xticks(xticks_pos, xticks_labels)

    # Configura o tema
    plt.theme("dark")

    # Exibe o gráfico
    plt.show()


def plot_candlestick(
    df: pd.DataFrame,
    symbol: str,
    width: int = 80,
    height: int = 25,
) -> None:
    """
    Exibe um gráfico com barras de preço (simulação de candlestick).

    Mostra o preço de abertura e fechamento como barras,
    permitindo visualizar a variação diária.

    Args:
        df: DataFrame com colunas 'Date', 'Open', 'Close'
        symbol: Símbolo do ativo
        width: Largura do gráfico
        height: Altura do gráfico
    """
    if df.empty:
        print("⚠️  Sem dados para exibir o gráfico.")
        return

    # Limpa o gráfico anterior
    plt.clear_figure()

    # Prepara os dados
    opens = df["Open"].tolist()
    closes = df["Close"].tolist()

    # Configura o tamanho do gráfico
    plt.plotsize(width, height)

    # Plota abertura e fechamento
    plt.plot(opens, label="Abertura", marker="braille")
    plt.plot(closes, label="Fechamento", marker="braille")

    # Configurações visuais
    plt.title(f"📊 Abertura vs Fechamento - {symbol.upper()}")
    plt.xlabel("Dias")
    plt.ylabel("Preço")
    plt.theme("dark")

    # Exibe o gráfico
    plt.show()


def plot_volume(
    df: pd.DataFrame,
    symbol: str,
    width: int = 80,
    height: int = 15,
) -> None:
    """
    Exibe um gráfico de volume de negociações no terminal.

    Args:
        df: DataFrame com colunas 'Date' e 'Volume'
        symbol: Símbolo do ativo
        width: Largura do gráfico
        height: Altura do gráfico
    """
    if df.empty or "Volume" not in df.columns:
        print("⚠️  Sem dados de volume para exibir.")
        return

    # Limpa o gráfico anterior
    plt.clear_figure()

    # Prepara os dados
    volumes = df["Volume"].tolist()

    # Configura o tamanho do gráfico
    plt.plotsize(width, height)

    # Plota o volume como barras
    plt.bar(
        list(range(len(volumes))),
        volumes,
        label=f"Volume - {symbol.upper()}",
    )

    # Configurações visuais
    plt.title(f"📊 Volume de Negociações - {symbol.upper()}")
    plt.xlabel("Dias")
    plt.ylabel("Volume")
    plt.theme("dark")

    # Exibe o gráfico
    plt.show()


def display_price_summary(df: pd.DataFrame, symbol: str) -> dict:
    """
    Calcula e retorna um resumo estatístico dos preços.

    Args:
        df: DataFrame com a coluna 'Close'
        symbol: Símbolo do ativo

    Returns:
        Dicionário com estatísticas: min, max, média, variação
    """
    if df.empty:
        return {}

    closes = df["Close"]

    summary = {
        "symbol": symbol.upper(),
        "min_price": round(float(closes.min()), 4),
        "max_price": round(float(closes.max()), 4),
        "avg_price": round(float(closes.mean()), 4),
        "std_dev": round(float(closes.std()), 4),
        "first_price": round(float(closes.iloc[0]), 4),
        "last_price": round(float(closes.iloc[-1]), 4),
        "variation": round(
            float(((closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]) * 100), 2
        ),
        "total_days": len(closes),
    }

    return summary
