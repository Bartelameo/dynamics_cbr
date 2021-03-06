#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import time
import psycopg2
from datetime import date, datetime
from bs4 import BeautifulSoup
from decimal import Decimal

from config import host, user, password, db_name, port, sslmode
from headers import headers as h


def get_dict_currencieses(url):
    try:
        r = requests.get(url=url, headers=h, timeout=5)
    except TooManyRedirects as e:
        print(f'{url} : {e}')
    soup = BeautifulSoup(r.text, "html.parser")
    select_currencies = soup.find_all('select', id="UniDbQuery_VAL_NM_RQ")
    dict_currencies = {}
    for i in select_currencies[0].find_all("option"):
        currencie = i.string.strip().lower()
        dict_currencies[currencie] = i.get("value")
    return dict_currencies


def get_data(code_currencies):
    today = datetime.today().strftime('%d.%m.%Y')
    url = (f'https://cbr.ru/currency_base/dynamics/?UniDbQuery.Posted=True&UniDbQuery.so='
           f'1&UniDbQuery.mode=1&UniDbQuery.date_req1=&UniDbQuery.date_req2=&UniDbQuery.VAL_NM_RQ='
           f'{code_currencies}&UniDbQuery.From=01.01.1992&UniDbQuery.To={today}')
    try:
        r = requests.get(url=url, headers=h, timeout=5)
    except Exception as _ex:
        print(f'[INFO] {url} : {_ex}')
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
        try:
            value[0] = datetime.strptime(value[0], '%d.%m.%Y').strftime("%Y-%m-%d")
            data.append(value)
        except IndexError:
            print("[INFO] IndexError while working with data from url")
        except ValueError:
            print("[INFO] ValueError while working with data from url")

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
        print("[INFO] Exception while working with PostgreSQL")
        return True
    finally:
        if connection:
            connection.close()


def transliterate(name):
    # ?????????????? ?? ????????????????
    slovar = {'??': 'a', '??': 'b', '??': 'v', '??': 'g', '??': 'd', '??': 'e', '??': 'e',
              '??': 'zh', '??': 'z', '??': 'i', '??': 'i', '??': 'k', '??': 'l', '??': 'm', '??': 'n',
              '??': 'o', '??': 'p', '??': 'r', '??': 's', '??': 't', '??': 'u', '??': 'f', '??': 'h',
              '??': 'c', '??': 'cz', '??': 'sh', '??': 'scz', '??': '', '??': 'y', '??': '', '??': 'e',
              '??': 'u', '??': 'ja', ',': '', '?': '', ' ': '_', '~': '', '!': '', '@': '', '#': '',
              '$': '', '%': '', '^': '', '&': '', '*': '', '(': '', ')': '', '-': '', '=': '', '+': '',
              ':': '', ';': '', '<': '', '>': '', '\'': '', '"': '', '\\': '', '/': '', '???': '',
              '[': '', ']': '', '{': '', '}': '', '??': '', '??': '', '??': '', '??': 'g', '??': 'i',
              '??': 'e', '???': ''}

    name_table = []
    for n in name:
        name_table.append(slovar[n])
    return "".join(name_table)


def main():
    url0 = "https://cbr.ru/currency_base/dynamics/"
    currencies = input(f"?????????????? ???????????????? ???????????? ?? ?????? ????????, ?? ?????????????? ?????? ???????????????? ???? ?????????? {url0}: ").lower()
    name_table = transliterate(currencies)
    dict_currencies = get_dict_currencieses(url0)
    if currencies not in dict_currencies:
        print("[INFO] ???????????? ???? ??????????????")
    else:
        code_currencies = dict_currencies[currencies]
        data = get_data(code_currencies)
        try:
            connection_to_db(name_table, data[0])
            print(f'[INFO] ???????????? ??????????????! ???????????????????????? ???????????????? ???????????? ???? {len(data) - 1} ????????(??)')
            count = 0
            for d in data[1:]:
                if connection_to_db(name_table, data[0], d):
                    print(f"[INFO] ?? ???????? ???????????????? {count} ?????????? ???????????????? ????????????!")
                    break
                count += 1
            print(f"[INFO] ?? ???????? ???????????????? ?????? ???????????????? ????????????!")
        except Exception:
            pass


if __name__ == "__main__":
    main()
