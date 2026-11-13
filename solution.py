# -*- coding: utf-8 -*-
# Решение ДЗ_3 (Cassandra). Заполняйте места с TODO -
# остальное (стенд, контрольные данные, проверки) уже готово в lab.py.
# Служебный lab.py менять не нужно

import json
from datetime import datetime, timedelta

from cassandra.query import ConsistencyLevel

# База отсчёта времени событий: 2026-01-01T00:00:00Z. Важно: без таймзоны (UTC)
# драйвер возвращает timestamp без tzinfo, и сценарий data
# сравнивает прочитанные значения именно с наивной базой.
BASE_EVENT_TIME = datetime(2026, 1, 1)

# Типы событий: циклично по индексу i - login, purchase, view.
EVENT_TYPES = ['login', 'purchase', 'view']


def create_tables(session):
    # Две таблицы журнала действий пользователя.
    #
    # user_actions:
    #   - partition key user_id - все события пользователя лежат в одной
    #     партиции, лента читается одним запросом по ключу партиции;
    #   - clustering key event_time DESC - строки внутри партиции хранятся
    #     по убыванию времени, поэтому "последние N событий" - это просто
    #     чтение первых N строк партиции (LIMIT), без сортировки на клиенте;
    #   - сжатие LZ4 - журнал хорошо сжимается, экономия места и I/O.
    #
    # user_actions_none: та же структура без сжатия - контрольная таблица
    # для сравнения размеров SSTable в разделе 5. В Cassandra 5.0 сжатие
    # отключается опцией {'enabled': 'false'} (класс NoCompressor из старых
    # версий в 5.0.4 недоступен); в system_schema это видно как
    # compression = {'enabled': 'false'}.
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS user_actions (
            user_id     int,
            event_time  timestamp,
            event_type  text,
            payload     text,
            PRIMARY KEY (user_id, event_time)
        )
        WITH CLUSTERING ORDER BY (event_time DESC)
          AND compression = {'class': 'LZ4Compressor'};
        """
    )
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS user_actions_none (
            user_id     int,
            event_time  timestamp,
            event_type  text,
            payload     text,
            PRIMARY KEY (user_id, event_time)
        )
        WITH CLUSTERING ORDER BY (event_time DESC)
          AND compression = {'enabled': 'false'};
        """
    )
    return ['user_actions', 'user_actions_none']


def insert_events(session, table, user_id, n, consistency):
    # Вставка n событий через PreparedStatement: запрос компилируется
    # (парсится и планируется) на сервере один раз, дальше драйвер шлёт
    # только значения с токеном подготовленного statements. Имя таблицы
    # не может быть плейсхолдером, поэтому подставляется в текст запроса;
    # уровень консистентности задаётся на каждом bound statement.
    query = (
        'INSERT INTO %s (user_id, event_time, event_type, payload) '
        'VALUES (?, ?, ?, ?)' % table
    )
    prepared = session.prepare(query)
    for i in range(n):
        event_time = BASE_EVENT_TIME + timedelta(minutes=i)
        event_type = EVENT_TYPES[i % 3]
        payload = json.dumps({'seq': i})
        bound = prepared.bind((user_id, event_time, event_type, payload))
        bound.consistency_level = consistency
        session.execute(bound)
    return n


def read_last(session, table, user_id, limit, consistency):
    # Лента последних событий: кластеризация партиции по event_time DESC
    # уже хранит строки в нужном порядке, поэтому достаточно выбрать
    # первые limit строк партиции - сортировки на клиенте не требуется.
    query = (
        'SELECT event_time, event_type, payload FROM %s '
        'WHERE user_id = ? LIMIT ?' % table
    )
    prepared = session.prepare(query)
    bound = prepared.bind((user_id, limit))
    bound.consistency_level = consistency
    return list(session.execute(bound))


def configure_twcs_ttl(session, table):
    # Журнал событий - поток данных с монотонным временем, поэтому:
    #   - TWCS с окном в один день складывает SSTable в суточные окна и
    #     компактирует каждое окно в один файл; окно целиком "умирает"
    #     по TTL без переписывания данных между окнами;
    #   - default_time_to_live = 2592000 (30 дней) - срок жизни строк
    #     журнала; по истечении Cassandra сама превращает строку в tombstone.
    session.execute(
        """
        ALTER TABLE %s
        WITH compaction = {
            'class': 'TimeWindowCompactionStrategy',
            'compaction_window_unit': 'DAYS',
            'compaction_window_size': '1'
        }
        AND default_time_to_live = 2592000;
        """ % table
    )
