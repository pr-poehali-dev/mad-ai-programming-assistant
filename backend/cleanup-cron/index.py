import json
import os
import psycopg2
from typing import Dict, Any
from datetime import datetime, timedelta

def cleanup_old_messages(conn, days_to_keep: int = 1) -> int:
    '''Удаляет сообщения старше указанного количества дней'''
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

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Автоматическая очистка старых сообщений по расписанию
    Args: event - триггер от cron, context - контекст функции
    Returns: HTTP response с результатом очистки
    '''
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'isBase64Encoded': False,
            'body': json.dumps({'error': 'Database not configured'})
        }
    
    conn = psycopg2.connect(database_url)
    
    try:
        # Удаляем сообщения старше 1 дня
        deleted_count = cleanup_old_messages(conn, days_to_keep=1)
        conn.close()
        
        result = {
            'success': True,
            'deleted_messages': deleted_count,
            'timestamp': datetime.now().isoformat(),
            'message': f'Автоочистка: удалено {deleted_count} сообщений'
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'isBase64Encoded': False,
            'body': json.dumps(result)
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
