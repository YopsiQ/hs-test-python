import os
import re
import signal
import subprocess
import sys
from functools import partial
from time import sleep
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen, build_opener
from hstest.stage_test import StageTest
from hstest.check_result import CheckResult
from hstest.test_case import TestCase


class DjangoTest(StageTest):

    _kill = os.kill
    port = '0'
    tryout_ports = ['8000', '8001', '8002', '8003', '8004']
    process = None

    def run(self):
        if self.process is None:
            self.__find_free_port()
            self.process = subprocess.Popen([
                sys.executable, self.file_to_test,
                'runserver', self.port, '--noreload',
            ])

    def check_server(self):
        if self.port == '0':
            return CheckResult.false(
                f'Please free one of the ports: {", ".join(self.tryout_ports)}'
            )

        for _ in range(15):
            try:
                urlopen(f'http://localhost:{self.port}/not-existing-link-by-default')
                return CheckResult.true()
            except URLError as err:
                if isinstance(err, HTTPError):
                    return CheckResult.true()
                sleep(1)
        else:
            return CheckResult.false(
                'Cannot start the ./manage.py runserver for 15 seconds'
            )

    def __find_free_port(self):
        for port in self.tryout_ports:
            try:
                urlopen(f'http://localhost:{port}')
            except URLError as err:
                if isinstance(err.reason, ConnectionRefusedError):
                    self.port = port
                    break

    def read_page(self, link: str) -> str:
        return urlopen(link).read().decode().replace('\xc2\xa0', ' ')

    def after_all_tests(self):
        if self.process is not None:
            try:
                self._kill(self.process.pid, signal.SIGINT)
            except ProcessLookupError:
                pass


class HypercarWelcomeToServiceTest(DjangoTest):

    def get_welcome_page(self) -> CheckResult:
        try:
            main_page = self.read_page(f'http://localhost:{self.port}/welcome')
            if 'Welcome to the Hypercar Service!' in main_page:
                return CheckResult.true()
            return CheckResult.false(
                'Main page should contain "Welcome to the Hypercar Service!" line'
            )
        except URLError:
            return CheckResult.false(
                'Cannot connect to the /welcome page.'
            )

    def generate(self):
        return [
            TestCase(attach=self.check_server),
            TestCase(attach=self.get_welcome_page),
        ]

    def check(self, reply, attach):
        return attach()


class HypercarClientMenuTest(DjangoTest):
    ELEMENT_PATTERN = '''<a[^>]+href=['"](?P<href>[a-zA-Z/_]+)['"][^>]*>'''

    def get_client_menu_page(self) -> CheckResult:
        try:
            page = self.read_page(f'http://localhost:{self.port}/menu')
            links = re.findall(self.ELEMENT_PATTERN, page)
            for link in (
                '/get_ticket/change_oil',
                '/get_ticket/inflate_tires',
                '/get_ticket/diagnostic',
            ):
                if link not in links:
                    return CheckResult.false(
                        f'Menu page should contain <a> element with href {link}'
                    )
            return CheckResult.true()
        except URLError:
            return CheckResult.false(
                'Cannot connect to the /menu page.'
            )

    def generate(self):
        return [
            TestCase(attach=self.check_server),
            TestCase(attach=self.get_client_menu_page),
        ]

    def check(self, reply, attach):
        return attach()


