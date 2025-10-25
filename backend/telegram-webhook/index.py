import json
import os
import psycopg2
from typing import Dict, Any

def get_lua_knowledge(query: str, conn) -> str:
    cursor = conn.cursor()
    
    query_lower = query.lower()
    keywords = query_lower.split()
    
    cursor.execute("""
        SELECT topic, description, code_example, explanation
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
    
    if not results:
        return generate_generic_lua_response(query)
    
    response_parts = []
    for topic, description, code_example, explanation in results:
        response = f"**{topic}**\n\n"
        if description:
            response += f"{description}\n\n"
        if code_example:
            response += f"```lua\n{code_example}\n```\n\n"
        if explanation:
            response += f"{explanation}\n"
        response_parts.append(response.strip())
    
    return "\n\n---\n\n".join(response_parts)

def generate_generic_lua_response(query: str) -> str:
    query_lower = query.lower()
    
    if 'function' in query_lower or 'функция' in query_lower:
        return """**Функции в Lua**

Функции объявляются с помощью ключевого слова `function`:

```lua
function greet(name)
    return "Hello, " .. name
end

print(greet("World"))
```

Можно также использовать анонимные функции:

```lua
local add = function(a, b)
    return a + b
end
```"""
    
    if 'table' in query_lower or 'таблица' in query_lower:
        return """**Таблицы в Lua**

Таблицы — универсальная структура данных:

```lua
local person = {
    name = "John",
    age = 30,
    skills = {"Lua", "Python"}
}

print(person.name)
print(person.skills[1])
```"""
    
    if 'loop' in query_lower or 'цикл' in query_lower or 'for' in query_lower:
        return """**Циклы в Lua**

```lua
-- Числовой for
for i = 1, 10 do
    print(i)
end

-- Generic for (итерация)
local arr = {10, 20, 30}
for index, value in ipairs(arr) do
    print(index, value)
end

-- While цикл
local count = 0
while count < 5 do
    count = count + 1
    print(count)
end
```"""
    
    return """Я — MadAI, эксперт по Lua! 

Спросите меня о:
• Функциях и переменных
• Таблицах и массивах
• Циклах и условиях
• ООП в Lua
• Метатаблицах
• Корутинах

Пример: "Как работают функции в Lua?" """

def verify_api_key(api_key: str, telegram_token: str, conn) -> bool:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tb.id 
        FROM telegram_bots tb
        JOIN api_keys ak ON tb.api_key_id = ak.id
        WHERE ak.key = %s AND tb.telegram_token = %s AND tb.is_active = true
    """, (api_key, telegram_token))
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
    Business: Telegram webhook для MadAI бота с Lua экспертизой
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
    
    headers = event.get('headers', {})
    api_key = headers.get('x-api-key') or headers.get('X-Api-Key')
    telegram_token = headers.get('x-telegram-bot-token') or headers.get('X-Telegram-Bot-Token')
    
    if not api_key or not telegram_token:
        return {
            'statusCode': 401,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Missing API key or Telegram token'})
        }
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Database not configured'})
        }
    
    conn = psycopg2.connect(database_url)
    
    if not verify_api_key(api_key, telegram_token, conn):
        conn.close()
        return {
            'statusCode': 403,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid API key or bot not configured'})
        }
    
    try:
        body_data = json.loads(event.get('body', '{}'))
        
        if 'message' in body_data:
            message = body_data['message']
            chat_id = message['chat']['id']
            user_text = message.get('text', '')
            
            if user_text.startswith('/start'):
                response_text = """🚀 MadAI Telegram Bot активирован!

Я — эксперт по Lua программированию и могу помочь с:

✅ Синтаксисом и функциями Lua
✅ Таблицами и метатаблицами
✅ ООП в Lua
✅ Примерами кода
✅ Отладкой и оптимизацией

Просто напишите ваш вопрос!"""
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO chat_messages (role, content)
                    VALUES ('user', %s)
                """, (user_text,))
                conn.commit()
                cursor.close()
                
                ai_response = get_lua_knowledge(user_text, conn)
                
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO chat_messages (role, content)
                    VALUES ('assistant', %s)
                """, (ai_response,))
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