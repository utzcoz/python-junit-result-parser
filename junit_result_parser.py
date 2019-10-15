import argparse
import errno
import fnmatch
import os
import sys
import xml.sax

HELP_DESCRIPTION = '''Parse junit xml result from provided result dir.'''
EPILOG_TEXT = '''
-----------------------------------------------
PARSE JUNIT XML RESULT FROM PROVIDED RESULT DIR
-----------------------------------------------

    Usage template: junit_result_parser -d <JUNIT_XML_RESULT_DIR> --show-error-message --show-failed-message
    
    <JUNIT_XML_RESULT_DIR>
    
        The dir of junit xml result.
        
    --show-error-message
    
        If append this command, the program will show the message of tests occur error when running.
        
    --show-failed-message
    
        If append this command, the program will show the mssage of failed tests.

'''


class TestSuite:
    """Class to encapsulate testsuite element.

    <testsuite name="test_suite_name" tests="5" skipped="0" failures="1" errors="0"
    timestamp="2019-05-18T03:51:11" hostname="host_name" time="8.597">
    </testsuite>
    """

    def __init__(self):
        self.name = ''
        self.tests = 0
        self.skipped = 0
        self.failures = 0
        self.errors = 0
        self.test_cases = {}
        self.failure_cases = {}
        self.error_cases = {}

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_tests(self, tests):
        self.tests = tests

    def get_tests(self):
        return self.tests

    def set_skipped(self, skipped):
        self.skipped = skipped

    def get_skipped(self):
        return self.skipped

    def set_failures(self, failures):
        self.failures = failures

    def get_failures(self):
        return self.failures

    def set_errors(self, errors):
        self.errors = errors

    def get_errors(self):
        return self.errors

    def set_test_cases(self, test_cases):
        self.test_cases = test_cases

    def get_test_cases(self):
        return self.test_cases

    def set_failure_cases(self, failures_cases):
        self.failure_cases = failures_cases

    def get_failure_cases(self):
        return self.failure_cases

    def set_error_cases(self, error_cases):
        self.error_cases = error_cases

    def get_error_cases(self):
        return self.error_cases

    def __str__(self):
        test_cases_string = ''
        for _, test_cases in self.test_cases.items():
            for test_case in test_cases:
                test_cases_string += test_case.__str__()

        failure_cases_string = ''
        for _, failure_cases in self.failure_cases.items():
            for failure_case in failure_cases:
                failure_cases_string += failure_case.__str__()

        error_cases_string = ''
        for _, error_cases in self.error_cases.items():
            for error_case in error_cases:
                error_cases_string += error_case.__str__()

        return 'Test suite name:' + self.name \
               + ", tests:" + self.tests.__str__() \
               + ", skipped:" + self.skipped.__str__() \
               + ", failures:" + self.failures.__str__() \
               + ", errors:" + self.errors.__str__() \
               + ", test cases:" + test_cases_string \
               + ", failure cases:" + failure_cases_string \
               + ", error cases:" + error_cases_string


class TestCase:
    """Class to encapsulate testcase element.

    <testcase name="test_function_name" classname="test_class" time="7.187">
    """

    def __init__(self):
        self.name = ''
        self.class_name = ''
        self.time = ''

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_class_name(self, class_name):
        self.class_name = class_name

    def get_class_name(self):
        return self.class_name

    def set_time(self, time):
        self.time = time

    def get_time(self):
        return self.time

    def __str__(self):
        return 'Test case name:' + self.name \
               + ", class name:" + self.class_name \
               + ", time:" + self.time


class Failure:
    """Class to encapsulate failure element.

    The failure element is included by testcase element.

    <failure message="failure_message" type="failure_type">
    failure body
    </failure>

    """

    def __init__(self):
        self.test_case = None
        self.message = ''
        self.failure_type = ''
        self.failure_content = ''

    def set_test_case(self, test_case):
        self.test_case = test_case

    def get_test_case(self):
        return self.test_case

    def set_message(self, message):
        self.message = message

    def get_message(self):
        return self.message

    def set_failure_type(self, failure_type):
        self.failure_type = failure_type

    def get_failure_type(self):
        return self.failure_type

    def set_failure_content(self, content):
        self.failure_content = content

    def get_failure_content(self):
        return self.failure_content

    def __str__(self):
        return 'Failure class name:' + self.test_case.__str__() \
               + ", message:" + self.message \
               + ", failure type:" + self.failure_type \
               + ", failure content:" + self.failure_content


