import matplotlib.pyplot as plt
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.styles import Border, Side
from jinja2 import Environment, FileSystemLoader
import pdfkit
import requests
import xmltodict
import pandas as pd
import csv
import re
import time
from datetime import datetime
import os, glob
import concurrent.futures
from multiprocessing import Pool

translateToRus = {
    "name": "Название",
    "description": "Описание",
    "key_skills": "Навыки",
    "experience_id": "Опыт работы",
    "premium": "Премиум-вакансия",
    "employer_name": "Компания",
    "currency": "Оклад",
    "area_name": "Название региона",
    "published_at": "Дата публикации вакансии"
}

experience = {
    "noExperience": "Нет опыта",
    "between1And3": "От 1 года до 3 лет",
    "between3And6": "От 3 до 6 лет",
    "moreThan6": "Более 6 лет"
}

filterToNames = {
    "Название": "name",
    "Описание": "description",
    "Навыки": "key_skills",
    "Опыт работы": "experience_id",
    "Премиум-вакансия": "premium",
    "Компания": "employer_name",
    "Оклад": "currency",
    "Название региона": "area_name",
    "Дата публикации вакансии": "published_at"
}

currency = {
    "AZN": "Манаты",
    "BYR": "Белорусские рубли",
    "EUR": "Евро",
    "GEL": "Грузинский лари",
    "KGS": "Киргизский сом",
    "KZT": "Тенге",
    "RUR": "Рубли",
    "UAH": "Гривны",
    "USD": "Доллары",
    "UZS": "Узбекский сум"
}
currency_to_rub = {
    "AZN": 35.68,
    "BYR": 23.91,
    "EUR": 59.90,
    "GEL": 21.74,
    "KGS": 0.76,
    "KZT": 0.13,
    "RUR": 1,
    "UAH": 1.64,
    "USD": 60.66,
    "UZS": 0.0055,
    "not": 1
}

class Vacancy:
    """Класс для представления вакансий.

     Attributes:
        name(list): Название вакансии
        description(list): Описание вакансии
        key_skills(list): Навыки необходимые для работы
        experience_id(list): Необходимый опыт
        premium(list): Является ли ланная вакансия премиум?
        employer_name(list): Название компании
        salary(class): Все о зарплате
        area_name(list): Название региона для вакансии
        published_at(list): Дата публикации вакансии
        elements(list): Массив всех атрибутов
     """

    def __init__(self, name, description, key_skills, experience_id, premium, employer_name, salary, area_name, published_at):
        """
        Инициализирует объект Vacancy, выполняет конвертацию для целочисленных полей.

        Args:
            name(str): Название вакансии
            description(str):  Описание вакансии
            key_skills(str): Навыки необходимые для работы
            experience_id(str): Необходимый опыт
            premium(str): Является ли ланная вакансия премиум?
            employer_name(str): Название компании
            salary(str): Все о зарплате
            area_name(str): Название региона для вакансии
            published_at(str): Дата публикации вакансии

        >>> type(Vacancy("name", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "Москва", "published_at")).__name__
        'Vacancy'
        >>> Vacancy("name", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "Москва", "published_at").area_name
        ['Москва']
        >>> Vacancy("Яндекс", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "Москва", "published_at").name
        ['Яндекс']
        >>> Vacancy("name", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "Москва", "2007-12-03T17:34:36+0300").published_at
        ['2007-12-03T17:34:36+0300']
        """
        self.name = [name]
        self.description = [description]
        self.key_skills = key_skills
        self.experience_id = [experience_id]
        self.premium = [premium]
        self.employer_name = [employer_name]
        self.salary = salary
        self.area_name = [area_name]
        self.published_at = [published_at]
        self.elements = [name, description, key_skills, experience_id, premium, employer_name, salary, area_name, published_at]


