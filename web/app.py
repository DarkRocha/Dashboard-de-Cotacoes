"""
Servidor Flask que expõe a API REST do Stock Dashboard.

Conecta os módulos existentes (fetcher, storage) a endpoints HTTP
para serem consumidos pelo frontend web.
"""

import sys
import os
from pathlib import Path

# Corrige problema de SSL com curl_cffi quando o caminho contém caracteres especiais
# (ex: 'Cotações'). Copia o certificado para um caminho ASCII-safe.
import certifi
import shutil
import tempfile

_cert_source = certifi.where()
_cert_dest = os.path.join(tempfile.gettempdir(), "cacert.pem")
if not os.path.exists(_cert_dest) or os.path.getmtime(_cert_source) > os.path.getmtime(_cert_dest):
    shutil.copy2(_cert_source, _cert_dest)
os.environ["CURL_CA_BUNDLE"] = _cert_dest
os.environ["REQUESTS_CA_BUNDLE"] = _cert_dest

# Adiciona o diretório raiz ao path para importar os módulos
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from stock_dashboard.fetcher import fetch_current_price, fetch_history, get_asset_type, CRYPTO_MAP
from stock_dashboard.storage import save_history, load_history, list_saved_assets, delete_history

app = Flask(__name__, static_folder="static")
CORS(app)


# ─── Servir o frontend ───────────────────────────────────────────────

@app.route("/")
def index():
    """Serve a página principal do dashboard."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    """Serve arquivos estáticos (CSS, JS, imagens)."""
    return send_from_directory(app.static_folder, path)


# ─── API Endpoints ───────────────────────────────────────────────────

@app.route("/api/quote/<symbol>")
def api_quote(symbol):
    """
    Busca a cotação atual de um ativo.

    GET /api/quote/AAPL
    GET /api/quote/BTC
    GET /api/quote/PETR4
    """
    try:
        data = fetch_current_price(symbol)
        return jsonify({"success": True, "data": data})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except ConnectionError as e:
        return jsonify({"success": False, "error": str(e)}), 503
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro inesperado: {e}"}), 500


@app.route("/api/history/<symbol>")
def api_history(symbol):
    """
    Busca o histórico de preços de um ativo.

    GET /api/history/AAPL?days=30
    """
    days = request.args.get("days", 30, type=int)

    try:
        df = fetch_history(symbol, days=days)

        # Salva automaticamente no CSV
        try:
            save_history(df, symbol)
        except IOError:
            pass

        # Converte o DataFrame para lista de dicts
        records = df.to_dict(orient="records")
        return jsonify({"success": True, "data": records, "symbol": symbol.upper()})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except ConnectionError as e:
        return jsonify({"success": False, "error": str(e)}), 503
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro inesperado: {e}"}), 500


@app.route("/api/saved")
def api_saved():
    """Lista todos os ativos salvos localmente."""
    try:
        assets = list_saved_assets()
        return jsonify({"success": True, "data": assets})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/saved/<symbol>", methods=["DELETE"])
def api_delete(symbol):
    """Remove dados salvos de um ativo."""
    try:
        result = delete_history(symbol)
        if result:
            return jsonify({"success": True, "message": f"Dados de {symbol} removidos."})
        return jsonify({"success": False, "error": "Ativo não encontrado."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/watchlist/suggestions")
def api_suggestions():
    """Retorna ativos populares para sugestão."""
    suggestions = [
        {"symbol": "AAPL", "name": "Apple Inc.", "type": "us_stock"},
        {"symbol": "MSFT", "name": "Microsoft Corp.", "type": "us_stock"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "type": "us_stock"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "type": "us_stock"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "type": "us_stock"},
        {"symbol": "NVDA", "name": "NVIDIA Corp.", "type": "us_stock"},
        {"symbol": "META", "name": "Meta Platforms Inc.", "type": "us_stock"},
        {"symbol": "PETR4", "name": "Petrobras PN", "type": "br_stock"},
        {"symbol": "VALE3", "name": "Vale ON", "type": "br_stock"},
        {"symbol": "ITUB4", "name": "Itaú Unibanco PN", "type": "br_stock"},
        {"symbol": "BBDC4", "name": "Bradesco PN", "type": "br_stock"},
        {"symbol": "ABEV3", "name": "Ambev ON", "type": "br_stock"},
        {"symbol": "BTC", "name": "Bitcoin", "type": "crypto"},
        {"symbol": "ETH", "name": "Ethereum", "type": "crypto"},
        {"symbol": "SOL", "name": "Solana", "type": "crypto"},
        {"symbol": "ADA", "name": "Cardano", "type": "crypto"},
        {"symbol": "XRP", "name": "Ripple", "type": "crypto"},
    ]
    return jsonify({"success": True, "data": suggestions})


@app.route("/api/multi-quote", methods=["POST"])
def api_multi_quote():
    """
    Busca cotações de múltiplos ativos.

    POST /api/multi-quote
    Body: {"symbols": ["AAPL", "BTC", "PETR4"]}
    """
    body = request.get_json()
    symbols = body.get("symbols", [])
    results = []
    errors = []

    for symbol in symbols[:10]:  # Limita a 10 ativos
        try:
            data = fetch_current_price(symbol)
            results.append(data)
        except Exception as e:
            errors.append({"symbol": symbol, "error": str(e)})

    return jsonify({
        "success": True,
        "data": results,
        "errors": errors,
    })


if __name__ == "__main__":
    print("\n[*] Stock Dashboard Web")
    print("=" * 40)
    print("[>] Acesse: http://localhost:5000")
    print("=" * 40)
    print()
    app.run(debug=True, host="0.0.0.0", port=5000)
