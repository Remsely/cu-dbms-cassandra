# Результаты сценариев

Артефакты: `results.json` — статусы и числа сценариев; `tablestats.txt` / `tablestats_plain.txt` — вывод `bash ops.sh tablestats`; `repair.txt` — вывод `bash ops.sh repair`; `compaction.txt` — вывод `bash ops.sh compact`.

Результаты прогона 13 ноября 2026 года. Сценарии пересоздают keyspace, поэтому файлы относятся к разным этапам работы.

## `bulk` — вставка 10 000

| Что вставлено | Сколько | Время |
|---|---:|---:|
| События пользователя 1001 (`login`, `purchase`, `view`) | 10 000 | 14,009 с, в среднем 1,401 мс на запись |

Время — из `artifacts.bulk.seconds` в `results.json`; среднее за запись получено делением на 10 000.

## `consistency` — ONE и QUORUM

| Уровень | Запись, мс | Чтение, мс |
|---|---:|---:|
| ONE | 1222 | 3 |
| QUORUM | 1485 | 7 |

Запись — серия из 1000 событий, чтение — 20 последних событий. Значения — медианы пяти прогонов после прогрева из `artifacts.consistency`, переведённые из секунд в миллисекунды.

## Сжатие — `tablestats`

| Таблица | Space used (total) | SSTable count | SSTable Compression Ratio |
|---|---:|---:|---:|
| `user_actions` (LZ4) | 34 580 байт | 1 | 0,39049 |
| `user_actions_none` (без сжатия) | 78 582 байт | 1 | -1,00000 |

Источник — `tablestats.txt` и `tablestats_plain.txt`, снятые на узле `c1` после сценария `consistency`. В обоих файлах локальная задержка чтения равна `NaN`: на узле `c1` для обеих таблиц `Local read count = 0`, поэтому среднее вычислить нельзя. Чтения обслуживали другие реплики.

## Bloom-фильтр

| Показатель | Значение |
|---|---:|
| Bloom filter false positives | 0 |
| Bloom filter false ratio | 0,00000 |

Источник — `tablestats.txt`, секция `hw3.user_actions`.

## `compaction` — TWCS и TTL

| Показатель | Значение |
|---|---|
| Стратегия компакции | TimeWindowCompactionStrategy, окно 1 день |
| default_time_to_live | 2 592 000 секунд (30 дней) |
| События с TTL 5 секунд: до / после истечения | 5 / 0 |

Источник — `results.json`, раздел `artifacts.compaction`, и `compaction.txt`. Результат чтения истёкших записей сохранён в `tracing.txt`.

## `data` и `repair`

`data`: проверены обе таблицы, ключи, порядок кластеризации, сжатие, вставка 20 событий и чтение последних пяти. Статус — `passed` в `results.json`.

`repair`: в `repair.txt` зафиксировано `Repair completed successfully`. Объяснения anti-entropy, repair и его отличий от read repair и hinted handoff приведены в основном README.
