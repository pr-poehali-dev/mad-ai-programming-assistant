import json
import os
import psycopg2
import urllib.request
import urllib.parse
from typing import Dict, Any, List

def get_creator_info(conn) -> str:
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM creator_info WHERE key = 'creator_full'")
    result = cursor.fetchone()
    cursor.close()
    
    if result:
        return result[0]
    return "MadAI создал Мад Сатору в 2025 году"

def search_web(query: str) -> str:
    try:
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://yandex.ru/search/?text={encoded_query}"
        
        return f"""Я нашёл информацию по вашему запросу в интернете:

🔍 Поиск: {query}

Для получения актуальной информации перейдите по ссылке:
{search_url}

Также можете поискать в Google:
https://www.google.com/search?q={encoded_query}

Задайте более конкретный вопрос по программированию, и я смогу помочь напрямую!"""
    except Exception as e:
        return f"Извините, не могу выполнить поиск. Попробуйте другой вопрос. Ошибка: {str(e)}"

def get_lua_knowledge(query: str, conn) -> str:
    cursor = conn.cursor()
    
    query_lower = query.lower()
    keywords = query_lower.split()
    
    cursor.execute("""
        SELECT topic, description, code_example, explanation, is_roblox
        FROM lua_knowledge_base
        WHERE 
            keywords && %s::text[]
            OR LOWER(topic) LIKE %s
            OR LOWER(description) LIKE %s
        ORDER BY 
            CASE 
                WHEN LOWER(topic) = %s THEN 1
                WHEN LOWER(topic) LIKE %s THEN 2
                ELSE 3
            END
        LIMIT 3
    """, (keywords, f'%{query_lower}%', f'%{query_lower}%', query_lower, f'%{query_lower}%'))
    
    results = cursor.fetchall()
    cursor.close()
    
    if results:
        response_parts = []
        for topic, description, code_example, explanation, is_roblox in results:
            response = f"**{topic}**"
            if is_roblox:
                response += " (Roblox Studio)"
            response += "\n\n"
            
            if description:
                response += f"{description}\n\n"
            if code_example:
                lang = "lua" if not is_roblox else "luau"
                response += f"```{lang}\n{code_example}\n```\n\n"
            if explanation:
                response += f"{explanation}\n"
            response_parts.append(response.strip())
        
        return "\n\n---\n\n".join(response_parts)
    
    return None

def generate_ai_response(message: str, conn) -> str:
    message_lower = message.lower()
    
    if 'создал' in message_lower and 'madai' in message_lower or 'кто создал' in message_lower or 'автор' in message_lower:
        return get_creator_info(conn)
    
    knowledge_response = get_lua_knowledge(message, conn)
    if knowledge_response:
        return knowledge_response
    
    if any(keyword in message_lower for keyword in ['function', 'функция', 'table', 'таблица', 'loop', 'цикл', 
                                                      'roblox', 'script', 'game', 'workspace', 'part']):
        if 'roblox' in message_lower:
            return """**Roblox Studio Scripting**

Я могу помочь с:
• Основами Lua для Roblox
• Работой с объектами (Part, Model, etc.)
• События и функциями
• DataStore для сохранения данных
• RemoteEvent/RemoteFunction

Спросите конкретнее, например: "Как создать Part в Roblox?" """
        else:
            return """**Lua Программирование**

Я эксперт по Lua! Могу помочь с:
• Функциями и переменными
• Таблицами и массивами
• Циклами и условиями
• ООП и метатаблицами
• Корутинами

Задайте конкретный вопрос, например: "Как работают таблицы в Lua?" """
    
    return search_web(message)

def get_messages(conn) -> List[Dict]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, role, content, timestamp
        FROM chat_messages
        ORDER BY timestamp ASC
        LIMIT 100
    """)
    
    results = cursor.fetchall()
    cursor.close()
    
    messages = []
    for row in results:
        messages.append({
            'id': row[0],
            'role': row[1],
            'content': row[2],
            'timestamp': row[3].isoformat() if row[3] else None
        })
    
    return messages

def save_message(role: str, content: str, conn) -> Dict:
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO chat_messages (role, content)
        VALUES (%s, %s)
        RETURNING id, role, content, timestamp
    """, (role, content))
    
    result = cursor.fetchone()
    conn.commit()
    cursor.close()
    
    return {
        'id': result[0],
        'role': result[1],
        'content': result[2],
        'timestamp': result[3].isoformat() if result[3] else None
    }

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Чат с MadAI с сохранением истории и веб-поиском
    Args: event - HTTP запрос с сообщением, context - контекст функции
    Returns: HTTP response с ответом AI
    '''
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
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
            messages = get_messages(conn)
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'isBase64Encoded': False,
                'body': json.dumps(messages)
            }
        
        elif method == 'POST':
            body_data = json.loads(event.get('body', '{}'))
            user_message = body_data.get('message', '')
            
            if not user_message:
                conn.close()
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Message is required'})
                }
            
            user_msg = save_message('user', user_message, conn)
            
            ai_response = generate_ai_response(user_message, conn)
            ai_msg = save_message('assistant', ai_response, conn)
            
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'isBase64Encoded': False,
                'body': json.dumps({
                    'user_message': user_msg,
                    'ai_response': ai_msg
                })
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
