from flask import Flask, request, jsonify
from pytrends.request import TrendReq
import pandas as pd
import time

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'ok',
        'message': 'Trends API esta funcionando',
        'endpoints': {
            '/trends': 'POST - Obtener trending topics'
        }
    })

@app.route('/trends', methods=['POST'])
def get_trends():
    try:
        data = request.json
        query = data.get('query', 'Sevilla')
        geo = data.get('geo', 'ES-AN')
        timeframe = data.get('timeframe', 'now 7-d')
        
        pytrends = TrendReq(hl='es-ES', tz=60, timeout=(10, 25), retries=2, backoff_factor=0.5)
        pytrends.build_payload([query], timeframe=timeframe, geo=geo)
        related = pytrends.related_queries()
        
        rising_topics = []
        top_topics = []
        
        if query in related:
            if 'rising' in related[query] and related[query]['rising'] is not None:
                df_rising = related[query]['rising']
                if not df_rising.empty:
                    for _, row in df_rising.iterrows():
                        value = int(row['value']) if pd.notna(row['value']) else 0
                        rising_topics.append({
                            'query': row['query'],
                            'type': 'RISING',
                            'value': value,
                            'display_value': "Breakout" if value >= 5000 else f"+{value}%"
                        })
            
            if 'top' in related[query] and related[query]['top'] is not None:
                df_top = related[query]['top']
                if not df_top.empty:
                    for _, row in df_top.head(10).iterrows():
                        top_topics.append({
                            'query': row['query'],
                            'type': 'TOP',
                            'value': int(row['value']) if pd.notna(row['value']) else 0,
                            'display_value': f"Indice: {int(row['value'])}"
                        })
        
        agent_summary = f"Analisis de contexto para: \"{query}\"\n"
        if rising_topics:
            agent_summary += "TENDENCIAS EN ALZA (Noticias potenciales):\n"
            for topic
