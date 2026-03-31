"""
Módulo principal do Stock Dashboard.

Implementa o menu interativo no terminal usando a biblioteca Rich
para uma interface bonita e responsiva.
"""

import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich.text import Text
from rich import box

from stock_dashboard import __version__
from stock_dashboard.fetcher import fetch_current_price, fetch_history, get_asset_type
from stock_dashboard.chart import (
    plot_price_history,
    plot_candlestick,
    plot_volume,
    display_price_summary,
)
from stock_dashboard.storage import (
    save_history,
    load_history,
    list_saved_assets,
    delete_history,
)

# Console global do Rich
console = Console()


def display_header() -> None:
    """Exibe o cabeçalho do dashboard com ASCII art estilizado."""
    header = Text()
    header.append("╔══════════════════════════════════════════════════╗\n", style="bold cyan")
    header.append("║        ", style="bold cyan")
    header.append("📈 STOCK DASHBOARD", style="bold white")
    header.append(f"  v{__version__}", style="dim")
    header.append("            ║\n", style="bold cyan")
    header.append("║    ", style="bold cyan")
    header.append("Cotações em Tempo Real no Terminal", style="italic yellow")
    header.append("       ║\n", style="bold cyan")
    header.append("╚══════════════════════════════════════════════════╝", style="bold cyan")
    console.print(header)
    console.print()


def display_menu() -> None:
    """Exibe o menu principal com as opções disponíveis."""
    table = Table(
        title="Menu Principal",
        box=box.ROUNDED,
        title_style="bold magenta",
        border_style="bright_blue",
        show_header=True,
        header_style="bold green",
    )

    table.add_column("Opção", style="bold cyan", justify="center", width=8)
    table.add_column("Descrição", style="white", width=45)

    table.add_row("1", "🔍  Buscar cotação atual de um ativo")
    table.add_row("2", "📊  Ver histórico de preços (gráfico)")
    table.add_row("3", "📉  Ver gráfico Abertura vs Fechamento")
    table.add_row("4", "📦  Ver volume de negociações")
    table.add_row("5", "💾  Listar dados salvos localmente")
    table.add_row("6", "🗑️   Remover dados de um ativo")
    table.add_row("0", "🚪  Sair")

    console.print(table)
    console.print()


def handle_current_price() -> None:
    """Busca e exibe a cotação atual de um ativo."""
    console.print()
    symbol = Prompt.ask(
        "[bold cyan]Digite o símbolo do ativo[/]",
        default="AAPL",
    ).strip()

    if not symbol:
        console.print("[yellow]⚠️  Nenhum símbolo informado.[/]")
        return

    with console.status(f"[bold green]Buscando cotação de {symbol.upper()}...[/]"):
        try:
            data = fetch_current_price(symbol)
        except ValueError as e:
            console.print(f"\n[bold red]❌ Erro:[/] {e}")
            return
        except ConnectionError as e:
            console.print(f"\n[bold red]🌐 Erro de conexão:[/] {e}")
            return
        except Exception as e:
            console.print(f"\n[bold red]❌ Erro inesperado:[/] {e}")
            return

    # Monta a tabela de resultados
    table = Table(
        title=f"Cotação Atual - {data['name']}",
        box=box.DOUBLE,
        title_style="bold white",
        border_style="green",
    )

    table.add_column("Campo", style="bold cyan", width=20)
    table.add_column("Valor", style="white", width=30)

    # Define a cor da variação
    change_color = "green" if data["change"] >= 0 else "red"
    change_arrow = "▲" if data["change"] >= 0 else "▼"

    # Tipo do ativo
    type_labels = {
        "crypto": "🪙 Criptomoeda",
        "br_stock": "🇧🇷 Ação Brasileira",
        "us_stock": "🇺🇸 Ação Americana",
    }

    table.add_row("Símbolo", data["symbol"])
    table.add_row("Nome", data["name"])
    table.add_row("Tipo", type_labels.get(data["asset_type"], "Desconhecido"))
    table.add_row(
        "Preço",
        f"[bold]{data['currency']} {data['price']:,.4f}[/]",
    )
    table.add_row(
        "Variação",
        f"[{change_color}]{change_arrow} {data['change']:+,.4f} "
        f"({data['change_percent']:+.2f}%)[/]",
    )
    table.add_row("Volume", f"{data['volume']:,}" if data["volume"] else "N/A")
    table.add_row(
        "Market Cap",
        f"{data['market_cap']:,}" if data["market_cap"] else "N/A",
    )
    table.add_row("Atualizado em", data["timestamp"])

    console.print()
    console.print(table)


