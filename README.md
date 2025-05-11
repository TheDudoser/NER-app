# NER app
...

## Запуск приложения
* Установите python@3.13
* Инициализируем проект - `make init`

## Сборка и запуск приложения
* docker compose up --build

## Работа с БД напрямую
После поднятия БД проваливаемся в контейнер с postgres:
`docker compose exec postgres bash`
Заходим внутрь самого postgres в базу `ner`:
`psql ner --username=root`
