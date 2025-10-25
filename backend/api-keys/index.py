import json
import os
import psycopg2
import secrets
from typing import Dict, Any, List

def generate_api_key() -> str:
    return f"madai_{secrets.token_urlsafe(32)}"

def get_api_keys(conn) -> List[Dict]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, key, name, created_at, last_used
        FROM api_keys
        ORDER BY created_at DESC
    """)
    
    results = cursor.fetchall()
    cursor.close()
    
    keys = []
    for row in results:
        keys.append({
            'id': row[0],
            'key': row[1],
            'name': row[2],
            'created': row[3].isoformat() if row[3] else None,
            'lastUsed': row[4].isoformat() if row[4] else None
        })
    
    return keys

def create_api_key(name: str, conn) -> Dict:
    cursor = conn.cursor()
    
    new_key = generate_api_key()
    
    cursor.execute("""
        INSERT INTO api_keys (key, name)
        VALUES (%s, %s)
        RETURNING id, key, name, created_at
    """, (new_key, name))
    
    result = cursor.fetchone()
    conn.commit()
    cursor.close()
    
    return {
        'id': result[0],
        'key': result[1],
        'name': result[2],
        'created': result[3].isoformat() if result[3] else None
    }

def delete_api_key(key_id: int, conn) -> Dict:
    cursor = conn.cursor()
    
    cursor.execute("UPDATE api_keys SET key = NULL WHERE id = %s", (key_id,))
    
    conn.commit()
    cursor.close()
    
    return {'success': True}

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Управление API ключами с сохранением в БД
    Args: event - HTTP запрос, context - контекст функции
    Returns: HTTP response с API ключами
    '''
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
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
            keys = get_api_keys(conn)
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'isBase64Encoded': False,
                'body': json.dumps(keys)
            }
        
        elif method == 'POST':
            body_data = json.loads(event.get('body', '{}'))
            name = body_data.get('name', 'Unnamed Key')
            
            result = create_api_key(name, conn)
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
        
        elif method == 'DELETE':
            query_params = event.get('queryStringParameters') or {}
            key_id = query_params.get('id')
            
            if not key_id:
                conn.close()
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Missing key id'})
                }
            
            result = delete_api_key(int(key_id), conn)
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
            
    except Exception as e:
        if conn:
            conn.close()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
