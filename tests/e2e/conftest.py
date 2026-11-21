"""
E2E test run cleanup: removes the run rooms (see harness.TestRun) after all tests - also if tests failed.
"""
import asyncio

from tests.e2e.harness import test_run


def pytest_sessionfinish(session):
    errors = asyncio.run(test_run.cleanup())
    if errors:
        reporter = session.config.pluginmanager.get_plugin('terminalreporter')
        for error in errors:
            message = f'E2E cleanup failed - remove manually: {error}'
            if reporter:
                reporter.write_line(message, red=True)
            else:
                print(message)