class Salary:
    """Класс для представления зарплаты.

     Attributes:
        salary_from(list): Нижняя граница вилки оклада
        salary_to(list): Верхняя граница вилки оклада
        salary_gross(list): Представлена ли зарплата с учетом налогов?
        salary_currency(list): Валюта оклада
        salary(str): Строка со всеми данными зарплаты
     """

    def __init__(self, salary_from, salary_to, salary_gross, salary_currency):
        """
        Инициализирует объект Salary, выполняет конвертацию для целочисленных полей.

        Args:
            salary_from(str): Нижняя граница вилки оклада
            salary_to(str): Верхняя граница вилки оклада
            salary_gross(str): Представлена ли зарплата с учетом налогов?
            salary_currency(str): Валюта оклада
        >>> type(Salary(100, 200,"True", "RUR")).__name__
        'Salary'
        >>> Salary(100, 200,"True", "RUR").salary_from
        [100]
        >>> Salary(100, 200,"True", "RUR").salary_to
        [200]
        >>> Salary(100, 200,"True", "RUR").salary
        '100 - 200 (Рубли) (С вычетом налогов)'
        """
        if(salary_from == ''):
            salary_from = -1
        if(salary_to == ''):
            salary_to = -1
        if(salary_currency == ''):
            salary_currency = 'not'
        self.salary_from = [salary_from]
        self.salary_to = [salary_to]
        self.salary_gross = [salary_gross]
        self.salary_currency = [salary_currency]


