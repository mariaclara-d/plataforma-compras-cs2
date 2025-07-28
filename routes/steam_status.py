"""
Rota para verificar status da Steam
"""
from flask import Blueprint, jsonify
import requests
import logging

bp = Blueprint('steam_status', __name__)

@bp.route('/api/steam/status')
def steam_status():
    """
    Endpoint simples para verificar se a Steam está funcionando
    """
    try:
        # Tentar fazer uma requisição simples para a Steam API
        response = requests.get(
            'https://api.steampowered.com/ISteamWebAPIUtil/GetServerInfo/v0001/',
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify({
                'status': 'ok',
                'message': 'Steam funcionando normalmente',
                'timestamp': response.headers.get('date', 'unknown')
            })
        elif response.status_code == 503:
            return jsonify({
                'status': 'degraded',
                'message': 'Steam com instabilidade',
                'code': response.status_code
            }), 503
        else:
            return jsonify({
                'status': 'error',
                'message': 'Steam com problemas',
                'code': response.status_code
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({
            'status': 'degraded',
            'message': 'Steam lenta para responder',
            'error': 'timeout'
        }), 504
        
    except requests.exceptions.ConnectionError:
        return jsonify({
            'status': 'error',
            'message': 'Não foi possível conectar com a Steam',
            'error': 'connection_error'
        }), 502
        
    except Exception as e:
        logging.error(f"Erro ao verificar status da Steam: {e}")
        return jsonify({
            'status': 'unknown',
            'message': 'Erro ao verificar status',
            'error': str(e)
        }), 500
