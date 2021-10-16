#!/usr/bin/python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import time
from datetime import date, datetime
from config import host, user, password, db_name, port, sslmode
import psycopg2
from decimal import *


def get_dict_currencieses(url):
    headers = {
        "user-agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/94.0.4606.71 Safari/537.36"),
        "accept": "text/css,*/*;q=0.1",
    }
    try:
        r = requests.get(url=url, headers=headers, timeout=5)
    except TooManyRedirects as e:
        print(f'{url} : {e}')
    time.sleep(1)
    soup = BeautifulSoup(r.text, "html.parser")
    select_currencies = soup.find_all('select', id="UniDbQuery_VAL_NM_RQ")
    dict_currencies = {}
    for i in select_currencies[0].find_all("option"):
        currencie = i.string.replace("\n", "").split("  ")[14].lower().replace("\r", "").rstrip()  # HA-HA(!)
        dict_currencies[currencie] = i.get("value")
    return dict_currencies


def get_data(code_currencies):
    headers = {
        "user-agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/94.0.4606.71 Safari/537.36"),
        "accept": "text/css,*/*;q=0.1",
    }
    today = datetime.today().strftime('%d.%m.%Y')
    url = (f'https://cbr.ru/currency_base/dynamics/?UniDbQuery.Posted=True&UniDbQuery.so='
           f'1&UniDbQuery.mode=1&UniDbQuery.date_req1=&UniDbQuery.date_req2=&UniDbQuery.VAL_NM_RQ='
           f'{code_currencies}&UniDbQuery.From=01.01.1992&UniDbQuery.To={today}')
    try:
        r = requests.get(url=url, headers=headers, timeout=5)
    except TooManyRedirects as e:
        print(f'{url} : {e}')
    soup = BeautifulSoup(r.text, "html.parser")
    block_data = soup.find('div', class_="table")
    data = []
    name = block_data.find("h3").text
    alldata = block_data.find_all("tr")
    name_of_columns = alldata[1].text.split()
    name_of_columns.pop(1)
    data.append(name_of_columns)
    for i in alldata[2:]:
        value = i.text.split()
        value[0] = datetime.strptime(value[0], '%d.%m.%Y').strftime("%Y-%m-%d")
        data.append(value)
    return data


def connection_to_db(name_table, columns, value=0):
    try:
        # connect to exist database
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name,
            port=port,
            sslmode=sslmode)
        connection.autocommit = True
        if value != 0:
            insert = (f"INSERT INTO {name_table} ({columns[0]}, {columns[1]}, {columns[2]}) "
                      f"VALUES ('{value[0]}',{int(value[1])}, {Decimal(value[2].replace(',', '.'))});")
            massage = "[INFO] Data was succefully inserted"
        else:
            insert = (f"CREATE TABLE IF NOT EXISTS {name_table}({columns[0]} DATE UNIQUE, "
                      f"{columns[1]} INTEGER, {columns[2]} REAL);")
            massage = f"[INFO] Table {name_table} created successfully"
        with connection.cursor() as cursor:
            cursor.execute(insert)
    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            connection.close()


def transliterate(name):
    # Слоаврь с заменами
    slovar = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
              'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
              'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h',
              'ц': 'c', 'ч': 'cz', 'ш': 'sh', 'щ': 'scz', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e',
              'ю': 'u', 'я': 'ja', ',': '', '?': '', ' ': '_', '~': '', '!': '', '@': '', '#': '',
              '$': '', '%': '', '^': '', '&': '', '*': '', '(': '', ')': '', '-': '', '=': '', '+': '',
              ':': '', ';': '', '<': '', '>': '', '\'': '', '"': '', '\\': '', '/': '', '№': '',
              '[': '', ']': '', '{': '', '}': '', 'ґ': '', 'ї': '', 'є': '', 'Ґ': 'g', 'Ї': 'i',
              'Є': 'e', '—': ''}

    for key in slovar:
        name = name.replace(key, slovar[key])
    return name


def main():
    url0 = "https://cbr.ru/currency_base/dynamics/"
    currencies = input(f"Введите название валюты в том виде, в котором она записана на сайте {url0}: ").lower()
    name_table = transliterate(currencies)
    dict_currencies = get_dict_currencieses(url0)
    if currencies not in dict_currencies:
        print("[INFO] Валюта не найдена. Выход")
    else:
        code_currencies = dict_currencies[currencies]
        data = get_data(code_currencies)
        connection_to_db(name_table, data[0])
        count = len(data) - 1
        print(f'[INFO] Валюта найдена! Обрабатываем динамику валюты за {count} дней(я)')
        for d in data[1:]:
            connection_to_db(name_table, data[0], d)
        print(f"[INFO] В базу записаны все значений валюты!")


if __name__ == "__main__":
    main()