def handle_price_history() -> None:
    """Busca e exibe o histórico de preços em gráfico."""
    console.print()
    symbol = Prompt.ask(
        "[bold cyan]Digite o símbolo do ativo[/]",
        default="AAPL",
    ).strip()

    if not symbol:
        console.print("[yellow]⚠️  Nenhum símbolo informado.[/]")
        return

    days = IntPrompt.ask(
        "[bold cyan]Quantos dias de histórico?[/]",
        default=30,
    )

    with console.status(
        f"[bold green]Buscando histórico de {symbol.upper()} ({days} dias)...[/]"
    ):
        try:
            df = fetch_history(symbol, days=days)
        except ValueError as e:
            console.print(f"\n[bold red]❌ Erro:[/] {e}")
            return
        except ConnectionError as e:
            console.print(f"\n[bold red]🌐 Erro de conexão:[/] {e}")
            return
        except Exception as e:
            console.print(f"\n[bold red]❌ Erro inesperado:[/] {e}")
            return

    # Salva automaticamente o histórico
    try:
        filepath = save_history(df, symbol)
        console.print(f"\n[dim]💾 Dados salvos em: {filepath}[/]")
    except IOError as e:
        console.print(f"\n[yellow]⚠️  Não foi possível salvar: {e}[/]")

    # Exibe o gráfico
    console.print()
    plot_price_history(df, symbol)

    # Exibe resumo estatístico
    summary = display_price_summary(df, symbol)
    if summary:
        console.print()
        _display_summary_table(summary)


def handle_candlestick() -> None:
    """Exibe gráfico de abertura vs fechamento."""
    console.print()
    symbol = Prompt.ask(
        "[bold cyan]Digite o símbolo do ativo[/]",
        default="AAPL",
    ).strip()

    days = IntPrompt.ask(
        "[bold cyan]Quantos dias de histórico?[/]",
        default=30,
    )

    with console.status(
        f"[bold green]Buscando dados de {symbol.upper()}...[/]"
    ):
        try:
            df = fetch_history(symbol, days=days)
        except (ValueError, ConnectionError) as e:
            console.print(f"\n[bold red]❌ Erro:[/] {e}")
            return

    console.print()
    plot_candlestick(df, symbol)


def handle_volume() -> None:
    """Exibe gráfico de volume de negociações."""
    console.print()
    symbol = Prompt.ask(
        "[bold cyan]Digite o símbolo do ativo[/]",
        default="AAPL",
    ).strip()

    days = IntPrompt.ask(
        "[bold cyan]Quantos dias de histórico?[/]",
        default=30,
    )

    with console.status(
        f"[bold green]Buscando volume de {symbol.upper()}...[/]"
    ):
        try:
            df = fetch_history(symbol, days=days)
        except (ValueError, ConnectionError) as e:
            console.print(f"\n[bold red]❌ Erro:[/] {e}")
            return

    console.print()
    plot_volume(df, symbol)


