import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def analyze_sentiment_v2(market_data, aaii_data=None):
    result = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'market_status': 'neutral',
        'confidence': 0.5,
        'recommendations': [],
        'metrics': {}
    }
    
    if aaii_data:
        result['aaii_analysis'] = _analyze_aaii_v2(aaii_data)
    
    return result

def _analyze_aaii_v2(data):
    bull = data.get('bullish', 37.6)
    bear = data.get('bearish', 39.5)
    neutral = data.get('neutral', 22.9)
    
    sentiment_score = bull - bear
    
    return {
        'sentiment_score': sentiment_score,
        'sentiment': 'bearish' if sentiment_score < 0 else ('bullish' if sentiment_score > 10 else 'neutral'),
        'recommendation': '观望' if abs(sentiment_score) < 10 else ('加仓' if sentiment_score < -15 else '减仓')
    }

def get_market_context():
    context = {
        'vix_level': 'normal',
        'market_trend': 'sideways',
        'risk_level': 'medium'
    }
    
    try:
        vix = yf.Ticker('^VIX')
        hist = vix.history(period='5d')
        if not hist.empty:
            current_vix = hist['Close'].iloc[-1]
            if current_vix > 30:
                context['vix_level'] = 'high'
                context['risk_level'] = 'high'
            elif current_vix < 15:
                context['vix_level'] = 'low'
                context['risk_level'] = 'low'
    except:
        pass
    
    return context

def generate_report(market_data, aaii_data=None):
    context = get_market_context()
    sentiment = analyze_sentiment_v2(market_data, aaii_data)
    
    report = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'market_context': context,
        'sentiment_analysis': sentiment,
        'summary': _generate_summary(context, sentiment)
    }
    
    return report

def _generate_summary(context, sentiment):
    risk = context.get('risk_level', 'medium')
    market_status = sentiment.get('market_status', 'neutral')
    
    if risk == 'high' and market_status == 'fear':
        return "市场处于高恐慌状态，VIX指数高企，建议谨慎操作，适当减仓防御"
    elif risk == 'low' and market_status == 'greed':
        return "市场情绪乐观，VIX指数低位，可适当增加仓位但注意回调风险"
    else:
        return "市场情绪中性，维持常规仓位配置，保持定投节奏"
