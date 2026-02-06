from flask import Flask, request, jsonify
from pytrends.request import TrendReq
import pandas as pd
import time

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'ok',
        'message': 'Trends API está funcionando',
        'endpoints': {
            '/trends': 'POST - Obtener trending topics'
        }
    })

@app.route('/trends', methods=['POST'])
def get_trends():
    try:
        data = request.json
        query = data.get('query', 'Sevilla')
        geo = data.get('geo', 'ES-AN')  # ES-AN = Andalucía, ES = España
        timeframe = data.get('timeframe', 'now 7-d')
        
        # Inicializar pytrends (con retries por si Google bloquea temporalmente)
        pytrends = TrendReq(hl='es-ES', tz=60, timeout=(10, 25), retries=2, backoff_factor=0.5)
        
        # Construir payload
        pytrends.build_payload([query], timeframe=timeframe, geo=geo)
        
        # Obtener related queries
        related = pytrends.related_queries()
        
        # Formatear datos como SerpAPI
        rising_topics = []
        top_topics = []
        
        if query in related:
            # RISING topics (tendencias en alza)
            if 'rising' in related[query] and related[query]['rising'] is not None:
                df_rising = related[query]['rising']
                if not df_rising.empty:
                    for _, row in df_rising.iterrows():
                        value = int(row['value']) if pd.notna(row['value']) else 0
                        rising_topics.append({
                            'query': row['query'],
                            'type': 'RISING 🚀',
                            'value': value,
                            'display_value': "Breakout" if value >= 5000 else f"+{value}%"
                        })
            
            # TOP topics (búsquedas más populares)
            if 'top' in related[query] and related[query]['top'] is not None:
                df_top = related[query]['top']
                if not df_top.empty:
                    for _, row in df_top.head(10).iterrows():
                        top_topics.append({
                            'query': row['query'],
                            'type': 'TOP 📊',
                            'value': int(row['value']) if pd.notna(row['value']) else 0,
                            'display_value': f"Índice: {int(row['value'])}"
                        })
        
        # Crear resumen tipo SerpAPI
        agent_summary = f"Análisis de contexto para: \"{query}\"\n"
        if rising_topics:
            agent_summary += "⚠️ TENDENCIAS EN ALZA (Noticias potenciales):\n"
            for topic in rising_topics[:5]:
                agent_summary += f"   - \"{topic['query']}\" ({topic['display_value']})\n"
        if top_topics:
            agent_summary += "ℹ️ INTERÉS HABITUAL (Contexto):\n"
            for topic in top_topics[:5]:
                agent_summary += f"   - \"{topic['query']}\" ({topic['display_value']})\n"
        
        return jsonify({
            'tendencias': [{
                'mode': 'specific_topic_analysis',
                'base_query': query,
                'agent_summary': agent_summary,
                'topics_data': rising_topics + top_topics
            }]
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Error al obtener tendencias'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```