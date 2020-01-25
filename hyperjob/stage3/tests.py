# -*- coding: utf-8 -*-
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


class HyperJobItemsPageTest(DjangoTest, ModelsTestMixin):
    def check_vacancies(self) -> CheckResult:
        try:
            page = self.read_page(f'http://localhost:{self.port}/vacancies')
            for person, vacancy in zip(INITIAL_USERS, INITIAL_VACANCIES):
                description = f'{person[1]}: {vacancy[1]}'
                if description not in page:
                    return CheckResult.false(
                        f'Vacancies page should contain vacancies in form <username>: <description>'
                    )
            return CheckResult.true()
        except urllib.error.URLError:
            return CheckResult.false(
                'Cannot connect to the vacancies page.'
            )

    def check_resumes(self) -> CheckResult:
        try:
            page = self.read_page(f'http://localhost:{self.port}/resumes')
            for person, resume in zip(INITIAL_USERS[len(INITIAL_VACANCIES):], INITIAL_RESUMES):
                description = f'{person[1]}: {resume[1]}'
                if description not in page:
                    return CheckResult.false(
                        f'Resumes page should contain resumes in form <username>: <description>'
                    )
            return CheckResult.true()
        except urllib.error.URLError:
            return CheckResult.false(
                'Cannot connect to the resumes page.'
            )

    def generate(self):
        return [
            TestCase(attach=self.check_server),
            TestCase(attach=self.check_create_vacancies),
            TestCase(attach=self.check_create_resumes),
            TestCase(attach=self.check_vacancies),
            TestCase(attach=self.check_resumes),
        ]

    def check(self, reply, attach):
        return attach()


if __name__ == '__main__':
    HyperJobItemsPageTest('hyperjob.manage').run_tests()
