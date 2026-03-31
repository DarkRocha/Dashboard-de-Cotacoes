"""
Módulo responsável pelo armazenamento local dos dados.

Gerencia a leitura e escrita de arquivos CSV para persistência
do histórico de cotações no diretório 'data/'.
"""

import os
from pathlib import Path
from datetime import datetime

import pandas as pd


# Diretório padrão para armazenamento de dados
DATA_DIR = Path(__file__).parent.parent / "data"


def _ensure_data_dir(data_dir: Path | None = None) -> Path:
    """
    Garante que o diretório de dados existe.

    Args:
        data_dir: Diretório customizado (usa DATA_DIR se None)

    Returns:
        Caminho do diretório de dados
    """
    target = data_dir or DATA_DIR
    target.mkdir(parents=True, exist_ok=True)
    return target


def _get_filename(symbol: str) -> str:
    """
    Gera o nome do arquivo CSV para um ativo.

    Args:
        symbol: Símbolo do ativo

    Returns:
        Nome do arquivo (ex: AAPL_history.csv)
    """
    # Remove caracteres inválidos para nomes de arquivo
    safe_name = symbol.upper().replace("/", "_").replace("\\", "_").replace(".", "_")
    return f"{safe_name}_history.csv"


def save_history(
    df: pd.DataFrame,
    symbol: str,
    data_dir: Path | None = None,
) -> str:
    """
    Salva o histórico de preços em um arquivo CSV.

    Se o arquivo já existir, os dados novos são adicionados
    sem duplicar entradas (merge por data).

    Args:
        df: DataFrame com os dados de histórico
        symbol: Símbolo do ativo
        data_dir: Diretório customizado para salvar

    Returns:
        Caminho completo do arquivo salvo

    Raises:
        IOError: Se não for possível escrever o arquivo
    """
    target_dir = _ensure_data_dir(data_dir)
    filename = _get_filename(symbol)
    filepath = target_dir / filename

    try:
        if filepath.exists():
            # Carrega dados existentes
            existing_df = pd.read_csv(str(filepath))

            # Combina dados existentes com novos, removendo duplicatas
            combined = pd.concat([existing_df, df], ignore_index=True)

            if "Date" in combined.columns:
                combined = combined.drop_duplicates(subset=["Date"], keep="last")
                combined = combined.sort_values("Date").reset_index(drop=True)
            else:
                combined = combined.drop_duplicates(keep="last").reset_index(drop=True)

            combined.to_csv(str(filepath), index=False)
        else:
            df.to_csv(str(filepath), index=False)

        return str(filepath)

    except Exception as e:
        raise IOError(
            f"Erro ao salvar arquivo '{filepath}': {e}"
        ) from e


def load_history(
    symbol: str,
    data_dir: Path | None = None,
) -> pd.DataFrame | None:
    """
    Carrega o histórico de preços de um arquivo CSV local.

    Args:
        symbol: Símbolo do ativo
        data_dir: Diretório customizado para leitura

    Returns:
        DataFrame com os dados ou None se o arquivo não existir
    """
    target_dir = _ensure_data_dir(data_dir)
    filename = _get_filename(symbol)
    filepath = target_dir / filename

    if not filepath.exists():
        return None

    try:
        df = pd.read_csv(str(filepath))
        return df
    except Exception:
        return None


def list_saved_assets(data_dir: Path | None = None) -> list[dict]:
    """
    Lista todos os ativos com dados salvos localmente.

    Args:
        data_dir: Diretório customizado para buscar

    Returns:
        Lista de dicionários com informações dos arquivos salvos:
        [{'symbol': str, 'file': str, 'size_kb': float, 'records': int}]
    """
    target_dir = _ensure_data_dir(data_dir)
    assets = []

    for file in sorted(target_dir.glob("*_history.csv")):
        try:
            # Extrai o símbolo do nome do arquivo
            symbol = file.stem.replace("_history", "")
            size_kb = file.stat().st_size / 1024

            # Conta registros
            df = pd.read_csv(str(file))
            records = len(df)

            # Pega data da última modificação
            mod_time = datetime.fromtimestamp(file.stat().st_mtime)

            assets.append(
                {
                    "symbol": symbol,
                    "file": file.name,
                    "size_kb": round(size_kb, 2),
                    "records": records,
                    "last_modified": mod_time.strftime("%Y-%m-%d %H:%M"),
                }
            )
        except Exception:
            continue

    return assets


def delete_history(
    symbol: str,
    data_dir: Path | None = None,
) -> bool:
    """
    Remove o arquivo de histórico de um ativo.

    Args:
        symbol: Símbolo do ativo
        data_dir: Diretório customizado

    Returns:
        True se o arquivo foi removido, False se não existia
    """
    target_dir = _ensure_data_dir(data_dir)
    filename = _get_filename(symbol)
    filepath = target_dir / filename

    if filepath.exists():
        filepath.unlink()
        return True

    return False


def export_all_to_single_csv(
    data_dir: Path | None = None,
    output_file: str = "all_assets_combined.csv",
) -> str | None:
    """
    Exporta todos os dados salvos em um único arquivo CSV consolidado.

    Args:
        data_dir: Diretório de dados
        output_file: Nome do arquivo de saída

    Returns:
        Caminho do arquivo consolidado ou None se não houver dados
    """
    target_dir = _ensure_data_dir(data_dir)
    all_data = []

    for file in target_dir.glob("*_history.csv"):
        try:
            symbol = file.stem.replace("_history", "")
            df = pd.read_csv(str(file))
            df["Symbol"] = symbol
            all_data.append(df)
        except Exception:
            continue

    if not all_data:
        return None

    combined = pd.concat(all_data, ignore_index=True)
    output_path = target_dir / output_file
    combined.to_csv(str(output_path), index=False)

    return str(output_path)