def handle_list_saved() -> None:
    """Lista todos os ativos com dados salvos localmente."""
    assets = list_saved_assets()

    if not assets:
        console.print(
            "\n[yellow]📂 Nenhum dado salvo localmente. "
            "Busque cotações primeiro![/]"
        )
        return

    table = Table(
        title="📂 Dados Salvos Localmente",
        box=box.ROUNDED,
        title_style="bold white",
        border_style="bright_blue",
    )

    table.add_column("Símbolo", style="bold cyan", justify="center")
    table.add_column("Arquivo", style="white")
    table.add_column("Registros", style="green", justify="right")
    table.add_column("Tamanho", style="yellow", justify="right")
    table.add_column("Última Atualização", style="dim")

    for asset in assets:
        table.add_row(
            asset["symbol"],
            asset["file"],
            str(asset["records"]),
            f"{asset['size_kb']:.1f} KB",
            asset["last_modified"],
        )

    console.print()
    console.print(table)


def handle_delete() -> None:
    """Remove dados salvos de um ativo."""
    console.print()

    # Mostra os dados disponíveis primeiro
    assets = list_saved_assets()
    if not assets:
        console.print("[yellow]📂 Nenhum dado salvo para remover.[/]")
        return

    symbols = [a["symbol"] for a in assets]
    console.print(f"[dim]Ativos salvos: {', '.join(symbols)}[/]")

    symbol = Prompt.ask(
        "[bold cyan]Digite o símbolo para remover[/]",
    ).strip()

    if not symbol:
        return

    confirm = Prompt.ask(
        f"[bold red]Confirma remoção de {symbol.upper()}?[/]",
        choices=["s", "n"],
        default="n",
    )

    if confirm == "s":
        if delete_history(symbol):
            console.print(f"[green]✅ Dados de {symbol.upper()} removidos.[/]")
        else:
            console.print(f"[yellow]⚠️  Nenhum dado encontrado para {symbol.upper()}.[/]")


def _display_summary_table(summary: dict) -> None:
    """
    Exibe uma tabela com o resumo estatístico dos preços.

    Args:
        summary: Dicionário retornado por display_price_summary()
    """
    table = Table(
        title=f"📋 Resumo Estatístico - {summary['symbol']}",
        box=box.SIMPLE_HEAVY,
        title_style="bold white",
        border_style="blue",
    )

    table.add_column("Métrica", style="bold cyan", width=22)
    table.add_column("Valor", style="white", width=20, justify="right")

    variation_color = "green" if summary["variation"] >= 0 else "red"

    table.add_row("Preço Mínimo", f"{summary['min_price']:,.4f}")
    table.add_row("Preço Máximo", f"{summary['max_price']:,.4f}")
    table.add_row("Preço Médio", f"{summary['avg_price']:,.4f}")
    table.add_row("Desvio Padrão", f"{summary['std_dev']:,.4f}")
    table.add_row("Primeiro Preço", f"{summary['first_price']:,.4f}")
    table.add_row("Último Preço", f"{summary['last_price']:,.4f}")
    table.add_row(
        "Variação no Período",
        f"[{variation_color}]{summary['variation']:+.2f}%[/]",
    )
    table.add_row("Total de Dias", str(summary["total_days"]))

    console.print(table)


def main() -> None:
    """Função principal que executa o loop do menu interativo."""
    console.clear()
    display_header()

    # Mapa de opções
    handlers = {
        "1": handle_current_price,
        "2": handle_price_history,
        "3": handle_candlestick,
        "4": handle_volume,
        "5": handle_list_saved,
        "6": handle_delete,
    }

    while True:
        display_menu()

        choice = Prompt.ask(
            "[bold green]Escolha uma opção[/]",
            choices=["0", "1", "2", "3", "4", "5", "6"],
            default="1",
        )

        if choice == "0":
            console.print(
                Panel(
                    "[bold cyan]Obrigado por usar o Stock Dashboard! 👋[/]",
                    border_style="green",
                )
            )
            sys.exit(0)

        handler = handlers.get(choice)
        if handler:
            handler()

        console.print()
        Prompt.ask("[dim]Pressione Enter para continuar...[/]", default="")
        console.clear()
        display_header()


if __name__ == "__main__":
    main()
