import matplotlib.pyplot as plt
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.styles import Border, Side
from jinja2 import Environment, FileSystemLoader
import pdfkit
import csv
import re
from prettytable import PrettyTable
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
}


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
        self.salaryCity = {}
        self.vacancyCity = {}
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

        ax = plt.subplot(223)
        ax.set_title('Уровень зарплат по городам')
        y_pos = np.arange(len(list(self.salaryCity)))
        performance = self.salaryCity.values()
        ax.barh(y_pos, performance, align='center')
        ax.set_yticks(y_pos, labels=list(self.salaryCity))
        ax.invert_yaxis()
        plt.grid(axis='x')

        colors = ["g", "r", "#FF00BB", "0.5", "y", "b", "#05FFBB", "#70F750", "#569712", "#589656", "#BBBB75"]
        ax = plt.subplot(224)
        ax.set_title('Доля вакансий по городам')
        plt.rcParams.update({'font.size': 6})
        ax.pie(list(self.vacancyCity.values()) + [1 - sum(self.vacancyCity.values())], colors=colors,
               labels=list(self.vacancyCity) + ["Другие"])

        plt.subplots_adjust(wspace=0.5, hspace=0.5)
        plt.savefig('graph.png', dpi=200, bbox_inches='tight')

    def generate_excel(self):
        """Создает Excel файл со статистикой csv файла при помощи класса Workbook из библиотеки openpyxl"""

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Статистика по годам"
        ft = Font(bold=True)

        sheet["A1"] = "Год"
        sheet["A1"].font = ft
        sheet["B1"] = "Средняя зарплата"
        sheet["B1"].font = ft
        sheet["C1"] = "Средняя зарплата - " + self.profession
        sheet["C1"].font = ft
        sheet["D1"] = "Количество вакансий"
        sheet["D1"].font = ft
        sheet["E1"] = "Количество вакансий - " + self.profession
        sheet["E1"].font = ft

        count = 1
        for item in self.salaryYear.items():
            count += 1
            sheet["A" + str(count)] = int(item[0])
            sheet["B" + str(count)] = int(item[1])
        count = 1
        for item in self.salaryProfessionalYear.items():
            count += 1
            sheet["C" + str(count)] = int(item[1])
        count = 1
        for item in self.numberYear.items():
            count += 1
            sheet["D" + str(count)] = int(item[1])
        count = 1
        for item in self.numberProfessionalYear.items():
            count += 1
            sheet["E" + str(count)] = int(item[1])

        worksheet = workbook.create_sheet('Статистика по городам')
        worksheet["A1"] = "Город"
        worksheet["A1"].font = ft
        worksheet["B1"] = "Уровень зарплат"
        worksheet["B1"].font = ft
        worksheet["D1"] = "Город"
        worksheet["D1"].font = ft
        worksheet["E1"] = "Доля вакансий"
        worksheet["E1"].font = ft

        count = 1
        for item in self.salaryCity.items():
            count += 1
            worksheet["A" + str(count)] = str(item[0])
            worksheet["B" + str(count)] = int(item[1])
        count = 1
        for item in self.vacancyCity.items():
            count += 1
            worksheet["D" + str(count)] = str(item[0])
            worksheet["E" + str(count)].value = str(round(item[1] * 100, 2)) + "%"
            worksheet["E" + str(count)].number_format = '0.00%'

        self.columnWidth(worksheet)
        self.columnWidth(sheet)
        self.makeBorder(worksheet)
        self.makeBorder(sheet)
        workbook.save(filename="report.xlsx")

    def makeBorder(self, worksheet):
        """
        Создает границы в Excel файле

        Args:
            worksheet(Worksheet): Активная вкладка Excel файла
        """

        thin = Side(border_style="thin", color="000000")
        for row in worksheet:
            for cell in row:
                cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)

    def columnWidth(self, worksheet):
        """
        Задает ширину столбцов в Excel файле

        Args:
            worksheet(Worksheet): Активная вкладка Excel файла
        """

        dims = {}
        for row in worksheet.rows:
            for cell in row:
                if cell.value:
                    dims[cell.column_letter] = max((dims.get(cell.column_letter, 0), len(str(cell.value)))) + 0.2
        for col, value in dims.items():
            worksheet.column_dimensions[col].width = value

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
        table += "</tr></table><h1>Статистика по городам</h1>"
        table += "<table class='table1'><tr><th>Город</th><th>Уровень зарплат</th>"
        for i in range(len(list(self.salaryCity))):
            table += "<tr>"
            table += ("<td>" + str(list(self.salaryCity)[i]) + "</td>")
            table += ("<td>" + str(list(self.salaryCity.values())[i]) + "</td>")
            table += "</tr>"
        table += "</tr></table>"
        table += "<table class='table2'><tr><th>Город</th><th>Уровень зарплат</th>"
        for i in range(len(list(self.vacancyCity))):
            table += "<tr>"
            table += ("<td>" + str(list(self.vacancyCity)[i]) + "</td>")
            table += ("<td>" + str(round(list(self.vacancyCity.values())[i] * 100, 2)) + "%" + "</td>")
            table += "</tr>"
        table += "</tr></table>"
        return table


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

    def __init__(self, name, description, key_skills, experience_id, premium, employer_name, salary, area_name,
                 published_at):
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
        self.elements = [name, description, key_skills, experience_id, premium, employer_name, salary, area_name,
                         published_at]


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

        self.salary_from = [salary_from]
        self.salary_to = [salary_to]
        self.salary_gross = [salary_gross]
        self.salary_currency = [salary_currency]
        self.salary = str('{:,}'.format(int(float(salary_from))).replace(',', ' ')) + " - " + str(
            '{:,}'.format(int(float(salary_to))).replace(',', ' ')) + " (" + currency[salary_currency] + ") (" + (
                          "Без вычета налогов" if salary_gross.upper() == "ДА" else "С вычетом налогов") + ")"


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
                elif (len(row) >= len(names) and not ("" in row)):
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
        namesIndex = ["name", "description", "key_skills", "experience_id", "premium", "employer_name", "salary",
                      "area_name", "published_at"]
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

    def makeDict(self, vacancies_objects):
        """Заполняет класс Report и выводит статистические данные"""

        dicrionaries = {
            "salaryYear": {},
            "NumberYear": {},
            "salaryProfessionalYear": {},
            "NumberProfessionalYear": {},
            "salaryCity": {},
            "vacancyCity": {}
        }
        for vacancy in vacancies_objects:
            if (int(vacancy.published_at[0][0:4]) in dicrionaries["NumberYear"]):
                dicrionaries["NumberYear"][int(vacancy.published_at[0][0:4])] += 1
            else:
                dicrionaries["NumberYear"][int(vacancy.published_at[0][0:4])] = 1
                dicrionaries["NumberProfessionalYear"][int(vacancy.published_at[0][0:4])] = 0

            if (int(vacancy.published_at[0][0:4]) in dicrionaries["salaryYear"]):
                dicrionaries["salaryYear"][int(vacancy.published_at[0][0:4])] += [
                    currency_to_rub[vacancy.salary.salary_currency[0]] * (
                                float(vacancy.salary.salary_from[0]) + float(vacancy.salary.salary_to[0])) / 2]
            else:
                dicrionaries["salaryYear"][int(vacancy.published_at[0][0:4])] = [
                    currency_to_rub[vacancy.salary.salary_currency[0]] * (
                                float(vacancy.salary.salary_from[0]) + float(vacancy.salary.salary_to[0])) / 2]
                dicrionaries["salaryProfessionalYear"][int(vacancy.published_at[0][0:4])] = [0]

            if (vacancy.area_name[0] in dicrionaries["salaryCity"]):
                dicrionaries["salaryCity"][vacancy.area_name[0]] += [
                    currency_to_rub[vacancy.salary.salary_currency[0]] * (
                                float(vacancy.salary.salary_from[0]) + float(vacancy.salary.salary_to[0])) / 2]
            else:
                dicrionaries["salaryCity"][vacancy.area_name[0]] = [
                    currency_to_rub[vacancy.salary.salary_currency[0]] * (
                                float(vacancy.salary.salary_from[0]) + float(vacancy.salary.salary_to[0])) / 2]

            if (vacancy.area_name[0] in dicrionaries["vacancyCity"]):
                dicrionaries["vacancyCity"][vacancy.area_name[0]] += 1
            else:
                dicrionaries["vacancyCity"][vacancy.area_name[0]] = 1

            if (self.profession in vacancy.name[0]):
                if (int(vacancy.published_at[0][0:4]) in dicrionaries["NumberProfessionalYear"]):
                    dicrionaries["NumberProfessionalYear"][int(vacancy.published_at[0][0:4])] += 1
                else:
                    dicrionaries["NumberProfessionalYear"][int(vacancy.published_at[0][0:4])] = 1

                if (int(vacancy.published_at[0][0:4]) in dicrionaries["salaryProfessionalYear"].keys()):
                    dicrionaries["salaryProfessionalYear"][int(vacancy.published_at[0][0:4])] += [
                        currency_to_rub[vacancy.salary.salary_currency[0]] * (
                                    float(vacancy.salary.salary_from[0]) + float(vacancy.salary.salary_to[0])) / 2]
                else:
                    dicrionaries["salaryProfessionalYear"][int(vacancy.published_at[0][0:4])] = [
                        currency_to_rub[vacancy.salary.salary_currency[0]] * (
                                    float(vacancy.salary.salary_from[0]) + float(vacancy.salary.salary_to[0])) / 2]
        return dicrionaries

    def print_dict(self, dicrionaries):
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

        elem = {}
        for item in dicrionaries["salaryCity"].items():
            if (len(dicrionaries["salaryCity"][item[0]]) / sum(dicrionaries["NumberYear"].values()) >= 0.01):
                elem[item[0]] = int(sum(dicrionaries["salaryCity"][item[0]]) / len(dicrionaries["salaryCity"][item[0]]))
        elem = dict(sorted(elem.items(), key=lambda item: item[1], reverse=True)[:10])
        self.report.salaryCity = elem
        print("Уровень зарплат по городам (в порядке убывания):", elem)

        elem = {}
        for item in dicrionaries["vacancyCity"].items():
            if (dicrionaries["vacancyCity"][item[0]] / sum(dicrionaries["NumberYear"].values()) >= 0.01):
                elem[item[0]] = round(dicrionaries["vacancyCity"][item[0]] / sum(dicrionaries["NumberYear"].values()),
                                      4)
        elem = dict(sorted(elem.items(), key=lambda item: item[1], reverse=True)[:10])
        self.report.vacancyCity = elem
        print("Доля вакансий по городам (в порядке убывания):", elem)


