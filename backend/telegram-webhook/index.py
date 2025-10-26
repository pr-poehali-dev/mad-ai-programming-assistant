import json
import os
import psycopg2
from typing import Dict, Any

def get_openai_response(query: str, chat_history: list, conn) -> str:
    import urllib.request
    import urllib.parse
    
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if not openai_api_key:
        return "⚠️ OpenAI API key не настроен. Обратитесь к администратору."
    
    messages = [
        {"role": "system", "content": "Ты — MadAI, эксперт по программированию на Lua. Отвечай на русском языке. Давай четкие, понятные ответы с примерами кода когда это уместно. Используй Markdown для форматирования."}
    ]
    
    messages.extend(chat_history[-10:])
    
    messages.append({"role": "user", "content": query})
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}'
    }
    
    data = json.dumps({
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }).encode()
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return f"❌ Ошибка при обращении к AI: {str(e)}"

def get_chat_history(chat_id: int, conn) -> list:
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT role, content
        FROM chat_messages
        WHERE chat_id = {chat_id}
        ORDER BY created_at DESC
        LIMIT 20
    """)
    
    results = cursor.fetchall()
    cursor.close()
    
    history = []
    for role, content in reversed(results):
        history.append({"role": role, "content": content})
    
    return history

def get_bot_by_token(telegram_token: str, conn) -> bool:
    cursor = conn.cursor()
    
    token_safe = telegram_token.replace("'", "''")
    
    cursor.execute(f"""
        SELECT tb.id 
        FROM telegram_bots tb
        WHERE tb.telegram_token = '{token_safe}' AND tb.is_active = true
    """)
    result = cursor.fetchone()
    cursor.close()
    return result is not None

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
    Business: Telegram webhook для MadAI бота с AI интеграцией
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
    
    if not get_bot_by_token(telegram_token, conn):
        conn.close()
        return {
            'statusCode': 403,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Bot not found or inactive'})
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
                print(f"Processing user query with OpenAI: '{user_text}'")
                
                user_text_safe = user_text.replace("'", "''")
                
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO chat_messages (chat_id, role, content)
                    VALUES ({chat_id}, 'user', '{user_text_safe}')
                """)
                conn.commit()
                cursor.close()
                
                chat_history = get_chat_history(chat_id, conn)
                
                ai_response = get_openai_response(user_text, chat_history, conn)
                print(f"AI response (first 100 chars): {ai_response[:100]}")
                
                ai_response_safe = ai_response.replace("'", "''")
                
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO chat_messages (chat_id, role, content)
                    VALUES ({chat_id}, 'assistant', '{ai_response_safe}')
                """)
                conn.commit()
                cursor.close()
                
                response_text = ai_response
            
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
