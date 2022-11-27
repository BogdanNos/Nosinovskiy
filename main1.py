import matplotlib.pyplot as plt
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.styles import Border, Side
from jinja2 import Environment, FileSystemLoader
import pdfkit
import csv
import re
import os
from prettytable import PrettyTable
start = input("Выбор команд: Вакансии или Статистика: ")
file = input("Введите название файла: ")
resultList = []
names = []

translateToRus = {
"name":"Название",
"description":"Описание",
"key_skills":"Навыки",
"experience_id":"Опыт работы",
"premium":"Премиум-вакансия",
"employer_name":"Компания",
"currency": "Оклад",
"area_name":"Название региона",
"published_at":"Дата публикации вакансии"
}

experience = {
"noExperience": "Нет опыта",
"between1And3": "От 1 года до 3 лет",
"between3And6": "От 3 до 6 лет",
"moreThan6" : "Более 6 лет"
}

filterToNames = {
"Название": "name",
"Описание":"description",
"Навыки":"key_skills",
"Опыт работы":"experience_id",
"Премиум-вакансия":"premium",
"Компания":"employer_name",
"Оклад": "currency",
"Название региона":"area_name",
"Дата публикации вакансии":"published_at"
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

class Vacancy:
    def __init__(self, name, description, key_skills, experience_id, premium, employer_name, salary, area_name, published_at):
        self.name = [name]
        self.description = [description]
        self.key_skills = key_skills
        self.experience_id = [experience_id]
        self.premium = [premium]
        self.employer_name = [employer_name]
        self.salary = salary
        self.area_name = [area_name]
        self.published_at = [published_at]
        self.elements=[name, description, key_skills, experience_id, premium, employer_name, salary, area_name, published_at]

class Salary:
    def __init__(self, salary_from, salary_to, salary_gross, salary_currency):
        self.salary_from = [salary_from]
        self.salary_to = [salary_to]
        self.salary_gross = [salary_gross]
        self.salary_currency = [salary_currency]
        self.salary = str('{:,}'.format(int(float(salary_from))).replace(',', ' ')) + " - " + str('{:,}'.format(int(float(salary_to))).replace(',', ' ')) + " (" + currency[salary_currency] + ") (" + ("Без вычета налогов" if salary_gross.upper() == "ДА" else "С вычетом налогов") + ")"


class Report:
    def __init__(self):
        self.salaryYear = {}
        self.numberYear = {}
        self.salaryProfessionalYear = {}
        self.numberProfessionalYear = {}
        self.salaryCity = {}
        self.vacancyCity = {}

    def generate_image(self):
        plt.rcParams.update({'font.size': 8})

        x = np.arange(len(list(self.salaryYear)))
        width = 0.35
        ax = plt.subplot(221)
        ax.bar(x - width / 2, self.salaryYear.values(), width, label='средняя з/п')
        ax.bar(x + width / 2, self.salaryProfessionalYear.values(), width, label='з/п ' + profession)
        ax.set_title('Уровень зарплат по годам')
        ax.set_xticks(x, list(self.salaryYear), rotation = 90)
        ax.legend()
        plt.grid(axis='y')

        x = np.arange(len(list(self.numberYear)))
        width = 0.35
        ax = plt.subplot(222)
        ax.bar(x - width / 2, self.numberYear.values(), width, label='количество вакансий')
        ax.bar(x + width / 2, self.numberProfessionalYear.values(), width, label='количество вакансий \n' + profession)
        ax.set_title('Количество вакансий по годам')
        ax.set_xticks(x, list(self.numberYear), rotation = 90)
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
        ax.pie(list(self.vacancyCity.values()) + [1 - sum(self.vacancyCity.values())], colors=colors, labels=list(self.vacancyCity) + ["Другие"])

        plt.subplots_adjust(wspace=0.5, hspace=0.5)
        plt.savefig('graph.png', dpi = 200, bbox_inches='tight')

    def generate_excel(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Статистика по годам"
        ft = Font(bold=True)

        sheet["A1"] = "Год"
        sheet["A1"].font = ft
        sheet["B1"] = "Средняя зарплата"
        sheet["B1"].font = ft
        sheet["C1"] = "Средняя зарплата - " + profession
        sheet["C1"].font = ft
        sheet["D1"] = "Количество вакансий"
        sheet["D1"].font = ft
        sheet["E1"] = "Количество вакансий - " + profession
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
        thin = Side(border_style="thin", color="000000")
        for row in worksheet:
            for cell in row:
                cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)

    def columnWidth(self, worksheet):
        dims = {}
        for row in worksheet.rows:
            for cell in row:
                if cell.value:
                    dims[cell.column_letter] = max((dims.get(cell.column_letter, 0), len(str(cell.value)))) + 0.2
        for col, value in dims.items():
            worksheet.column_dimensions[col].width = value

    def generate_pdf(self):
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template("1.html")
        pdf_template = template.render({'name': profession})
        pdf_template = pdf_template.replace("$way", os.path.abspath(os.curdir)+"\\" )
        config = pdfkit.configuration(wkhtmltopdf=r'D:\wkhtmltopdf\bin\wkhtmltopdf.exe')
        options = {'enable-local-file-access': None}
        table = self.generate_table()
        pdf_template = pdf_template.replace("$table;", table)
        pdfkit.from_string(pdf_template, 'report.pdf', configuration=config, options=options)

    def generate_table(self):
        table = "<table class='table'><tr><th>Год</th><th>Средняя зарплата</th><th>Средняя зарплата - "
        table += profession + "</th><th>Количество вакансий</th><th>Количество вакансий - " + profession + "</th></tr>"
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

class DataSet:
    def __init__(self):
        self.report = Report()
        self.file_name = file
        self.vacancies_objects = []

    def сsv_reader(self, file_name):
        global names
        with open(file_name, encoding="utf-8-sig") as File:
            readerFile = csv.reader(File, delimiter=',',
                                quoting=csv.QUOTE_MINIMAL)
            for row in readerFile:
                if (len(names) == 0):
                    names = row
                elif (len(row) >= len(names) and not ("" in row)):
                    resultList.append(row)
        return resultList, names

    def csv_filer(self, reader, list_naming):
        for item in reader:
            argument = ["", "", "", "", "", "", "", "", ""]
            namesIndex = ["name", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "area_name", "published_at"]
            argSalary = ["", "", "", ""]
            nameSsalary = ["salary_from", "salary_to", "salary_gross", "salary_currency"]
            for i in range(len(names)):
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
            vacancy = Vacancy(*argument)
            self.vacancies_objects.append(vacancy)
        return self.vacancies_objects

    def clearStr(strValue):
        return ' '.join(re.sub(r"<[^>]+>", '', strValue).split())

    def makeDict(self):
        dicrionaries = {
            "salaryYear": {},
            "NumberYear": {},
            "salaryProfessionalYear": {},
            "NumberProfessionalYear": {},
            "salaryCity": {},
            "vacancyCity": {}
        }
        for vacancy in self.vacancies_objects:
            if (int(vacancy.published_at[0][0:4]) in dicrionaries["NumberYear"].keys()):
                dicrionaries["NumberYear"][int(vacancy.published_at[0][0:4])] += 1
            else:
                dicrionaries["NumberYear"][int(vacancy.published_at[0][0:4])] = 1
                dicrionaries["NumberProfessionalYear"][int(vacancy.published_at[0][0:4])] = 0

            if (int(vacancy.published_at[0][0:4]) in dicrionaries["salaryYear"].keys()):
                dicrionaries["salaryYear"][int(vacancy.published_at[0][0:4])] += [currency_to_rub[vacancy.salary.salary_currency[0]] * (float(vacancy.salary.salary_from[0]) + float(vacancy.salary.salary_to[0])) / 2]
            else:
                dicrionaries["salaryYear"][int(vacancy.published_at[0][0:4])] = [currency_to_rub[vacancy.salary.salary_currency[0]] * (float(vacancy.salary.salary_from[0]) + float(vacancy.salary.salary_to[0])) / 2]
                dicrionaries["salaryProfessionalYear"][int(vacancy.published_at[0][0:4])] = [0]

            if (vacancy.area_name[0] in dicrionaries["salaryCity"].keys()):
                dicrionaries["salaryCity"][vacancy.area_name[0]] += [currency_to_rub[vacancy.salary.salary_currency[0]] * (float(vacancy.salary.salary_from[0]) + float(vacancy.salary.salary_to[0])) / 2]
            else:
                dicrionaries["salaryCity"][vacancy.area_name[0]] = [currency_to_rub[vacancy.salary.salary_currency[0]] * (float(vacancy.salary.salary_from[0]) + float(vacancy.salary.salary_to[0])) / 2]

            if (vacancy.area_name[0] in dicrionaries["vacancyCity"].keys()):
                dicrionaries["vacancyCity"][vacancy.area_name[0]] += 1
            else:
                dicrionaries["vacancyCity"][vacancy.area_name[0]] = 1

            if(profession in vacancy.name[0]):
                if (int(vacancy.published_at[0][0:4]) in dicrionaries["NumberProfessionalYear"].keys()):
                    dicrionaries["NumberProfessionalYear"][int(vacancy.published_at[0][0:4])] += 1
                else:
                    dicrionaries["NumberProfessionalYear"][int(vacancy.published_at[0][0:4])] = 1

                if (int(vacancy.published_at[0][0:4]) in dicrionaries["salaryProfessionalYear"].keys()):
                    dicrionaries["salaryProfessionalYear"][int(vacancy.published_at[0][0:4])] += [currency_to_rub[vacancy.salary.salary_currency[0]] * (float(vacancy.salary.salary_from[0]) + float(vacancy.salary.salary_to[0])) / 2]
                else:
                    dicrionaries["salaryProfessionalYear"][int(vacancy.published_at[0][0:4])] = [currency_to_rub[vacancy.salary.salary_currency[0]] * (float(vacancy.salary.salary_from[0]) + float(vacancy.salary.salary_to[0])) / 2]

        elem = {}
        for item in dicrionaries["salaryYear"].items():
           elem[item[0]] = int(sum(dicrionaries["salaryYear"][item[0]]) / len(dicrionaries["salaryYear"][item[0]]))
        self.report.salaryYear = elem
        print("Динамика уровня зарплат по годам:", elem)

        self.report.numberYear = dicrionaries["NumberYear"]
        print("Динамика количества вакансий по годам:", dicrionaries["NumberYear"])


        elem = {}
        for item in dicrionaries["salaryProfessionalYear"].items():
            if(len(dicrionaries["salaryProfessionalYear"][item[0]]) > 1):
                elem[item[0]] = int(sum(dicrionaries["salaryProfessionalYear"][item[0]]) / (len(dicrionaries["salaryProfessionalYear"][item[0]]) - 1))
            else: elem[item[0]] = 0
        self.report.salaryProfessionalYear = elem
        print("Динамика уровня зарплат по годам для выбранной профессии:", elem)

        self.report.numberProfessionalYear = dicrionaries["NumberProfessionalYear"]
        print("Динамика количества вакансий по годам для выбранной профессии:", dicrionaries["NumberProfessionalYear"])

        elem = {}
        for item in dicrionaries["salaryCity"].items():
            if(len(dicrionaries["salaryCity"][item[0]]) / sum(dicrionaries["NumberYear"].values()) >= 0.01):
                elem[item[0]] = int(sum(dicrionaries["salaryCity"][item[0]]) / len(dicrionaries["salaryCity"][item[0]]))
        elem = dict(sorted(elem.items(), key=lambda item: item[1], reverse=True)[:10])
        self.report.salaryCity = elem
        print("Уровень зарплат по городам (в порядке убывания):", elem)

        elem = {}
        for item in dicrionaries["vacancyCity"].items():
            if(dicrionaries["vacancyCity"][item[0]] / sum(dicrionaries["NumberYear"].values()) >= 0.01):
                elem[item[0]] = round(dicrionaries["vacancyCity"][item[0]] / sum(dicrionaries["NumberYear"].values()), 4)
        elem = dict(sorted(elem.items(), key=lambda item: item[1], reverse=True)[:10])
        self.report.vacancyCity = elem
        print("Доля вакансий по городам (в порядке убывания):", elem)

    def printVacancy(self):
        resultList, names = self.сsv_reader(file)
        if len(names) == 0 or len(resultList) == 0:
            print("Нет данных")
        else:
            self.csv_filer(resultList, names)
            self.makeDict()
            self.report.generate_image()
            self.report.generate_excel()
            self.report.generate_pdf()

class InputConnect:
    def __init__(self):
        self.data = DataSet()

    def filter_parametr(self, row):
        count = 0
        if(filtration[0] == "Идентификатор валюты оклада"):
            if (str(row.salary.salary).split("(")[1].split(")")[0] == filtration[1]):
                return row
        elif(filtration[0] == "Оклад"):
            if (int(float(row.salary.salary_from)) <= int(filtration[1]) <= int(float(row.salary.salary_to))):
                return row
        elif (filtration[0] == "Дата публикации вакансии"):
            if(row.published_at.split("T")[0].split("-")[2] + "." + row.published_at.split("T")[0].split("-")[1] + "." + row.published_at.split("T")[0].split("-")[0] == filtration[1]):
                return row

        elif(filtration[0] == "Навыки"):
            skills = filtration[1].split(", ")
            for item in skills:
                if (item in row.key_skills):
                    count += 1
            if(count == len(skills)):
                return row
        elif(filtration[0] == ""):
            return row
        elif (getattr(row,filterToNames[filtration[0]]) == filtration[1]):
            return row
        return {}


    def print_vacancies(self, data_vacancies, dic_naming):
        counter = 0
        mytable = PrettyTable()
        mytable._max_width = {"Название": 20, "Описание": 20, "Навыки": 20, "Опыт работы": 20, "Премиум-вакансия": 20,
                        "Компания": 20, "Оклад": 20, "Название региона": 20, "Дата публикации вакансии": 20}

        mytable.field_names = ["№"] + list(dic_naming.values())
        mytable.hrules = 1
        mytable.align = "l"

        if (sortirovka == "Оклад"):
            data_vacancies = sorted(data_vacancies, key = lambda x: currency_to_rub[x.salary.salary_currency] * (float(x.salary.salary_from) + float(x.salary.salary_to)), reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Дата публикации вакансии"):
            data_vacancies = sorted(data_vacancies, key=lambda x:  x.published_at, reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Навыки"):
            data_vacancies = sorted(data_vacancies, key=lambda x: len(x.key_skills) if type(x.key_skills) == list else 1, reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Опыт работы"):
            data_vacancies = sorted(data_vacancies, key=lambda x: x.experience_id[3], reverse=(True if (sortOrder == "Да") else False))
        elif(sortirovka == "Премиум-вакансия"):
            data_vacancies = sorted(data_vacancies, key=lambda x: "Да" if x.premium.upper() == "TRUE" else "Нет", reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Название"):
            data_vacancies = sorted(data_vacancies, key=lambda x: x.name, reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Описание"):
            data_vacancies = sorted(data_vacancies, key=lambda x: x.description, reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka == "Компания"):
            data_vacancies = sorted(data_vacancies, key=lambda x: x.employer_name, reverse=(True if (sortOrder == "Да") else False))
        elif (sortirovka != ""):
            data_vacancies = sorted(data_vacancies, key=lambda x: x.area_name, reverse=(True if (sortOrder == "Да") else False))

        for vacancy in data_vacancies:
            counter += 1
            vacancy = self.filter_parametr(vacancy)
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
            if(len(val) > 1):
                mytable.add_row(val)
            else: counter -= 1
        if(counter == 0):
            print("Ничего не найдено")
        else:
            print(mytable.get_string(fields = (["№"] + (column if len(column) > 1 else list(dic_naming.values()))), start = (int(lines[0]) - 1 if len(lines) > 0 else 0), end = (int(lines[1]) - 1 if len(lines) > 1 else counter)))


    def PrintFunction(self):
        if(os.stat(file).st_size == 0):
            print("Пустой файл")
        elif (len(filtration) == 1 and len(filtration[0]) > 0):
            print("Формат ввода некорректен")
        elif ((filtration[0] not in (list(filterToNames.keys()) + ["Идентификатор валюты оклада"])) and filtration[0] != ""):
            print("Параметр поиска некорректен")
        elif (sortirovka not in translateToRus.values() and sortirovka != ""):
            print("Параметр сортировки некорректен")
        elif (sortOrder not in ["Да","Нет",""]):
            print("Порядок сортировки задан некорректно")
        else:
            resultList, names = self.data.сsv_reader(file)
            if len(names) == 0 or len(resultList) == 0:
                print("Нет данных")
            else:
                self.print_vacancies(self.data.csv_filer(resultList, names), translateToRus)


conclusion = DataSet()
connect = InputConnect()
if(start == "Статистика"):
    profession = input("Введите профессии: ")
    conclusion.printVacancy()
elif(start == "Вакансии"):
    filtration = input("Введите параметр фильтрации: ").split(": ")
    sortirovka = input("Введите параметр сортировки: ")
    sortOrder = input("Обратный порядок сортировки (Да / Нет): ")
    lines = input("Введите диапазон вывода: ").split()
    column = input("Введите требуемые столбцы: ").split(", ")
    connect.PrintFunction()
