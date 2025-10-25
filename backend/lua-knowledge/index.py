import json
import os
import psycopg2
from typing import Dict, Any, List

def get_all_lua_knowledge(conn) -> List[Dict]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, category, topic, description, code_example, explanation, keywords
        FROM lua_knowledge_base
        ORDER BY category, topic
    """)
    
    results = cursor.fetchall()
    cursor.close()
    
    knowledge = []
    for row in results:
        knowledge.append({
            'id': row[0],
            'category': row[1],
            'topic': row[2],
            'description': row[3],
            'code_example': row[4],
            'explanation': row[5],
            'keywords': row[6] or []
        })
    
    return knowledge

def add_lua_knowledge(data: Dict, conn) -> Dict:
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO lua_knowledge_base (category, topic, description, code_example, explanation, keywords)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        data['category'],
        data['topic'],
        data.get('description'),
        data.get('code_example'),
        data.get('explanation'),
        data.get('keywords', [])
    ))
    
    new_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    
    return {'id': new_id, 'success': True}

def seed_initial_knowledge(conn):
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM lua_knowledge_base")
    count = cursor.fetchone()[0]
    
    if count > 0:
        cursor.close()
        return
    
    initial_knowledge = [
        {
            'category': 'Основы',
            'topic': 'Переменные и типы данных',
            'description': 'Lua — динамически типизированный язык с 8 базовыми типами',
            'code_example': '''-- Типы данных в Lua
local num = 42              -- number
local str = "Hello"         -- string
local bool = true           -- boolean
local tbl = {1, 2, 3}      -- table
local func = function() end -- function
local nothing = nil         -- nil

print(type(num))   -- number
print(type(str))   -- string''',
            'explanation': 'В Lua переменные объявляются с помощью local (локальные) или без него (глобальные). Используйте local для избежания конфликтов.',
            'keywords': ['переменные', 'типы', 'local', 'number', 'string', 'boolean', 'table', 'nil']
        },
        {
            'category': 'Основы',
            'topic': 'Функции',
            'description': 'Функции в Lua — объекты первого класса',
            'code_example': '''-- Обычная функция
function greet(name)
    return "Привет, " .. name
end

-- Анонимная функция
local add = function(a, b)
    return a + b
end

-- Функция с множественным возвратом
function getCoords()
    return 10, 20, 30
end

local x, y, z = getCoords()

print(greet("Мир"))  -- Привет, Мир
print(add(5, 3))     -- 8''',
            'explanation': 'Функции могут возвращать несколько значений, храниться в переменных и передаваться как параметры.',
            'keywords': ['function', 'функции', 'return', 'параметры', 'множественный возврат']
        },
        {
            'category': 'Основы',
            'topic': 'Таблицы (массивы и словари)',
            'description': 'Таблицы — единственная структура данных в Lua',
            'code_example': '''-- Массив (индексы с 1!)
local fruits = {"apple", "banana", "orange"}
print(fruits[1])  -- apple

-- Словарь (ассоциативный массив)
local person = {
    name = "John",
    age = 30,
    city = "Moscow"
}
print(person.name)  -- John
print(person["age"])  -- 30

-- Смешанная таблица
local mixed = {
    "first",           -- [1]
    "second",          -- [2]
    key = "value",
    [10] = "tenth"
}''',
            'explanation': 'В Lua индексация массивов начинается с 1, а не с 0! Таблицы могут содержать любые значения и использоваться как массивы, словари или объекты.',
            'keywords': ['table', 'таблицы', 'массив', 'словарь', 'индекс', 'array']
        },
        {
            'category': 'Основы',
            'topic': 'Циклы',
            'description': 'Различные типы циклов в Lua',
            'code_example': '''-- Числовой for (от start до end)
for i = 1, 5 do
    print(i)  -- 1 2 3 4 5
end

-- Числовой for с шагом
for i = 10, 1, -2 do
    print(i)  -- 10 8 6 4 2
end

-- Generic for (итерация по массиву)
local arr = {"a", "b", "c"}
for index, value in ipairs(arr) do
    print(index, value)
end

-- Generic for (итерация по таблице)
local tbl = {x=10, y=20}
for key, value in pairs(tbl) do
    print(key, value)
end

-- While
local count = 0
while count < 3 do
    count = count + 1
    print(count)
end

-- Repeat-until
local n = 0
repeat
    n = n + 1
    print(n)
until n == 3''',
            'explanation': 'ipairs — для массивов (целочисленные ключи), pairs — для всех элементов таблицы.',
            'keywords': ['for', 'while', 'repeat', 'циклы', 'ipairs', 'pairs', 'итерация']
        },
        {
            'category': 'Основы',
            'topic': 'Условия',
            'description': 'Условные конструкции if-then-else',
            'code_example': '''local age = 18

if age >= 18 then
    print("Взрослый")
elseif age >= 13 then
    print("Подросток")
else
    print("Ребенок")
end

-- Тернарный оператор (через and/or)
local status = (age >= 18) and "adult" or "minor"

-- Только false и nil = ложь, всё остальное = истина
if 0 then print("0 = true!") end  -- выполнится!
if "" then print("Пустая строка = true!") end  -- выполнится!''',
            'explanation': 'В Lua только false и nil считаются ложью. 0 и пустая строка — истина!',
            'keywords': ['if', 'then', 'else', 'elseif', 'условия', 'boolean']
        },
        {
            'category': 'Продвинутое',
            'topic': 'Метатаблицы',
            'description': 'Метатаблицы позволяют изменять поведение таблиц',
            'code_example': '''-- Создание класса через метатаблицы
local Vector = {}
Vector.__index = Vector

function Vector.new(x, y)
    local self = setmetatable({}, Vector)
    self.x = x
    self.y = y
    return self
end

function Vector:length()
    return math.sqrt(self.x^2 + self.y^2)
end

-- Перегрузка оператора сложения
Vector.__add = function(a, b)
    return Vector.new(a.x + b.x, a.y + b.y)
end

local v1 = Vector.new(3, 4)
local v2 = Vector.new(1, 2)
local v3 = v1 + v2  -- использует __add

print(v1:length())  -- 5
print(v3.x, v3.y)   -- 4, 6''',
            'explanation': 'Метатаблицы — мощный инструмент для создания классов, перегрузки операторов и контроля доступа к таблицам.',
            'keywords': ['metatable', 'метатаблицы', '__index', '__add', 'ООП', 'классы', 'setmetatable']
        },
        {
            'category': 'Продвинутое',
            'topic': 'Корутины (coroutines)',
            'description': 'Корутины для асинхронного выполнения кода',
            'code_example': '''-- Создание корутины
local co = coroutine.create(function()
    for i = 1, 3 do
        print("Корутина:", i)
        coroutine.yield()  -- приостановка
    end
end)

print(coroutine.status(co))  -- suspended

-- Запуск корутины
coroutine.resume(co)  -- Корутина: 1
coroutine.resume(co)  -- Корутина: 2
coroutine.resume(co)  -- Корутина: 3

-- Передача данных через yield/resume
local producer = coroutine.create(function()
    for i = 1, 3 do
        coroutine.yield(i * 10)
    end
end)

local status, value = coroutine.resume(producer)
print(value)  -- 10''',
            'explanation': 'Корутины позволяют приостанавливать и возобновлять выполнение функций, полезны для асинхронных операций.',
            'keywords': ['coroutine', 'корутины', 'yield', 'resume', 'async', 'асинхронность']
        },
        {
            'category': 'Продвинутое',
            'topic': 'Модули и require',
            'description': 'Организация кода в модули',
            'code_example': '''-- mymodule.lua
local M = {}

function M.hello(name)
    return "Hello, " .. name
end

function M.add(a, b)
    return a + b
end

return M

-- main.lua
local mymodule = require("mymodule")

print(mymodule.hello("World"))  -- Hello, World
print(mymodule.add(5, 3))       -- 8

-- Альтернативный способ
local M = {}

M.VERSION = "1.0"

function M:init()
    self.data = {}
end

return M''',
            'explanation': 'Модули в Lua — это обычные таблицы, которые возвращаются из файла. require загружает и кэширует модуль.',
            'keywords': ['module', 'модули', 'require', 'import', 'export']
        },
        {
            'category': 'Полезное',
            'topic': 'Работа со строками',
            'description': 'Манипуляции со строками в Lua',
            'code_example': '''local str = "Hello World"

-- Длина строки
print(#str)  -- 11
print(string.len(str))  -- 11

-- Подстрока
print(string.sub(str, 1, 5))  -- Hello
print(str:sub(7))  -- World

-- Поиск
local pos = string.find(str, "World")
print(pos)  -- 7

-- Замена
print(string.gsub(str, "World", "Lua"))  -- Hello Lua

-- Регулярные выражения (паттерны)
local text = "Мой email: test@example.com"
local email = string.match(text, "[%w.]+@[%w.]+")
print(email)  -- test@example.com

-- Разделение строки
function split(str, delimiter)
    local result = {}
    for match in (str..delimiter):gmatch("(.-)"..delimiter) do
        table.insert(result, match)
    end
    return result
end

local parts = split("a,b,c", ",")
-- {"a", "b", "c"}''',
            'explanation': 'В Lua встроенная мощная система паттернов (похожа на regex). Строки иммутабельны.',
            'keywords': ['string', 'строки', 'sub', 'find', 'gsub', 'match', 'паттерны', 'regex']
        },
        {
            'category': 'Полезное',
            'topic': 'Работа с таблицами',
            'description': 'Полезные функции для работы с таблицами',
            'code_example': '''local t = {10, 20, 30}

-- Добавление элемента
table.insert(t, 40)  -- {10, 20, 30, 40}
table.insert(t, 1, 5)  -- {5, 10, 20, 30, 40}

-- Удаление элемента
table.remove(t)  -- удаляет последний: {5, 10, 20, 30}
table.remove(t, 1)  -- удаляет первый: {10, 20, 30}

-- Сортировка
table.sort(t)  -- {10, 20, 30}
table.sort(t, function(a, b) return a > b end)  -- {30, 20, 10}

-- Объединение в строку
print(table.concat(t, ", "))  -- 30, 20, 10

-- Копирование таблицы (поверхностное)
function copy(t)
    local result = {}
    for k, v in pairs(t) do
        result[k] = v
    end
    return result
end

-- Подсчет элементов
function count(t)
    local n = 0
    for _ in pairs(t) do
        n = n + 1
    end
    return n
end''',
            'explanation': 'table.insert/remove работают только с массивами. Для словарей используйте прямое присваивание.',
            'keywords': ['table', 'insert', 'remove', 'sort', 'concat', 'таблицы', 'массивы']
        },
        {
            'category': 'Полезное',
            'topic': 'Обработка ошибок',
            'description': 'pcall и xpcall для безопасного выполнения кода',
            'code_example': '''-- Функция, которая может упасть
function riskyFunction(x)
    if x < 0 then
        error("x не может быть отрицательным!")
    end
    return math.sqrt(x)
end

-- pcall (protected call)
local success, result = pcall(riskyFunction, 16)
if success then
    print("Результат:", result)  -- 4
else
    print("Ошибка:", result)
end

local success, err = pcall(riskyFunction, -5)
print(success)  -- false
print(err)  -- x не может быть отрицательным!

-- xpcall с обработчиком ошибок
local function errorHandler(err)
    return "Произошла ошибка: " .. tostring(err)
end

local status, result = xpcall(
    function() return riskyFunction(-10) end,
    errorHandler
)

print(result)  -- Произошла ошибка: x не может быть отрицательным!

-- assert для проверки условий
local function divide(a, b)
    assert(b ~= 0, "Деление на ноль!")
    return a / b
end''',
            'explanation': 'pcall возвращает статус и результат/ошибку. xpcall позволяет задать обработчик ошибок.',
            'keywords': ['pcall', 'xpcall', 'error', 'assert', 'ошибки', 'исключения', 'try-catch']
        }
    ]
    
    for item in initial_knowledge:
        cursor.execute("""
            INSERT INTO lua_knowledge_base (category, topic, description, code_example, explanation, keywords)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            item['category'],
            item['topic'],
            item['description'],
            item['code_example'],
            item['explanation'],
            item['keywords']
        ))
    
    conn.commit()
    cursor.close()

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: API для управления базой знаний Lua
    Args: event - HTTP запрос, context - контекст функции
    Returns: HTTP response с данными базы знаний
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
            query_params = event.get('queryStringParameters') or {}
            
            if query_params.get('seed') == 'true':
                seed_initial_knowledge(conn)
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'success': True, 'message': 'Knowledge base seeded'})
                }
            
            knowledge = get_all_lua_knowledge(conn)
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'isBase64Encoded': False,
                'body': json.dumps(knowledge)
            }
        
        elif method == 'POST':
            body_data = json.loads(event.get('body', '{}'))
            result = add_lua_knowledge(body_data, conn)
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
