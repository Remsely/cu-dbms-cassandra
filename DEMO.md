# Демонстрация

Скриншоты сделаны при предыдущем прогоне; времена могут отличаться от результатов последнего запуска. Реализация — в [solution.py](solution.py), свежие результаты — в [results](results/README.md).

## 2. Таблицы и модель данных

```
docker compose run --rm lab data
```

![data](screenshots/02-data.png)

## 3. Вставка и чтение

```
docker compose run --rm lab bulk
```

![bulk](screenshots/03-bulk.png)

## 4. Консистентность

```
docker compose run --rm lab consistency
```

![consistency](screenshots/04-consistency.png)

## 5. Сжатие

```
bash ops.sh tablestats
```

![сжатие](screenshots/05-compression.png)

Значения размеров и сжатия: [user_actions](results/tablestats.txt) и [user_actions_none](results/tablestats_plain.txt).

## 6. Bloom-фильтр

![bloom](screenshots/06-bloom.png)

## 7. Repair

```
bash ops.sh repair
```

![repair](screenshots/07-repair.png)

[Полный вывод repair](results/repair.txt).

## 8. TTL и компакция

```
docker compose run --rm lab compaction
```

![compaction](screenshots/08-ttl.png)

```
docker compose run --rm lab shell
```

```
TRACING ON;
SELECT event_time, event_type FROM hw3.user_actions WHERE user_id = 3001;
```

![tracing](screenshots/08-tracing.png)

```
bash ops.sh compact
```

![compact](screenshots/08-compact.png)

[История компакции](results/compaction.txt).

## 9. Результаты

```
docker compose run --rm lab metrics
```

![metrics](screenshots/09-metrics.png)
