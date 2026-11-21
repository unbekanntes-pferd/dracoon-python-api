"""
Request snapshot (characterization) for all API adapter methods:
every method is called once with arguments generated from its type hints against a catch-all mock,
the resulting requests (method, url, body) must match tests/responses/request_snapshot.json.

Guards refactorings of the request handling - a diff means a request changed.
Regenerate after an intended change: UPDATE_REQUEST_SNAPSHOT=1 uv run pytest tests/test_request_snapshot.py
"""
import asyncio
import warnings
import json
import os
import unittest
from pathlib import Path

import httpx
import respx

from tests.adapter_harness import adapter_methods, make_client

SNAPSHOT = Path('tests/responses/request_snapshot.json')


def mask_keys(value):
    """ generated keys (PEM) differ per run """
    if isinstance(value, dict):
        return {key: mask_keys(item) for key, item in value.items()}
    if isinstance(value, list):
        return [mask_keys(item) for item in value]
    if isinstance(value, str) and value.startswith('-----BEGIN'):
        return '<PEM>'
    return value


def record_request(request: httpx.Request) -> dict:
    content = request.content.decode('utf-8', errors='replace')
    try:
        body = json.loads(content) if content else None
    except ValueError:
        body = content
    return {"method": request.method, "url": str(request.url), "body": mask_keys(body)}


async def capture_requests() -> dict:
    client = make_client()
    captured = {}

    for name, method, kwargs in adapter_methods(client):
        with respx.mock(assert_all_called=False) as router:
            router.route().respond(200, json={})
            # JSON ready sample values in model fields cause pydantic serializer warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                try:
                    await method(**kwargs)
                except Exception:
                    # responses are not valid models - only the requests matter
                    pass
            captured[name] = [record_request(call.request) for call in router.calls]

    await client.disconnect()
    return captured


class TestRequestSnapshot(unittest.TestCase):

    def test_requests_match_snapshot(self):
        captured = asyncio.run(capture_requests())

        if os.environ.get('UPDATE_REQUEST_SNAPSHOT'):
            SNAPSHOT.write_text(json.dumps(captured, indent=2, sort_keys=True) + '\n')
            self.skipTest('request snapshot updated')

        snapshot = json.loads(SNAPSHOT.read_text())
        self.assertEqual(sorted(captured), sorted(snapshot), 'adapter methods changed')
        for method, requests in snapshot.items():
            with self.subTest(method=method):
                self.assertEqual(captured[method], requests)


if __name__ == '__main__':
    unittest.main()
