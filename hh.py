import requests
import json
import pandas as pd

def make_hhru_file():
    """
    Создает CSV файл с IT вакансиями за 22.12.2022
    """

    name =[]
    salary_from = []
    salary_to = []
    salary_currency = []
    area_name = []
    published_at =[]
    x = ''
    for page in range(0,21):
        for hour in range (0,24):
            x = requests.get(f'https://api.hh.ru/vacancies/', params={"specialization":1, "per_page":100, 'page': page,  'date_from':f"2022-12-22T{str(hour).zfill(2)}:00:00",'date_to':f"2022-12-22T{str(hour).zfill(2)}:59:59"})
            if 'items' in json.loads(x.text) and len(json.loads(x.text)['items']) != 0:
                for item in json.loads(x.text)['items']:
                    try:
                        name.append(item["name"])
                    except: 
                        name.append('')
                    try:
                        salary_from.append(item["salary"]["from"])
                    except: 
                        salary_from.append('')
                    try:
                        salary_to.append(item["salary"]["to"])
                    except: 
                        salary_to.append('')
                    try:
                        salary_currency.append(item["salary"]["currency"])
                    except: 
                        salary_currency.append('')
                    try:
                        area_name.append(item["address"]["city"])
                    except: 
                        area_name.append('')
                    try:
                        published_at.append(item["published_at"])
                    except: 
                        published_at.append('')

    d = {'name': name, 'salary_from': salary_from, 'salary_to': salary_to, 'salary_currency': salary_currency,
            'area_name': area_name, 'published_at': published_at}
    df = pd.DataFrame(data=d)
    df.to_csv('hhru.csv', index=False)

make_hhru_file()