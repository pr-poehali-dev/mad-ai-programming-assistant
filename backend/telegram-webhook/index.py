import json
import os
import psycopg2
from typing import Dict, Any

def get_lua_knowledge(query: str, conn) -> str:
    cursor = conn.cursor()
    
    query_lower = query.lower()
    query_safe = query_lower.replace("'", "''")
    
    print(f"Searching lua_knowledge_base for: '{query_safe}'")
    
    cursor.execute(f"""
        SELECT topic, description, code_example, explanation
        FROM lua_knowledge_base
        WHERE 
            LOWER(topic) LIKE '%{query_safe}%'
            OR LOWER(description) LIKE '%{query_safe}%'
        ORDER BY 
            CASE 
                WHEN LOWER(topic) = '{query_safe}' THEN 1
                WHEN LOWER(topic) LIKE '%{query_safe}%' THEN 2
                ELSE 3
            END
        LIMIT 3
    """)
    
    results = cursor.fetchall()
    cursor.close()
    
    print(f"Found {len(results)} results from knowledge base")
    
    if not results:
        print("No results found, using generic response")
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

Я — эксперт по Lua программированию и могу помочь с:

✅ Синтаксисом и функциями Lua
✅ Таблицами и метатаблицами
✅ ООП в Lua
✅ Примерами кода
✅ Отладкой и оптимизацией

Просто напишите ваш вопрос!"""
            else:
                print(f"Processing user query: '{user_text}'")
                
                user_text_safe = user_text.replace("'", "''")
                
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO chat_messages (role, content)
                    VALUES ('user', '{user_text_safe}')
                """)
                conn.commit()
                cursor.close()
                
                print("Getting AI response from lua_knowledge...")
                ai_response = get_lua_knowledge(user_text, conn)
                print(f"AI response (first 100 chars): {ai_response[:100]}")
                
                ai_response_safe = ai_response.replace("'", "''")
                
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO chat_messages (role, content)
                    VALUES ('assistant', '{ai_response_safe}')
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