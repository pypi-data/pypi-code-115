import requests
from bs4 import BeautifulSoup as bs
import unicodedata

__author__ = "Gregory"
__github__ = "https://github.com/Gregory-coder/litAPI"
__version__ = "0.0"
__status__ = "Beta test"

class ArgumentsError(Exception):
    def __init__(self, text):
        self.txt = text


class Ulysses:
    def __init__(self, code):
        self.s = requests.Session()
        self.code = code
        # get csrf
        auth_html = self.s.get("https://in.lit.msu.ru/Ulysses/login/?next=/Ulysses")
        auth_bs = bs(auth_html.content, "html.parser")
        scrf = auth_bs.select("input[name=csrfmiddlewaretoken]")[0]['value']

        payload = {
            "csrfmiddlewaretoken": scrf,
            "password": self.code
        }

        self.answ = self.s.post("https://in.lit.msu.ru/Ulysses/login/keyword/?next=/Ulysses", data=payload)
        answ_bs = bs(self.answ.content, "html.parser")
        wrong_data = answ_bs.find_all("div", "alert alert-danger alert-dismissable alert-link")
        if len(wrong_data):
            raise ArgumentsError("Wrong password")

    def years(self):
        answ_bs = bs(self.answ.content, "html.parser")
        years_tags = answ_bs.find_all('li')[8:-1]
        years = []
        for elem in years_tags:
            year_ = elem.text.strip()
            year_ = unicodedata.normalize("NFKD", year_)  # Избавляюсь от символов \xa0/\xa0
            year_ = year_.replace(' / ', '-')  # Привожу год в вид как внутри ссыл
            years.append(year_)

        return years

    def get_homework(self, year=None, class_=None, subject_id=None, teacher_id=None, homework_id=None, link=None):
        if year is None:
            year = self.years()[0]
        elif not isinstance(year, str):
            raise ArgumentsError(f"argument year must be str, but {type(year)} is given")
        if link is None:
            if None in (subject_id, teacher_id, homework_id, class_):
                raise ArgumentsError("function get_homework() takes arguments \
subject_id, teacher_id, homework_id, year, class_ or argument link")
            link = f"http://in.lit.msu.ru/Ulysses/{year}/{class_}/{subject_id}/{teacher_id}/{homework_id}"
        task_html = self.s.get(link)
        task_bs = bs(task_html.content, "html.parser")
        if task_bs.text == 'Учебный материал не найден':
            raise ArgumentsError("task not found")
        task_content = task_bs.find_all('div', class_="course-content-item-body")
        upload_data = task_content[0].find_all('p')[0].text
        text = task_content[0].find_all('p')[-1].text
        upload_time = upload_data[len('публикации:') + upload_data.find('публикации') + 1:].strip().split()

        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября',
                  'ноября', 'декабря']
        date = {
            'month': months.index(upload_time[1]) + 1,
            'day': int(upload_time[0]),
            'year': int(upload_time[2]),
            'hour': int(upload_time[4][:upload_time[4].find(":")]),
            'minute': int(upload_time[4][upload_time[4].find(":") + 1:])}
        res = {'text': text, 'date': date, 'info': {
            'class_': class_,
            'subject_id': subject_id,
            'teacher_id': teacher_id,
            'homework_id': homework_id,
            'link': link
        }}

        return res

    def get_courses(self, year=None):
        if year is None:
            year = self.years()[0]
        year_html = self.s.get("https://in.lit.msu.ru/Ulysses/"+year)
        year_bs = bs(year_html.content, "html.parser")
        if year_bs.text == 'Учебные материалы за этот учебный не найдены':
            raise ArgumentsError("courses not found")
        courses_tags = year_bs.find_all('li')
        courses = []
        for elem in courses_tags[10:-1]:
            course = elem.text.strip()
            link = "https://in.lit.msu.ru/Ulysses/" + year + '/' + elem.find('a').get('href')
            st1 = course.find("(")
            teacher = course[st1 + 1:-1]
            st2 = teacher.find("(")
            if st2 != -1:
                subject = course[:st2 + st1]
                teacher = teacher[st2 + 1:]
            else:
                subject = course[:st1]
            courses.append({'subject': subject, 'teacher': teacher, 'link': link})
        # Всатвить алгоритм обработки списка курсов
        return courses

    def get_subject(self, year=None, class_=None, subject_id=None, teacher_id=None, link=None):
        if year is None:
            year = self.years()[0]
        elif not isinstance(year, str):
            raise ArgumentsError(f"argument year must be str, but {type(year)} is given")
        if link is None:
            if None in (subject_id, teacher_id, class_):
                raise ArgumentsError("function get_subject() takes arguments \
subject_id, teacher_id, year, class_ or argument link")
            link = f"http://in.lit.msu.ru/Ulysses/{year}/{class_}/{subject_id}/{teacher_id}"
        subject_html = self.s.get(link)
        subject_bs = bs(subject_html.content, "html.parser")
        tasks = {}
        pages = subject_bs.find_all('li', class_="last")[-1].find('a').get("href")
        for i in range(1,int(pages[-1])+1):
            page_html = self.s.get(link+pages[:-1]+str(i))
            page_bs = bs(page_html.content, "html.parser")
            page = page_bs.find_all('h2', class_="course-content-item-name")
            for elem in page:
                tasks[elem.text] = link + elem.find('a').get("href")

        return tasks

    def get_timetable(self, class_=None):
        # def get_table():
        tt_html = self.s.get("https://www.lit.msu.ru/study/timetable/5")
        tt_bs = bs(tt_html.content, "html.parser")
        table_bs = tt_bs.find_all("tbody")
        print(len(table_bs))
        for elem in table_bs:
            pass
            # print(elem)
        # if class_ is None:
        #     for i in range(5,12):
        #         get_table()