class HypercarElecronicQueueTest(DjangoTest):

    def get_ticket(self, service: str, content: str, helper_msg: str) -> CheckResult:
        try:
            page = self.read_page(f'http://localhost:{self.port}/get_ticket/{service}')
            if content in page:
                return CheckResult.true()
            else:
                return CheckResult.false(
                    f'Expected to have {content} on /get_ticket/{service} page after\n'
                    f'{helper_msg}'
                )
        except URLError:
            return CheckResult.false(
                f'Cannot connect to the /get_ticket/{service} page.'
            )

    def generate(self):
        helper_msg_1 = '\tClient #1 get ticket for inflating tires\n'
        helper_msg_2 = helper_msg_1 + '\tClient #2 get ticket for changing oil\n'
        helper_msg_3 = helper_msg_2 + '\tClient #3 get ticket for changing oil\n'
        helper_msg_4 = helper_msg_3 + '\tClient #4 get ticket for inflating tires\n'
        helper_msg_5 = helper_msg_4 + '\tClient #5 get ticket for diagnostic\n'
        return [
            TestCase(attach=self.check_server),
            TestCase(attach=partial(
                self.get_ticket,
                'inflate_tires',
                'Please wait around 0 minutes',
                helper_msg_1
            )),
            TestCase(attach=partial(
                self.get_ticket,
                'change_oil',
                'Please wait around 0 minutes',
                helper_msg_2
            )),
            TestCase(attach=partial(
                self.get_ticket,
                'change_oil',
                'Please wait around 2 minutes',
                helper_msg_3
            )),
            TestCase(attach=partial(
                self.get_ticket,
                'inflate_tires',
                'Please wait around 9 minutes',
                helper_msg_4
            )),
            TestCase(attach=partial(
                self.get_ticket,
                'diagnostic',
                'Please wait around 14 minutes',
                helper_msg_5
            )),
        ]

    def check(self, reply, attach):
        return attach()


class HypercarOperatorMenuTest(DjangoTest):

    def get_ticket(self, service: str, content: str, helper_msg: str) -> CheckResult:
        try:
            page = self.read_page(f'http://localhost:{self.port}/get_ticket/{service}')
            if content in page:
                return CheckResult.true()
            else:
                return CheckResult.false(
                    f'Expected to have {content} on /get_ticket/{service} page after\n'
                    f'{helper_msg}'
                )
        except URLError:
            return CheckResult.false(
                f'Cannot connect to the /get_ticket/{service} page.'
            )

    def check_menu(self, service: str, content: str, menu_content: str,
                   helper_msg: str) -> CheckResult:
        try:
            result = self.get_ticket(service, content, helper_msg)
            if not result.result:
                return result

            page = self.read_page(f'http://localhost:{self.port}/processing')
            if menu_content in page:
                return CheckResult.true()
            else:
                return CheckResult.false(
                    f'Expected to have {menu_content} on /processing page after\n'
                    f'{helper_msg}'
                )
        except URLError:
            return CheckResult.false(
                f'Cannot connect to the /processing page.'
            )

    def generate(self):
        helper_msg_1 = '\tClient #1 get ticket for inflating tires\n'
        helper_msg_2 = helper_msg_1 + '\tClient #2 get ticket for changing oil\n'
        helper_msg_3 = helper_msg_2 + '\tClient #3 get ticket for changing oil\n'
        helper_msg_4 = helper_msg_3 + '\tClient #4 get ticket for inflating tires\n'
        helper_msg_5 = helper_msg_4 + '\tClient #5 get ticket for diagnostic\n'
        return [
            TestCase(attach=self.check_server),
            TestCase(attach=partial(
                self.check_menu,
                'inflate_tires',
                'Please wait around 0 minutes',
                'Inflate tires queue: 1',
                helper_msg_1
            )),
            TestCase(attach=partial(
                self.check_menu,
                'change_oil',
                'Please wait around 0 minutes',
                'Change oil queue: 1',
                helper_msg_2
            )),
            TestCase(attach=partial(
                self.check_menu,
                'change_oil',
                'Please wait around 2 minutes',
                'Change oil queue: 2',
                helper_msg_3
            )),
            TestCase(attach=partial(
                self.check_menu,
                'inflate_tires',
                'Please wait around 9 minutes',
                'Inflate tires queue: 2',
                helper_msg_4
            )),
            TestCase(attach=partial(
                self.check_menu,
                'diagnostic',
                'Please wait around 14 minutes',
                'Get diagnostic queue: 1',
                helper_msg_5
            )),
        ]

    def check(self, reply, attach):
        return attach()


