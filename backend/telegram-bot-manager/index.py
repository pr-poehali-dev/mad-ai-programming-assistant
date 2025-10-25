import json
import os
import psycopg2
from typing import Dict, Any, List

def get_telegram_bots(api_key: str, conn) -> List[Dict]:
    cursor = conn.cursor()
    
    api_key_safe = api_key.replace("'", "''")
    
    cursor.execute(f"""
        SELECT tb.id, tb.telegram_token, tb.bot_username, tb.is_active, 
               tb.webhook_url, tb.created_at, tb.last_activity
        FROM telegram_bots tb
        JOIN api_keys ak ON tb.api_key_id = ak.id
        WHERE ak.key = '{api_key_safe}'
        ORDER BY tb.created_at DESC
    """)
    
    results = cursor.fetchall()
    cursor.close()
    
    bots = []
    for row in results:
        bots.append({
            'id': row[0],
            'telegram_token': row[1][:10] + '...' + row[1][-5:] if row[1] else None,
            'bot_username': row[2],
            'is_active': row[3],
            'webhook_url': row[4],
            'created_at': row[5].isoformat() if row[5] else None,
            'last_activity': row[6].isoformat() if row[6] else None
        })
    
    return bots

def add_telegram_bot(api_key: str, telegram_token: str, webhook_url: str, conn) -> Dict:
    cursor = conn.cursor()
    
    api_key_safe = api_key.replace("'", "''")
    
    cursor.execute(f"SELECT id FROM api_keys WHERE key = '{api_key_safe}'")
    api_key_result = cursor.fetchone()
    
    if not api_key_result:
        cursor.close()
        raise ValueError("Invalid API key")
    
    api_key_id = api_key_result[0]
    
    import urllib.request
    import urllib.error
    
    try:
        api_url = f"https://api.telegram.org/bot{telegram_token}/getMe"
        req = urllib.request.Request(api_url)
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        
        if not data.get('ok'):
            raise ValueError("Invalid Telegram token")
        
        bot_username = data['result'].get('username')
        
    except urllib.error.URLError:
        raise ValueError("Cannot verify Telegram token")
    
    telegram_token_safe = telegram_token.replace("'", "''")
    bot_username_safe = (bot_username or '').replace("'", "''")
    webhook_url_safe = webhook_url.replace("'", "''")
    
    cursor.execute(f"""
        INSERT INTO telegram_bots (api_key_id, telegram_token, bot_username, webhook_url)
        VALUES ({api_key_id}, '{telegram_token_safe}', '{bot_username_safe}', '{webhook_url_safe}')
        RETURNING id
    """)
    
    new_id = cursor.fetchone()[0]
    conn.commit()
    
    try:
        import urllib.parse
        webhook_url_full = f"{webhook_url}?token={urllib.parse.quote(telegram_token)}"
        set_webhook_url = f"https://api.telegram.org/bot{telegram_token}/setWebhook"
        
        webhook_data = json.dumps({'url': webhook_url_full}).encode()
        
        req = urllib.request.Request(
            set_webhook_url,
            data=webhook_data,
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        print(f"Webhook set result: {result}")
        
    except Exception as e:
        print(f"Warning: Could not set webhook: {e}")
    
    cursor.close()
    
    return {
        'id': new_id,
        'bot_username': bot_username,
        'success': True
    }

def toggle_bot_status(bot_id: int, api_key: str, conn) -> Dict:
    cursor = conn.cursor()
    
    api_key_safe = api_key.replace("'", "''")
    
    cursor.execute(f"""
        UPDATE telegram_bots tb
        SET is_active = NOT is_active
        FROM api_keys ak
        WHERE tb.id = {bot_id} AND tb.api_key_id = ak.id AND ak.key = '{api_key_safe}'
        RETURNING is_active
    """)
    
    result = cursor.fetchone()
    
    if not result:
        cursor.close()
        raise ValueError("Bot not found or access denied")
    
    conn.commit()
    cursor.close()
    
    return {'is_active': result[0]}

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Управление Telegram ботами и связка с API ключами
    Args: event - HTTP запрос с данными бота, context - контекст функции
    Returns: HTTP response с данными ботов
    '''
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Api-Key',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    headers = event.get('headers', {})
    api_key = headers.get('x-api-key') or headers.get('X-Api-Key')
    
    if not api_key:
        return {
            'statusCode': 401,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Missing API key'})
        }
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Database not configured'})
        }
    
    conn = psycopg2.connect(database_url)
    
    try:
        if method == 'GET':
            bots = get_telegram_bots(api_key, conn)
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'isBase64Encoded': False,
                'body': json.dumps(bots)
            }
        
        elif method == 'POST':
            body_data = json.loads(event.get('body', '{}'))
            telegram_token = body_data.get('telegram_token')
            webhook_url = body_data.get('webhook_url')
            
            if not telegram_token or not webhook_url:
                conn.close()
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Missing telegram_token or webhook_url'})
                }
            
            result = add_telegram_bot(api_key, telegram_token, webhook_url, conn)
            conn.close()
            
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'isBase64Encoded': False,
                'body': json.dumps(result)
            }
        
        elif method == 'PUT':
            body_data = json.loads(event.get('body', '{}'))
            bot_id = body_data.get('bot_id')
            
            if not bot_id:
                conn.close()
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Missing bot_id'})
                }
            
            result = toggle_bot_status(bot_id, api_key, conn)
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'isBase64Encoded': False,
                'body': json.dumps(result)
            }
        
        else:
            conn.close()
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except ValueError as e:
        if conn:
            conn.close()
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        if conn:
            conn.close()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }