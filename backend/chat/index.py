import json
import os
import psycopg2
import urllib.parse
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

def calculate_math(expression: str) -> Optional[str]:
    '''Вычисляет простые математические выражения'''
    try:
        expression = expression.lower()
        expression = expression.replace('плюс', '+').replace('минус', '-')
        expression = expression.replace('умножить', '*').replace('разделить', '/')
        expression = expression.replace('на', '*').replace('х', '*')
        
        match = re.search(r'([\d\.\s]+)\s*([\+\-\*\/])\s*([\d\.\s]+)', expression)
        if match:
            left = float(match.group(1).strip())
            operator = match.group(2)
            right = float(match.group(3).strip())
            
            if operator == '+':
                result = left + right
            elif operator == '-':
                result = left - right
            elif operator == '*':
                result = left * right
            elif operator == '/':
                if right == 0:
                    return "**Ошибка:** Деление на ноль невозможно"
                result = left / right
            else:
                return None
            
            return f"**Результат:** {left} {operator} {right} = **{result}**"
    except:
        pass
    return None

def search_game(query: str, conn) -> Optional[str]:
    '''Ищет информацию об игре в базе данных'''
    cursor = conn.cursor()
    query_lower = query.lower()
    keywords = query_lower.split()
    
    cursor.execute("""
        SELECT name, developer, publisher, release_year, genre, platform, description
        FROM games_database
        WHERE keywords && %s::text[]
           OR LOWER(name) LIKE %s
        ORDER BY 
            CASE 
                WHEN LOWER(name) = %s THEN 1
                WHEN LOWER(name) LIKE %s THEN 2
                ELSE 3
            END
        LIMIT 1
    """, (keywords, f'%{query_lower}%', query_lower, f'%{query_lower}%'))
    
    result = cursor.fetchone()
    cursor.close()
    
    if result:
        name, developer, publisher, year, genre, platform, description = result
        response = f"🎮 **{name}**\n\n"
        if developer:
            response += f"**Разработчик:** {developer}\n"
        if publisher:
            response += f"**Издатель:** {publisher}\n"
        if year:
            response += f"**Год выхода:** {year}\n"
        if genre:
            response += f"**Жанр:** {genre}\n"
        if platform:
            response += f"**Платформы:** {platform}\n"
        if description:
            response += f"\n{description}"
        return response
    
    return None

def search_celebrity(query: str, conn) -> Optional[str]:
    '''Ищет информацию об артисте/знаменитости'''
    cursor = conn.cursor()
    query_lower = query.lower()
    keywords = query_lower.split()
    
    cursor.execute("""
        SELECT name, profession, birth_year, nationality, known_for, description
        FROM celebrities_database
        WHERE keywords && %s::text[]
           OR LOWER(name) LIKE %s
        ORDER BY 
            CASE 
                WHEN LOWER(name) = %s THEN 1
                WHEN LOWER(name) LIKE %s THEN 2
                ELSE 3
            END
        LIMIT 1
    """, (keywords, f'%{query_lower}%', query_lower, f'%{query_lower}%'))
    
    result = cursor.fetchone()
    cursor.close()
    
    if result:
        name, profession, birth_year, nationality, known_for, description = result
        response = f"🎤 **{name}**\n\n"
        if profession:
            response += f"**Профессия:** {profession}\n"
        if birth_year:
            response += f"**Год рождения:** {birth_year}\n"
        if nationality:
            response += f"**Страна:** {nationality}\n"
        if known_for:
            response += f"**Известен:** {known_for}\n"
        if description:
            response += f"\n{description}"
        return response
    
    return None

def get_creator_info(conn) -> str:
    '''Возвращает информацию о создателе'''
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM creator_info WHERE key = 'creator_full'")
    result = cursor.fetchone()
    cursor.close()
    
    if result:
        return result[0]
    return "MadAI создал Мад Сатору в 2025 году"

def search_web(query: str) -> str:
    '''Возвращает прямые ссылки на поиск'''
    encoded_query = urllib.parse.quote(query)
    yandex_url = f"https://yandex.ru/search/?text={encoded_query}"
    google_url = f"https://www.google.com/search?q={encoded_query}"
    
    return f"""🔍 **Поиск:** {query}

**Яндекс:** {yandex_url}

**Google:** {google_url}

Нажмите на ссылку для поиска в интернете!"""

def get_lua_knowledge(query: str, conn) -> Optional[str]:
    '''Ищет знания о Lua/Roblox'''
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
    '''Генерирует умный ответ на основе запроса'''
    message_lower = message.lower()
    
    math_result = calculate_math(message)
    if math_result:
        return math_result
    
    if 'создал' in message_lower and 'madai' in message_lower or 'кто создал' in message_lower or 'автор' in message_lower:
        return get_creator_info(conn)
    
    game_info = search_game(message, conn)
    if game_info:
        return game_info
    
    celebrity_info = search_celebrity(message, conn)
    if celebrity_info:
        return celebrity_info
    
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
    '''Получает историю сообщений'''
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

def cleanup_old_messages(conn, days_to_keep: int = 1) -> int:
    '''Удаляет старые сообщения'''
    cursor = conn.cursor()
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    cursor.execute("""
        DELETE FROM chat_messages
        WHERE created_at < %s
    """, (cutoff_date,))
    
    deleted_count = cursor.rowcount
    conn.commit()
    cursor.close()
    
    return deleted_count

def save_message(role: str, content: str, conn) -> Dict:
    '''Сохраняет сообщение в БД'''
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
    Business: Умный AI-чат с математикой, играми, артистами и веб-поиском
    Args: event - HTTP запрос, context - контекст функции
    Returns: HTTP response с умным ответом
    '''
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Api-Key',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'isBase64Encoded': False,
            'body': json.dumps({'error': 'Database not configured'})
        }
    
    conn = psycopg2.connect(database_url)
    
    headers = event.get('headers', {})
    api_key = headers.get('X-Api-Key') or headers.get('x-api-key')
    
    if api_key:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM api_keys 
            WHERE key = %s AND key IS NOT NULL
        """, (api_key,))
        result = cursor.fetchone()
        
        if result:
            cursor.execute("""
                UPDATE api_keys 
                SET last_used = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (result[0],))
            conn.commit()
        cursor.close()
    
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
            
            if body_data.get('cleanup'):
                days_to_keep = body_data.get('days', 1)
                deleted_count = cleanup_old_messages(conn, days_to_keep)
                conn.close()
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'isBase64Encoded': False,
                    'body': json.dumps({
                        'success': True,
                        'deleted_messages': deleted_count,
                        'message': f'Удалено {deleted_count} сообщений старше {days_to_keep} дн.'
                    })
                }
            
            user_message = body_data.get('message', '').strip()
            
            if not user_message:
                conn.close()
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'isBase64Encoded': False,
                    'body': json.dumps({'error': 'Сообщение не может быть пустым'})
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
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'isBase64Encoded': False,
                'body': json.dumps({'error': 'Method not allowed'})
            }
    
    except Exception as e:
        if conn:
            conn.close()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'isBase64Encoded': False,
            'body': json.dumps({'error': str(e)})
        }