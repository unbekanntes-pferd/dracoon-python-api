"""
Error contract for all API adapter methods (HTTP 404 on every request):
- raise_on_err=True: raises the typed DRACOONHttpError subclass (HTTPNotFoundError)
- default (raise_on_err=False): no exception, returns None (error is logged)
"""
import asyncio
import warnings
import unittest

import respx

from dracoon.errors import HTTPNotFoundError
from tests.adapter_harness import adapter_methods, make_client

ERROR_RESPONSE = {"code": 404, "message": "Not found", "errorCode": -40000}


async def call_with_not_found(raise_on_err: bool) -> dict:
    """ outcome per method: 'None', 'returned <type>', exception class name - methods without request are skipped """
    client = make_client(raise_on_err=raise_on_err)
    outcomes = {}

    for name, method, kwargs in adapter_methods(client):
        with respx.mock(assert_all_called=False) as router:
            router.route().respond(404, json=ERROR_RESPONSE)
            # JSON ready sample values in model fields cause pydantic serializer warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                try:
                    result = await method(**kwargs)
                    outcome = 'None' if result is None else f'returned {type(result).__name__}'
                except Exception as error:
                    outcome = type(error).__name__
            if router.calls:
                outcomes[name] = outcome

    await client.disconnect()
    return outcomes


class TestErrorContract(unittest.TestCase):

    def assert_contract(self, outcomes: dict, expected: dict):
        for name, outcome in outcomes.items():
            with self.subTest(method=name):
                self.assertEqual(outcome, expected[name])

    def test_raise_on_err_raises_http_error(self):
        outcomes = asyncio.run(call_with_not_found(raise_on_err=True))
        expected = {name: HTTPNotFoundError.__name__ for name in outcomes}

        self.assert_contract(outcomes, expected)

    def test_default_returns_none(self):
        outcomes = asyncio.run(call_with_not_found(raise_on_err=False))
        expected = {name: 'None' for name in outcomes}

        self.assert_contract(outcomes, expected)


if __name__ == '__main__':
    unittest.main()
