# -*- coding: utf-8 -*-
import re
import urllib
import sqlite3

from hstest.django_test import DjangoTest, TEST_DATABASE
from hstest.check_result import CheckResult
from hstest.test_case import TestCase

INITIAL_USERS = [
    (1, 'Lemon_2059', 'contemp2015@protonmail.com', True),
    (2, 'RuthlessnessSirens-1882', 'oversured1842@yahoo.com', True),
    (3, 'moping_1935', 'tenons1970@outlook.com', True),
    (4, 'MillagePenstemon-1843', 'chrisman1923@yandex.com', True),
    (5, 'Archeus.1930', 'concentric1895@gmail.com', True),
    (6, 'BenzalazineCurite.1832', 'quassiin1927@live.com', True),
    (7, 'Bossa-1831', 'breena1977@live.com', False),
    (8, 'ClinkChinho_2027', 'adansonia1808@gmail.com', False),
    (9, 'RepassableTournefortian.1973', 'vomer1822@yahoo.com', False),
    (10, 'debenture-1898', 'average2014@yahoo.com', False),
]

INITIAL_VACANCIES = [
    (1, 'Botanist'),
    (2, 'Signwriter'),
    (3, 'Stewardess'),
    (4, 'Medical Secretary'),
    (5, 'Stone Cutter'),
    (6, 'Musician'),
]

INITIAL_RESUMES = [
    (7, 'Charge Hand'),
    (8, 'Occupations'),
    (9, 'Milklady'),
    (10, 'Auctioneer'),
]


class ModelsTestMixin(object):
    def check_create_vacancies(self) -> CheckResult:
        connection = sqlite3.connect(TEST_DATABASE)
        cursor = connection.cursor()
        try:
            cursor.executemany(
                'INSERT INTO auth_user '
                '(`id`, `username`, `email`, `is_staff`, `password`, `is_superuser`, '
                '`first_name`, `last_name`, `is_active`, `date_joined`) '
                'VALUES (?, ?, ?, ?, "", false, "", "", true, datetime())',
                INITIAL_USERS[:len(INITIAL_VACANCIES)]
            )
            cursor.executemany(
                'INSERT INTO vacancy_vacancy (`author_id`, `description`) VALUES (?, ?)',
                INITIAL_VACANCIES
            )
            connection.commit()

            cursor.execute('SELECT `author_id`, `description` FROM vacancy_vacancy')
            result = cursor.fetchall()

            for item in INITIAL_VACANCIES:
                if item not in result:
                    return CheckResult.false('Check your Vacancy model')
            return CheckResult.true()

        except sqlite3.DatabaseError as err:
            return CheckResult.false(str(err))

    def check_create_resumes(self) -> CheckResult:
        connection = sqlite3.connect(TEST_DATABASE)
        cursor = connection.cursor()
        try:
            cursor.executemany(
                'INSERT INTO auth_user '
                '(`id`, `username`, `email`, `is_staff`, `password`, `is_superuser`, '
                '`first_name`, `last_name`, `is_active`, `date_joined`) '
                'VALUES (?, ?, ?, ?, "", false, "", "", true, datetime())',
                INITIAL_USERS[len(INITIAL_VACANCIES):]
            )
            cursor.executemany(
                'INSERT INTO resume_resume (`author_id`, `description`) VALUES (?, ?)',
                INITIAL_RESUMES
            )
            connection.commit()

            cursor.execute('SELECT `author_id`, `description` FROM resume_resume')
            result = cursor.fetchall()

            for item in INITIAL_RESUMES:
                if item not in result:
                    return CheckResult.false('Check your Resume model')
            return CheckResult.true()

        except sqlite3.DatabaseError as err:
            return CheckResult.false(str(err))


class HyperJobMenuTest(DjangoTest, ModelsTestMixin):
    ELEMENT_PATTERN = '''<a[^>]+href=['"](?P<href>[a-zA-Z/_]+)['"][^>]*>'''

    def check_greeting(self) -> CheckResult:
        try:
            main_page = self.read_page(f'http://localhost:{self.port}')
            if 'Welcome to Hyperjob!' in main_page:
                return CheckResult.true()
            return CheckResult.false(
                'Main page should contain "Welcome to Hyperjob!" line'
            )
        except urllib.error.URLError:
            return CheckResult.false(
                'Cannot connect to the menu page.'
            )

    def check_links(self) -> CheckResult:
        try:
            page = self.read_page(f'http://localhost:{self.port}')
            links = re.findall(self.ELEMENT_PATTERN, page)
            for link in (
                '/login',
                '/signup',
                '/vacancies',
                '/resumes',
                '/home',
            ):
                if link not in links:
                    return CheckResult.false(
                        f'Menu page should contain <a> element with href {link}'
                    )
            return CheckResult.true()
        except urllib.error.URLError:
            return CheckResult.false(
                'Cannot connect to the menu page.'
            )

    def generate(self):
        return [
            TestCase(attach=self.check_server),
            TestCase(attach=self.check_create_vacancies),
            TestCase(attach=self.check_create_resumes),
            TestCase(attach=self.check_greeting),
            TestCase(attach=self.check_links),
        ]

    def check(self, reply, attach):
        return attach()


if __name__ == '__main__':
    HyperJobMenuTest('hyperjob.manage').run_tests()
