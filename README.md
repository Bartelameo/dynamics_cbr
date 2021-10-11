## Содержание
* [Описание](#Описание)
* [Инструменты](#technologies)
* [Запуск](#setup)

## Описание
Скрейпинг исторической динамики валютного курса заданной валюты (венгерский форинт, гонконгский доллар и т.п.) с сайта ЦБР в postgresql базу данных (за весь период наблюдений).

---

## Инструменты
Проект использует:
* python: 3.8
* postgresql: 12.8
* bautifulsoup4: 4.10.0
* psycopg2: 2.9.1
* requests: 2.26.0

---

## Запуск
<p>Изменить файл conf.py, для подключение к серверу postgresql:</p>
<pre><code>host = "IP_server"
user = "user"
password = "password"
db_name = "db_name"
port = "5432" #default_port = 5432</code></pre>

<p>Установка библиотек</p>
<pre><code>pip install -r requirements.txt</code></pre>

<p>Запустить файл run.py и следовать запросам</p>
