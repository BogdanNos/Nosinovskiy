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
        self.salary = [salary]
        self.area_name = [area_name]
        self.published_at = [published_at]
        self.elements = [name, description, key_skills, experience_id, premium, employer_name, salary, area_name, published_at]


class Report:
    """Класс в котором создается картинка, Excel и PDF файлы со статистикой csv файла

    Attributes:
        salaryYear(dictionary): Содержит среднюю зарплату для каждого года
        numberYear(dictionary): Содержит количество вакансий для каждого года
        salaryProfessionalYear(dictionary): Содержит среднюю зарплату для каждого года определенной профессии
        numberProfessionalYear(dictionary): Содержит количество вакансий для каждого года определенной профессии
        salaryCity(dictionary): Содержит среднюю зарплату для каждого города
        vacancyCity(dictionary): Содержит количество вакансий для каждого города
    """

    def __init__(self, profession):
        """Инизиализирует объект Report"""

        self.salaryYear = {}
        self.numberYear = {}
        self.salaryProfessionalYear = {}
        self.numberProfessionalYear = {}
        self.profession = profession

    def generate_image(self):
        """Создает картику со статистикой csv файла при помощи библиотеки matplotlib"""

        plt.rcParams.update({'font.size': 8})

        x = np.arange(len(list(self.salaryYear)))
        width = 0.35
        ax = plt.subplot(221)
        ax.bar(x - width / 2, self.salaryYear.values(), width, label='средняя з/п')
        ax.bar(x + width / 2, self.salaryProfessionalYear.values(), width, label='з/п ' + self.profession)
        ax.set_title('Уровень зарплат по годам')
        ax.set_xticks(x, list(self.salaryYear), rotation=90)
        ax.legend()
        plt.grid(axis='y')

        x = np.arange(len(list(self.numberYear)))
        width = 0.35
        ax = plt.subplot(222)
        ax.bar(x - width / 2, self.numberYear.values(), width, label='количество вакансий')
        ax.bar(x + width / 2, self.numberProfessionalYear.values(), width,
               label='количество вакансий \n' + self.profession)
        ax.set_title('Количество вакансий по годам')
        ax.set_xticks(x, list(self.numberYear), rotation=90)
        ax.legend()
        plt.grid(axis='y')


        plt.subplots_adjust(wspace=0.5, hspace=0.5)
        plt.savefig('graph.png', dpi=200, bbox_inches='tight')

   
    def generate_pdf(self):
        """Создает PDF файл со статистикой csv файла при помощи библиотеки pdfkit"""

        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("1.html")
        pdf_template = template.render({'name': self.profession})
        pdf_template = pdf_template.replace("$way", os.path.abspath(os.curdir) + "\\")
        config = pdfkit.configuration(wkhtmltopdf=r'D:\wkhtmltopdf\bin\wkhtmltopdf.exe')
        options = {'enable-local-file-access': None}
        table = self.generate_table()
        pdf_template = pdf_template.replace("$table;", table)
        pdfkit.from_string(pdf_template, 'report.pdf', configuration=config, options=options)

    def generate_table(self):
        """
        Создает таблицу при помощи HTML кода

        Returns:
            str: таблица со статистикой HTML кодом

        >>> Report("Программист").generate_table()
        "<table class='table'><tr><th>Год</th><th>Средняя зарплата</th><th>Средняя зарплата - Программист</th><th>Количество вакансий</th><th>Количество вакансий - Программист</th></tr></tr></table><h1>Статистика по городам</h1><table class='table1'><tr><th>Город</th><th>Уровень зарплат</th></tr></table><table class='table2'><tr><th>Город</th><th>Уровень зарплат</th></tr></table>"
        """

        table = "<table class='table'><tr><th>Год</th><th>Средняя зарплата</th><th>Средняя зарплата - "
        table += self.profession + "</th><th>Количество вакансий</th><th>Количество вакансий - " + self.profession + "</th></tr>"
        for i in range(len(list(self.salaryYear))):
            table += "<tr>"
            table += ("<td>" + str(list(self.salaryYear)[i]) + "</td>")
            table += ("<td>" + str(list(self.salaryYear.values())[i]) + "</td>")
            table += ("<td>" + str(list(self.numberYear.values())[i]) + "</td>")
            table += ("<td>" + str(list(self.salaryProfessionalYear.values())[i]) + "</td>")
            table += ("<td>" + str(list(self.numberProfessionalYear.values())[i]) + "</td>")
            table += "</tr>"
        table += "</tr></table>"
        return table



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
        self.report = Report(self.profession)
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
            item(list): одна вакансия
            list_naming(list): названия полей из шапки файла

        """

        argument = ["", "", "", "", "", "", "", "", ""]
        namesIndex = ["name", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "area_name", "published_at"]
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

    def lets_chunk(self):
        dictionary = {}
        def write_chunk(part, lines):
            with open('newCSV//data_'+ str(part) +'.csv', 'w', encoding="utf-8-sig") as f_out:
                f_out.write(header)
                f_out.writelines(lines)
                f_out.close()

        with open(bigFile, 'r', encoding="utf-8-sig") as f:
            header = f.readline()
            for x in f:
                listLine = x.split(",")
                year = listLine[-1].split('-')[0]
                if (year in dictionary.keys()):
                    dictionary[year].append(x)
                else:
                    dictionary[year] = [x]

            for data in dictionary:
                write_chunk(data, dictionary[data])

    def formatDateTime(self, time):
        """
        Преобразует строку даты публикации вакансии

        Args:
            time(str): строка, которую нужно преобразовать

        Returns:
            str: строка времени в нужном формате

        """
        value = [time.split("T")[0].split("-")[0], time.split("T")[0].split("-")[1], time.split("T")[0].split("-")[2]]
        day = datetime(int(value[0]), int(value[1]), int(value[2]), 0, 0, 0)
        return day.strftime('%Y-%m')


    def makeAndPrintDict(self, vacancies_objects):
        """Заполняет класс Report и выводит статистические данные

        Args:
            vacancies_objects(list): массив со всеми вакансиями
        """

        dicrionaries = {
            "salaryYear": {},
            "NumberYear": {},
            "salaryProfessionalYear": {},
            "NumberProfessionalYear": {},
            "salaryCity": {},
            "vacancyCity": {}
        }
        for vacancyByYear in vacancies_objects:
            for vacancy in vacancyByYear:
                if(vacancy.salary[0] != ''):
                    if (int(vacancy.published_at[0][0:4]) in dicrionaries["NumberYear"]):
                        dicrionaries["NumberYear"][int(vacancy.published_at[0][0:4])] += 1
                    else:
                        dicrionaries["NumberYear"][int(vacancy.published_at[0][0:4])] = 1
                        dicrionaries["NumberProfessionalYear"][int(vacancy.published_at[0][0:4])] = 0

                    if (int(vacancy.published_at[0][0:4]) in dicrionaries["salaryYear"]):
                        dicrionaries["salaryYear"][int(vacancy.published_at[0][0:4])] += [float(vacancy.salary[0])]
                    else:
                        dicrionaries["salaryYear"][int(vacancy.published_at[0][0:4])] = [float(vacancy.salary[0])]
                        dicrionaries["salaryProfessionalYear"][int(vacancy.published_at[0][0:4])] = [0]

                    if (self.profession in vacancy.name[0]):
                        if (int(vacancy.published_at[0][0:4]) in dicrionaries["NumberProfessionalYear"]):
                            dicrionaries["NumberProfessionalYear"][int(vacancy.published_at[0][0:4])] += 1
                        else:
                            dicrionaries["NumberProfessionalYear"][int(vacancy.published_at[0][0:4])] = 1

                        if (int(vacancy.published_at[0][0:4]) in dicrionaries["salaryProfessionalYear"].keys()):
                            dicrionaries["salaryProfessionalYear"][int(vacancy.published_at[0][0:4])] += [float(vacancy.salary[0])]
                        else:
                            dicrionaries["salaryProfessionalYear"][int(vacancy.published_at[0][0:4])] = [float(vacancy.salary[0])]

        elem = {}
        for item in dicrionaries["salaryYear"].items():
            elem[item[0]] = int(sum(dicrionaries["salaryYear"][item[0]]) / len(dicrionaries["salaryYear"][item[0]]))
        self.report.salaryYear = elem
        print("Динамика уровня зарплат по годам:", elem)

        self.report.numberYear = dicrionaries["NumberYear"]
        print("Динамика количества вакансий по годам:", dicrionaries["NumberYear"])

        elem = {}
        for item in dicrionaries["salaryProfessionalYear"].items():
            if (len(dicrionaries["salaryProfessionalYear"][item[0]]) > 1):
                elem[item[0]] = int(sum(dicrionaries["salaryProfessionalYear"][item[0]]) / (
                            len(dicrionaries["salaryProfessionalYear"][item[0]]) - 1))
            else:
                elem[item[0]] = 0
        self.report.salaryProfessionalYear = elem
        print("Динамика уровня зарплат по годам для выбранной профессии:", elem)

        self.report.numberProfessionalYear = dicrionaries["NumberProfessionalYear"]
        print("Динамика количества вакансий по годам для выбранной профессии:", dicrionaries["NumberProfessionalYear"])

def pool_handler(allFiles, profession):
    """Запускает все csv файлы в мультипотоке

    Args:
        allFiles(list): массив со всеми файлами
        profession(str): нужная профессия

    Returns:
        list: массив со всеми вакансиями
    """

    conclusion = DataSet(profession)
    result = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=11) as executor:
        futures = {executor.submit(conclusion.сsv_reader, file): file for file in allFiles}
        for fut in concurrent.futures.as_completed(futures):
            result.append(fut.result())
    return result

if(__name__ == "__main__"):
    bigFile = input("Введите название файла: ")
    profession = input("Введите название профессии: ")
    conclusion = DataSet(profession)
    conclusion.lets_chunk()
    path = "newCSV/"
    allFiles = []
    for filename in glob.glob(os.path.join(path, '*.csv')):
        allFiles.append(filename)
    clock = time.time()
    multi = pool_handler(allFiles, profession)
    conclusion.makeAndPrintDict(multi)
    conclusion.report.generate_image()
    conclusion.report.generate_pdf()
    print("\nProcess has finished:", time.time() - clock)