class HypercarServeNextTest(DjangoTest):

    def get_ticket(self, service: str, content: str, helper_msg: str) -> CheckResult:
        try:
            page = self.read_page(f'http://localhost:{self.port}/get_ticket/{service}')
            if content in page:
                return CheckResult.true()
            else:
                return CheckResult.false(
                    f'Expected to have {content} on /get_ticket/{service} page after\n'
                    f'{helper_msg}'
                )
        except URLError:
            return CheckResult.false(
                f'Cannot connect to the /get_ticket/{service} page.'
            )

    def check_menu(self, service: str, content: str, menu_content: str,
                   helper_msg: str) -> CheckResult:
        try:
            result = self.get_ticket(service, content, helper_msg)
            if not result.result:
                return result

            page = self.read_page(f'http://localhost:{self.port}/processing')
            if menu_content in page:
                return CheckResult.true()
            else:
                return CheckResult.false(
                    f'Expected to have {menu_content} on /processing page after\n'
                    f'{helper_msg}'
                )
        except URLError:
            return CheckResult.false(
                f'Cannot connect to the /processing page.'
            )

    def check_next(self, service: str, content: str, menu_content: str,
                   next_content: str, make_process: bool, helper_msg: str) -> CheckResult:
        try:
            result = self.check_menu(service, content, menu_content, helper_msg)
            if not result.result:
                return result

            if make_process:
                result = self.process_ticket()
                if not result.result:
                    return result

            page = self.read_page(f'http://localhost:{self.port}/next')

            if next_content in page:
                return CheckResult.true()
            else:
                return CheckResult.false(
                    f'Expected to have {next_content} on /next page after\n'
                    f'{helper_msg}'
                )
        except URLError:
            return CheckResult.false(
                f'Cannot connect to the /next page.'
            )

    def process_ticket(self):
        response = urlopen(f'http://localhost:{self.port}/processing')
        csrf_options = re.findall(
            b'<input[^>]+value="(?P<csrf>\w+)"[^>]*>', response.read()
        )
        if not csrf_options:
            return CheckResult.false(
                'Add csrf_token to your form'
            )
        set_cookie = response.headers.get('Set-Cookie')
        opener = build_opener()
        opener.addheaders.append(('Cookie', set_cookie))
        try:
            opener.open(
                f'http://localhost:{self.port}/processing',
                data=urlencode({'csrfmiddlewaretoken': csrf_options[0]}).encode()
            )
        except HTTPError:
            return CheckResult.false(
                'Cannot send POST request to /processsing page'
            )
        return CheckResult.true()

    def generate(self):
        helper_msg_1 = '\tClient #1 get ticket for inflating tires\n'
        helper_msg_2 = helper_msg_1 + '\tClient #2 get ticket for changing oil\n'
        helper_msg_3 = helper_msg_2 + '\tClient #3 get ticket for changing oil\n'
        helper_msg_3 += '\tOperator processed client\n'
        helper_msg_4 = helper_msg_3 + '\tClient #4 get ticket for inflating tires\n'
        helper_msg_4 += '\tOperator processed client\n'
        helper_msg_5 = helper_msg_4 + '\tClient #5 get ticket for diagnostic\n'
        helper_msg_5 += '\tOperator processed client\n'
        return [
            TestCase(attach=self.check_server),
            TestCase(attach=partial(
                self.check_next,
                'inflate_tires',
                'Please wait around 0 minutes',
                'Inflate tires queue: 1',
                'Waiting for the next client',
                False,
                helper_msg_1
            )),
            TestCase(attach=partial(
                self.check_next,
                'change_oil',
                'Please wait around 0 minutes',
                'Change oil queue: 1',
                'Waiting for the next client',
                False,
                helper_msg_2
            )),
            TestCase(attach=partial(
                self.check_next,
                'change_oil',
                'Please wait around 2 minutes',
                'Change oil queue: 2',
                'Next ticket #2',
                True,
                helper_msg_3
            )),
            TestCase(attach=partial(
                self.check_next,
                'inflate_tires',
                'Please wait around 7 minutes',
                'Inflate tires queue: 2',
                'Next ticket #3',
                True,
                helper_msg_4
            )),
            TestCase(attach=partial(
                self.check_next,
                'diagnostic',
                'Please wait around 10 minutes',
                'Get diagnostic queue: 1',
                'Next ticket #1',
                True,
                helper_msg_5
            )),
        ]

    def check(self, reply, attach):
        return attach()
