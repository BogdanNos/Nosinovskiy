from unittest import TestCase
from main1 import Salary, Vacancy, Report, DataSet, InputConnect

class SalaryTest(TestCase):
    def test_salary_type(self):
        self.assertEqual(type(Salary(100, 200 ,"True", "RUR")).__name__, 'Salary')
    def test_salary_get_correct_salary_from(self):
        self.assertEqual(Salary(100, 200,"True", "RUR").salary_from, [100])
    def test_salary_get_correct_salary_to(self):
        self.assertEqual(Salary(100, 200,"True", "RUR").salary_to, [200])
    def test_salary_get_correct_all_salary_information(self):
        self.assertEqual(Salary(100, 200,"True", "RUR").salary, '100 - 200 (Рубли) (С вычетом налогов)')

class VacancyTest(TestCase):
    def test_vacancy_type(self):
        self.assertEqual(type(Vacancy("name", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "Москва", "published_at")).__name__, 'Vacancy')
    def test_vacancy_get_correct_area_name(self):
        self.assertEqual(Vacancy("name", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "Москва", "published_at").area_name, ['Москва'])
    def test_vacancy_get_correct_name(self):
        self.assertEqual(Vacancy("Яндекс", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "Москва", "published_at").name, ['Яндекс'])
    def test_vacancy_get_correct_published_at(self):
        self.assertEqual(Vacancy("name", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "Москва", "2007-12-03T17:34:36+0300").published_at, ['2007-12-03T17:34:36+0300'])

class GenerateTableTest(TestCase):
    def test_generate_correct_table(self):
        self.assertEqual(Report().generate_table("Программист"), "<table class='table'><tr><th>Год</th><th>Средняя зарплата</th><th>Средняя зарплата - Программист</th><th>Количество вакансий</th><th>Количество вакансий - Программист</th></tr></tr></table><h1>Статистика по городам</h1><table class='table1'><tr><th>Город</th><th>Уровень зарплат</th></tr></table><table class='table2'><tr><th>Город</th><th>Уровень зарплат</th></tr></table>")

class ClearStringFromHTMLTagsTest(TestCase):
    def test_clear_from_single_tegs(self):
        self.assertEqual(DataSet.clearStr("<p>man</p>"), 'man')
    def test_clear_from_many_tegs(self):
        self.assertEqual(DataSet.clearStr("<body><p>word</p></body>"), 'word')

class CorrectFiltrationTest(TestCase):
    def test_check_uncorrect_filtr(self):
        filtration = ["Название", "Программист"]
        self.assertEqual(InputConnect().filter_parametr(Vacancy("Аналитик", "description", "key_skills", "experience_id", "premium", "employer_name", "salary", "Москва", "2007-12-03T17:34:36+0300"), filtration), {})