class Error:
    """Class to encapsulate error element.

    The error element is include by testcase element.
    <error type="error_type">
    error body
    </error>
    """

    def __init__(self):
        self.test_case = None
        self.error_type = ''
        self.error_content = ''

    def set_test_case(self, test_case):
        self.test_case = test_case

    def get_test_case(self):
        return self.test_case

    def set_error_type(self, error_type):
        self.error_type = error_type

    def get_error_type(self):
        return self.error_type

    def set_error_content(self, error_content):
        self.error_content = error_content

    def get_error_content(self):
        return self.error_content

    def __str__(self):
        return 'Error name:' + self.test_case.__str__() \
               + ', error type:' + self.error_type \
               + ', error content:' + self.error_content


class JUnitXmlResultHandler(xml.sax.ContentHandler):
    """Class to parse junit xml result based on sax API.
    """

    def __init__(self):
        super(JUnitXmlResultHandler, self).__init__()
        self.test_suites = set()
        self.current_test_suite = None
        self.current_test_case = None
        self.current_failure_case = None
        self.current_error_case = None

    def startElement(self, tag, attrs):
        # We only support testsuite, testcase and failure now.
        if tag == "testsuite":
            self.current_test_suite = TestSuite()
            self.current_test_suite.set_name(attrs['name'])
            self.current_test_suite.set_tests(int(attrs['tests']))
            self.current_test_suite.set_skipped(int(attrs['skipped']))
            self.current_test_suite.set_failures(int(attrs['failures']))
            self.current_test_suite.set_errors(int(attrs['errors']))
            self.test_suites.add(self.current_test_suite)

        if tag == 'testcase':
            test_case = TestCase()
            test_case.set_name(attrs['name'])
            test_case.set_class_name(attrs['classname'])
            test_case.set_time(attrs['time'])
            test_cases_with_class_name = \
                self.current_test_suite.get_test_cases().get(test_case.get_class_name(), None)
            if test_cases_with_class_name is None:
                test_cases_with_class_name = set()
            test_cases_with_class_name.add(test_case)
            self.current_test_suite.get_test_cases()[test_case.get_class_name()] = \
                test_cases_with_class_name

            self.current_test_case = test_case

        if tag == 'failure':
            # Failure content will be parsed in characters() callback.
            failure = Failure()
            failure.set_message(attrs['message'])
            failure.set_failure_type(attrs['type'])
            failure.set_test_case(self.current_test_case)
            failure_class_name = failure.get_test_case().get_class_name()
            failures_with_class_name = \
                self.current_test_suite.get_failure_cases().get(failure_class_name, None)
            if failures_with_class_name is None:
                failures_with_class_name = set()
            failures_with_class_name.add(failure)
            self.current_test_suite.get_failure_cases()[failure_class_name] = \
                failures_with_class_name

            self.current_failure_case = failure

        if tag == 'error':
            # Error content will be parsed in characters() callback.
            error = Error()
            error.set_error_type(attrs['type'])
            error.set_test_case(self.current_test_case)
            error_class_name = error.get_test_case().get_class_name()
            errors_with_class_name = \
                self.current_test_suite.get_error_cases().get(error_class_name, None)
            if errors_with_class_name is None:
                errors_with_class_name = set()
            errors_with_class_name.add(error)
            self.current_test_suite.get_error_cases()[error_class_name] = \
                errors_with_class_name

            self.current_error_case = error

    def characters(self, content):
        if self.current_failure_case is not None:
            failure_content = self.current_failure_case.get_failure_content()
            failure_content += content
            self.current_failure_case.set_failure_content(failure_content)

        if self.current_error_case is not None:
            error_content = self.current_error_case.get_error_content()
            error_content += content
            self.current_error_case.set_error_content(error_content)

    def endElement(self, tag):
        if tag == 'testsuite':
            self.current_test_suite = None
        if tag == 'testcase':
            self.current_test_case = None
        if tag == 'failure':
            self.current_failure_case = None
        if tag == 'error':
            self.current_error_case = None

    def get_test_suites(self):
        return self.test_suites


