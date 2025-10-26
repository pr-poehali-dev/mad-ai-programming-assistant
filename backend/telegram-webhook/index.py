import json
import os
import psycopg2
from typing import Dict, Any

def get_ai_response_from_chat(message: str, chat_id: int, api_key: str) -> str:
    import urllib.request
    
    chat_api_url = os.environ.get('CHAT_API_URL', 'https://functions.poehali.dev/chat')
    
    headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': api_key
    }
    
    data = json.dumps({
        "message": message,
        "chat_id": chat_id
    }).encode()
    
    try:
        req = urllib.request.Request(chat_api_url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result.get('ai_response', {}).get('content', 'Ошибка получения ответа')
    except Exception as e:
        print(f"Chat API error: {e}")
        return f"❌ Ошибка связи с AI: {str(e)}"

def get_api_key_by_id(api_key_id: int, conn) -> str:
    cursor = conn.cursor()
    cursor.execute("SELECT key FROM api_keys WHERE id = %s", (api_key_id,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def get_bot_by_token(telegram_token: str, conn) -> tuple:
    cursor = conn.cursor()
    
    token_safe = telegram_token.replace("'", "''")
    
    cursor.execute(f"""
        SELECT tb.id, tb.api_key_id
        FROM telegram_bots tb
        WHERE tb.telegram_token = '{token_safe}' AND tb.is_active = true
    """)
    result = cursor.fetchone()
    cursor.close()
    
    if result:
        return (result[0], result[1])
    return (None, None)

def send_telegram_message(chat_id: int, text: str, bot_token: str):
    import urllib.request
    import urllib.parse
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    data = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }).encode()
    
    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error sending message: {e}")

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Telegram webhook для MadAI с вашим AI через API ключи
    Args: event - webhook от Telegram, context - функция контекст
    Returns: HTTP response
    '''
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Api-Key, X-Telegram-Bot-Token',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    query_params = event.get('queryStringParameters', {}) or {}
    telegram_token = query_params.get('token')
    
    if not telegram_token:
        return {
            'statusCode': 401,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Missing bot token in query params'})
        }
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Database not configured'})
        }
    
    conn = psycopg2.connect(database_url)
    
    bot_id, api_key_id = get_bot_by_token(telegram_token, conn)
    
    if not bot_id:
        conn.close()
        return {
            'statusCode': 403,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Bot not found or inactive'})
        }
    
    api_key = get_api_key_by_id(api_key_id, conn) if api_key_id else None
    
    if not api_key:
        conn.close()
        return {
            'statusCode': 403,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'API key not configured for this bot'})
        }
    
    try:
        body_data = json.loads(event.get('body', '{}'))
        print(f"Received webhook body: {json.dumps(body_data)[:200]}")
        
        if 'message' in body_data:
            message = body_data['message']
            chat_id = message['chat']['id']
            user_text = message.get('text', '')
            
            print(f"User message: '{user_text}' from chat_id: {chat_id}")
            
            if user_text.startswith('/start'):
                response_text = """🚀 MadAI Telegram Bot активирован!

Я — AI-эксперт по Lua программированию и могу помочь с:

✅ Синтаксисом и функциями Lua
✅ Таблицами и метатаблицами
✅ ООП в Lua
✅ Примерами кода
✅ Отладкой и оптимизацией

Просто напишите ваш вопрос!"""
            else:
                print(f"Sending to chat API: '{user_text}'")
                response_text = get_ai_response_from_chat(user_text, chat_id, api_key)
                print(f"AI response (first 100 chars): {response_text[:100]}")
            
            send_telegram_message(chat_id, response_text, telegram_token)
        
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': True})
        }
        
    except Exception as e:
        if conn:
            conn.close()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }