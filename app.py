from flask import Flask, request, jsonify
from pytrends.request import TrendReq
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'ok',
        'message': 'Trends API funcionando'
    })

@app.route('/trends', methods=['POST'])
def get_trends():
    try:
        data = request.json
        query = data.get('query', 'Sevilla')
        geo = data.get('geo', 'ES-AN')
        timeframe = data.get('timeframe', 'now 7-d')
        
        pytrends = TrendReq(hl='es-ES', tz=60)
        pytrends.build_payload([query], timeframe=timeframe, geo=geo)
        related = pytrends.related_queries()
        
        rising_topics = []
        top_topics = []
        
        if query in related:
            if 'rising' in related[query] and related[query]['rising'] is not None:
                df_rising = related[query]['rising']
                if not df_rising.empty:
                    for index, row in df_rising.iterrows():
                        value = int(row['value']) if pd.notna(row['value']) else 0
                        rising_topics.append({
                            'query': row['query'],
                            'type': 'RISING',
                            'value': value,
                            'display_value': 'Breakout' if value >= 5000 else '+' + str(value) + '%'
                        })
            
            if 'top' in related[query] and related[query]['top'] is not None:
                df_top = related[query]['top']
                if not df_top.empty:
                    for index, row in df_top.head(10).iterrows():
                        val = int(row['value']) if pd.notna(row['value']) else 0
                        top_topics.append({
                            'query': row['query'],
                            'type': 'TOP',
                            'value': val,
                            'display_value': 'Indice: ' + str(val)
                        })
        
        summary_lines = ['Analisis de contexto para: "' + query + '"']
        
        if rising_topics:
            summary_lines.append('TENDENCIAS EN ALZA:')
            for i in range(min(5, len(rising_topics))):
                topic = rising_topics[i]
                summary_lines.append('  - "' + topic['query'] + '" (' + topic['display_value'] + ')')
        
        if top_topics:
            summary_lines.append('INTERES HABITUAL:')
            for i in range(min(5, len(top_topics))):
                topic = top_topics[i]
                summary_lines.append('  - "' + topic['query'] + '" (' + topic['display_value'] + ')')
        
        agent_summary = '\n'.join(summary_lines)
        
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