def _parse_args(argv):
    """Parse command line arguments.

    :param argv: A list of arguments.
    :return: Returns an argspace.Namespace class instance holding parsed args.
    """
    parser = argparse.ArgumentParser(
        description=HELP_DESCRIPTION,
        epilog=EPILOG_TEXT,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-d', '--dir', help='Assign junit xml result dir.')
    parser.add_argument(
        '--show-error-message',
        action='store_true',
        dest='show_error_message',
        help='Show message of tests occur error when running.'
    )
    parser.add_argument(
        '--show-failed-message',
        action='store_true',
        dest='show_failed_message',
        help='Show message of failed tests'
    )
    return parser.parse_args(argv)


def _parse_junit_xml_result(junit_xml_file_path):
    """Parse junit xml result.

    :param junit_xml_file_path: The junit xml result path.
    :return: Returns parsed result dict.
    """
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    parser_handler = JUnitXmlResultHandler()
    parser.setContentHandler(parser_handler)
    parser.parse(junit_xml_file_path)
    return parser_handler.get_test_suites()


def _merge_failure_cases(current_failure_cases, failure_cases):
    if current_failure_cases is None:
        return failure_cases
    for class_name, failure_cases_with_same_class_name in current_failure_cases.items():
        exist_failure_cases_with_same_class_name = failure_cases.get(class_name, set())
        exist_failure_cases_with_same_class_name.update(failure_cases_with_same_class_name)
        failure_cases[class_name] = exist_failure_cases_with_same_class_name
    return failure_cases


def _merge_error_cases(current_error_cases, error_cases):
    if current_error_cases is None:
        return error_cases
    for class_name, error_cases_with_same_class_name in current_error_cases.items():
        exist_error_cases_with_same_class_name = error_cases.get(class_name, set())
        exist_error_cases_with_same_class_name.update(error_cases_with_same_class_name)
        error_cases[class_name] = exist_error_cases_with_same_class_name
    return error_cases


def main(argv):
    """Entry point of parser script.

    :param argv: A list of arguments.
    :return: Returns exit code.
    """
    args = _parse_args(argv)

    # Make sure junit xml result
    junit_xml_result_dir = args.dir
    if junit_xml_result_dir is None:
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), "Must assign junit xml result.")
    if os.path.exists(junit_xml_result_dir) is False:
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), "Must assign exist junit xml result.")

    # We only support basic counting for test cases result.
    # TODO add more arguments to get more information.
    total_test_cases = 0
    total_skipped_cases = 0
    total_failure_cases = 0
    total_error_cases = 0
    failure_cases = {}
    error_cases = {}
    for parent_dir, _, filenames in os.walk(junit_xml_result_dir):
        for filename in fnmatch.filter(filenames, '*.xml'):
            junit_xml_result_file = os.path.join(parent_dir, filename)
            if os.path.exists(junit_xml_result_file) is False:
                continue
            parsed_test_suites = _parse_junit_xml_result(junit_xml_result_file)
            for parsed_test_suite in parsed_test_suites:
                total_test_cases += parsed_test_suite.get_tests()
                total_skipped_cases += parsed_test_suite.get_skipped()
                total_failure_cases += parsed_test_suite.get_failures()
                total_error_cases += parsed_test_suite.get_errors()
                current_failure_cases = parsed_test_suite.get_failure_cases()
                failure_cases = _merge_failure_cases(current_failure_cases, failure_cases)
                current_error_cases = parsed_test_suite.get_error_cases()
                error_cases = _merge_error_cases(current_error_cases, error_cases)

    print('Total test cases %d, failures %d, skipped %d, errors %d'
          % (total_test_cases, total_failure_cases, total_skipped_cases, total_error_cases))
    if args.show_error_message is True or args.show_failed_message is True:
        print('')

    if args.show_failed_message is True:
        for class_name, failure_cases_with_same_class_name in failure_cases.items():
            if len(failure_cases_with_same_class_name) > 0:
                print('==============================================================================')
                print('Failure cases in class %s' % class_name)
                print('==============================================================================')
            for failure_case in failure_cases_with_same_class_name:
                print('Failure case %s' % failure_case)
                print('')

    if args.show_error_message is True:
        for class_name, error_cases_with_same_class_name in error_cases.items():
            if len(error_cases_with_same_class_name) > 0:
                print('==============================================================================')
                print('Error cases in class %s' % class_name)
                print('==============================================================================')
            for error_case in error_cases_with_same_class_name:
                print('Error case %s' % error_case)
                print('')


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