class DataSet:
    """Класс, который считавает CSV файл, заполняет классы Salary и Vacancy и выводит статистические данные

    Attributes:
        report(class): класс Report
        file_name(str): Название файла
        vacancies_objects(list): Массив, содержащий все данные по каждой из вакансий
    """

    def __init__(self, profession="None", file="None"):
        """Инизиализирует объект DataSet"""

        self.profession = profession
        self.file_name = file
        self.vacancies_objects = []

    def сsv_reader(self, file_name):
        """
        Считывает данные с csv файла и заполняет ими resultList и names

        Args:
            file_name(str): название файла

        Returns:
            list: данные с csv файла
        """
        names = []
        with open(file_name, encoding="utf-8-sig") as File:
            readerFile = csv.reader(File, delimiter=',',
                                    quoting=csv.QUOTE_MINIMAL)
            for row in readerFile:
                if (len(names) == 0):
                    names = row
                elif (len(row) >= len(names)):
                    self.csv_filer(row, names)
        return self.vacancies_objects

    def csv_filer(self, item, list_naming):
        """
        Заполняет классы Vacancy и Salary, а так же переводит True и False на русский язык

        Args:
            reader(list): данные со всеми вакансиями
            list_naming(list): названия полей из шапки файла

        Returns:
            list: данные со всеми вакансиями
        """

        argument = ["", "", "", "", "", "", "", "", ""]
        namesIndex = ["name", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "area_name", "published_at"]
        argSalary = ["", "", "", ""]
        nameSsalary = ["salary_from", "salary_to", "salary_gross", "salary_currency"]
        for i in range(len(list_naming)):
            element = item[i]
            if ("\n" in element):
                element = element.split("\n")
            else:
                element = element
            newArray = []
            for word in element:
                if (word.upper() == "TRUE"):
                    newArray.append("Да")
                elif (word.upper() == "FALSE"):
                    newArray.append("Нет")
                elif (word in experience.keys()):
                    newArray.append(experience[word])
                else:
                    newArray.append(DataSet.clearStr(word))
            if (len(newArray) == 1):
                newArray = newArray[0]

            if (list_naming[i] == "salary_from"):
                argSalary[nameSsalary.index(list_naming[i])] = element
            elif (list_naming[i] == "salary_to"):
                argSalary[nameSsalary.index(list_naming[i])] = element
            elif (list_naming[i] == "salary_gross"):
                argSalary[nameSsalary.index(list_naming[i])] = element
            elif (list_naming[i] == "salary_currency"):
                argSalary[nameSsalary.index(list_naming[i])] = element
                argument[namesIndex.index("salary")] = Salary(*argSalary)
            else:
                argument[namesIndex.index(list_naming[i])] = element
        self.vacancies_objects.append(Vacancy(*argument))

    def clearStr(strValue):
        """
        Чистит строку от HTML тегов

        Args:
            strValue(str): строка, которую нужно преобразовать

        Returns:
            str: строка без HTML тегов
        >>> DataSet.clearStr("<p>yes</p>")
        'yes'
        >>> DataSet.clearStr("<body><p>word</p></body>")
        'word'

        """

        return ' '.join(re.sub(r"<[^>]+>", '', strValue).split())

    def currency_to_CSV(self):
        currencyID = ["R01235", "R01239", "R01720", "R01335", "R01090"]
        currency = {
            "R01235": [],
            "R01239": [],
            "R01720": [],
            "R01335": [],
            "R01090": []
        }
        dates = []
        for curr in currencyID:
            for year in range(2003, 2023):
                for mounth in range(1, 13):
                    dat = f'{year}-{("0" + str(mounth))[-2:]}'
                    if (dat not in dates):
                        dates.append(dat)
                    for day in range(1, 29):
                        date = f'{("0" + (str(day)))[-2:]}/{("0" + str(mounth))[-2:]}/{year}'
                        response = requests.get(
                            f'http://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={date}&date_req2={date}&VAL_NM_RQ={curr}')
                        dict_data = xmltodict.parse(response.content)
                        if "Record" in dict_data["ValCurs"]:
                            currency[curr].append(round(
                                float(dict_data["ValCurs"]['Record']["Value"].replace(',', '.')) / float(
                                    dict_data["ValCurs"]['Record']["Nominal"].replace(',', '.')), 3))
                            break
                        if day == 28:
                            currency[curr].append("-")

        d = {'date': dates, 'USD': currency["R01235"], 'EUR': currency["R01239"], 'UAH': currency["R01720"],
             'KZT': currency["R01335"], 'BYR': currency["R01090"]}
        df = pd.DataFrame(data=d)
        df.to_csv('out.csv', index=False)

    def makeDict(self, vacancies_objects):
        """Заполняет класс Report и выводит статистические данные"""
        dict_currency = {}
        for vacancy in vacancies_objects:
            if (vacancy.salary.salary_currency[0] in dict_currency):
                dict_currency[vacancy.salary.salary_currency[0]] += 1
            else:
                dict_currency[vacancy.salary.salary_currency[0]] = 1
        return dict_currency

    def print_dict(self, dicrionaries):
        print("Количество валют:", dicrionaries)
        elem = {}
        for item in dicrionaries.items():
            elem[item[0]] = round(dicrionaries[item[0]] / sum(dicrionaries.values()), 4)
        print("Частотность валют:", elem)


def get_answer(result):
    dict_currency = {}
    for year in result:
        for city in year:
            if city not in dict_currency:
                dict_currency[city] = 0
            dict_currency[city] += year[city]
    return dict_currency

def get_futures(profession, allFiles):
    conclusion = DataSet(profession)
    vacancies_list = conclusion.сsv_reader(allFiles)
    return conclusion.makeDict(vacancies_list)

def pool_handler(allFiles, profession):
    conclusion = DataSet(profession)
    result = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=11) as executor:
        futures = {executor.submit(get_futures, profession, file): file for file in allFiles}
        for fut in concurrent.futures.as_completed(futures):
            result.append(fut.result())
    conclusion.print_dict(get_answer(result))

if(__name__ == "__main__"):
    #profession = input("Введите название профессии: ")
    profession = "Программист"
    data = DataSet()
    #path = input("Введите название папки: ") + '/'
    path = "allCSV/"
    allFiles = []
    for filename in glob.glob(os.path.join(path, '*.csv')):
        allFiles.append(filename)
    clock = time.time()
    pool_handler(allFiles, profession)
    data.currency_to_CSV()
    print("\nProcess has finished:", time.time() - clock)