class InputConnect:
    """
    Заполняет, фильтрует, сортирует и отрисовывает таблицу с вакансиями

    Attributes:
        data(class): Класс DataSet
    """

    def __init__(self):
        """Инизиализирует объект InputConnect"""

        self.data = DataSet()

    def formatDateTime1(self, time):
        return time.split("T")[0].split("-")[2] + "." + time.split("T")[0].split("-")[1] + "." + \
               time.split("T")[0].split("-")[0]

    def formatDateTime2(self, time):
        value = datetime.strptime(time.replace("+", ".").replace("T", " "), '%Y-%m-%d %H:%M:%S.%f')
        return ("0" + str(value.day))[-2:] + "." + str(value.month) + "." + str(value.year)

    def formatDateTime3(self, time):
        value = [time.split("T")[0].split("-")[0], time.split("T")[0].split("-")[1], time.split("T")[0].split("-")[2]]
        day = datetime(int(value[0]), int(value[1]), int(value[2]), 0, 0, 0)
        return day.strftime('%d.%m.%Y')

    def formatDateTime4(self, time):
        value = [time.split("T")[0].split("-")[2], time.split("T")[0].split("-")[1], time.split("T")[0].split("-")[0]]
        return ".".join(value)

    def filter_parametr(self, row, filtration):
        """
        Фильтрует таблицу по вводимым значениям

        Args:
            row(list): вакансия, которую нужно преобразовать

        Returns:
            list: отфильтрованная вакансия

        >>> filtration = ["Название", "Программист"]
        >>> InputConnect().filter_parametr(Vacancy("Аналитик", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "Москва", "2007-12-03T17:34:36+0300"), filtration)
        {}
        """

        count = 0
        if (filtration[0] == "Идентификатор валюты оклада"):
            if (str(row.salary.salary).split("(")[1].split(")")[0] == filtration[1]):
                return row
        elif (filtration[0] == "Оклад"):
            if (int(float(row.salary.salary_from[0])) <= int(filtration[1]) <= int(float(row.salary.salary_to[0]))):
                return row
        elif (filtration[0] == "Дата публикации вакансии"):
            if (self.formatDateTime1(row.published_at[0]) == filtration[1]):
                return row

        elif (filtration[0] == "Навыки"):
            skills = filtration[1].split(", ")
            for item in skills:
                if (item in row.key_skills):
                    count += 1
            if (count == len(skills)):
                return row
        elif (filtration[0] == ""):
            return row
        elif (getattr(row, filterToNames[filtration[0]]) == filtration[1]):
            return row
        return {}

    def print_vacancies(self, data_vacancies, dic_naming):
        """
        Сортирует таблицу по вводимым значениям и отрисовывает ее

        Args:
            data_vacancies(list): Массив, со всеми вакансиями
            dic_naming(dict): Названия полей
        """

        counter = 0
        mytable = PrettyTable()
        mytable._max_width = {"Название": 20, "Описание": 20, "Навыки": 20, "Опыт работы": 20, "Премиум-вакансия": 20,
                              "Компания": 20, "Оклад": 20, "Название региона": 20, "Дата публикации вакансии": 20}

        mytable.field_names = ["№"] + list(dic_naming.values())
        mytable.hrules = 1
        mytable.align = "l"

        if (sortirovka == "Оклад"):
            data_vacancies = sorted(data_vacancies, key=lambda x: currency_to_rub[x.salary.salary_currency] * (
                        float(x.salary.salary_from) + float(x.salary.salary_to)),
                                    reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Дата публикации вакансии"):
            data_vacancies = sorted(data_vacancies, key=lambda x: x.published_at,
                                    reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Навыки"):
            data_vacancies = sorted(data_vacancies,
                                    key=lambda x: len(x.key_skills) if type(x.key_skills) == list else 1,
                                    reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Опыт работы"):
            data_vacancies = sorted(data_vacancies, key=lambda x: x.experience_id[3],
                                    reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Премиум-вакансия"):
            data_vacancies = sorted(data_vacancies, key=lambda x: "Да" if x.premium.upper() == "TRUE" else "Нет",
                                    reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Название"):
            data_vacancies = sorted(data_vacancies, key=lambda x: x.name,
                                    reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Описание"):
            data_vacancies = sorted(data_vacancies, key=lambda x: x.description,
                                    reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Компания"):
            data_vacancies = sorted(data_vacancies, key=lambda x: x.employer_name,
                                    reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka != ""):
            data_vacancies = sorted(data_vacancies, key=lambda x: x.area_name,
                                    reverse=(True if (sortOrder == "Да") else False))

        for vacancy in data_vacancies:
            counter += 1
            vacancy = self.filter_parametr(vacancy, filtration)
            val = [str(counter)]
            if (type(vacancy) != dict):
                for item in vacancy.elements:
                    if (type(item) == list):
                        element = ('\n'.join(str(x) for x in item))
                    elif (type(item) == Salary):
                        element = item.salary
                    else:
                        element = item
                    val.append(str(element) if (len(element) < 100) else (element[0:100] + "..."))

                popVal = val.pop().split("T")[0]
                val.append(popVal.split("-")[2] + "." + popVal.split("-")[1] + "." + popVal.split("-")[0])
            if (len(val) > 1):
                mytable.add_row(val)
            else:
                counter -= 1
        if (counter == 0):
            print("Ничего не найдено")
        else:
            print(mytable.get_string(fields=(["№"] + (column if len(column) > 1 else list(dic_naming.values()))),
                                     start=(int(lines[0]) - 1 if len(lines) > 0 else 0),
                                     end=(int(lines[1]) - 1 if len(lines) > 1 else counter)))

    def PrintFunction(self):
        """Вызывает все необходимые функции для отрисовки таблицы"""

        if (os.stat(file).st_size == 0):
            print("Пустой файл")
        elif (len(filtration) == 1 and len(filtration[0]) > 0):
            print("Формат ввода некорректен")
        elif ((filtration[0] not in (list(filterToNames.keys()) + ["Идентификатор валюты оклада"])) and filtration[
            0] != ""):
            print("Параметр поиска некорректен")
        elif (sortirovka not in translateToRus.values() and sortirovka != ""):
            print("Параметр сортировки некорректен")
        elif (sortOrder not in ["Да", "Нет", ""]):
            print("Порядок сортировки задан некорректно")
        else:
            if self.data.сsv_reader(file) == []:
                print("Нет данных")
            else:
                self.print_vacancies(self.data.сsv_reader(file), translateToRus)


def get_answer(result):
    salaryCity = {}
    vacancyCity = {}
    for year in result:
        for city in year["salaryCity"]:
            if city not in salaryCity:
                salaryCity[city] = []
            salaryCity[city] += year["salaryCity"][city]
        for city in year["vacancyCity"]:
            if city not in vacancyCity:
                vacancyCity[city] = 0
            vacancyCity[city] += year["vacancyCity"][city]
    NumberYear = {}
    salaryYear = {}
    salaryProfessionalYear = {}
    NumberProfessionalYear = {}
    for year in result:
        items = list(year["salaryYear"].items())[0]
        salaryYear[items[0]] = items[1]
        items = list(year["NumberYear"].items())[0]
        NumberYear[items[0]] = items[1]
        items = list(year["salaryProfessionalYear"].items())[0]
        salaryProfessionalYear[items[0]] = items[1]
        items = list(year["NumberProfessionalYear"].items())[0]
        NumberProfessionalYear[items[0]] = items[1]
    salaryYear = dict(sorted(salaryYear.items(), key=lambda x: x[0]))
    NumberYear = dict(sorted(NumberYear.items(), key=lambda x: x[0]))
    salaryProfessionalYear = dict(sorted(salaryProfessionalYear.items(), key=lambda x: x[0]))
    NumberProfessionalYear = dict(sorted(NumberProfessionalYear.items(), key=lambda x: x[0]))
    dicrionaries = {
        "salaryYear": salaryYear,  # {2007: [40, 50], 2008:[123, 1231]}
        "NumberYear": NumberYear,  # {2007: 123, 2008:132}
        "salaryProfessionalYear": salaryProfessionalYear,  # {2007: [40, 50], 2008:[123, 1231]}
        "NumberProfessionalYear": NumberProfessionalYear,  # {2007: 123, 2008:132}
        "salaryCity": salaryCity,
        "vacancyCity": vacancyCity
    }
    return dicrionaries

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
    conclusion.report.generate_image()
    conclusion.report.generate_excel()
    conclusion.report.generate_pdf()

if(__name__ == "__main__"):
    start = input("Вакансии или Статистика: ")
    connect = InputConnect()
    if (start == "Статистика"):
        profession = input("Введите название профессии: ")
        path = input("Введите название папки: ") + '/'
        allFiles = []
        for filename in glob.glob(os.path.join(path, '*.csv')):
            allFiles.append(filename)
        clock = time.time()
        pool_handler(allFiles, profession)
        print("\nProcess has finished:", time.time() - clock)

    elif (start == "Вакансии"):
        file = input("Введите название файла: ")
        filtration = input("Введите параметр фильтрации: ").split(": ")
        sortirovka = input("Введите параметр сортировки: ")
        sortOrder = input("Обратный порядок сортировки (Да / Нет): ")
        lines = input("Введите диапазон вывода: ").split()
        column = input("Введите требуемые столбцы: ").split(", ")
        connect.PrintFunction()

