"""
Request snapshot (characterization) for all API adapter methods:
every method is called once with arguments generated from its type hints against a catch-all mock,
the resulting requests (method, url, body) must match tests/responses/request_snapshot.json.

Guards refactorings of the request handling - a diff means a request changed.
Regenerate after an intended change: UPDATE_REQUEST_SNAPSHOT=1 uv run pytest tests/test_request_snapshot.py
"""
import asyncio
import inspect
import json
import os
import unittest
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Union, get_args, get_origin, get_type_hints

import httpx
import respx
from pydantic import BaseModel

from dracoon.client import DRACOONClient
from dracoon.client.models import DRACOONConnection
from dracoon.branding import DRACOONBranding
from dracoon.config import DRACOONConfig
from dracoon.eventlog import DRACOONEvents
from dracoon.groups import DRACOONGroups
from dracoon.nodes import DRACOONNodes
from dracoon.public import DRACOONPublic, DRACOONPublicBranding
from dracoon.reports import DRACOONReports
from dracoon.roles import DRACOONRoles
from dracoon.settings import DRACOONSettings
from dracoon.shares import DRACOONShares
from dracoon.user import DRACOONUser
from dracoon.users import DRACOONUsers

BASE_URL = 'https://dracoon.team'
SNAPSHOT = Path('tests/responses/request_snapshot.json')

ADAPTERS = [DRACOONBranding, DRACOONConfig, DRACOONEvents, DRACOONGroups, DRACOONNodes, DRACOONPublic, DRACOONPublicBranding,
            DRACOONReports, DRACOONRoles, DRACOONSettings, DRACOONShares, DRACOONUser, DRACOONUsers]

# transfers are covered by test_uploads.py / test_downloads.py
EXCLUDED = {'upload_unencrypted', 'upload_encrypted', 'upload_s3_unencrypted', 'upload_s3_encrypted'}


def sample_value(annotation):
    """ deterministic sample argument for a type hint """
    origin = get_origin(annotation)
    if origin is Union:
        return sample_value(next(arg for arg in get_args(annotation) if arg is not type(None)))
    if origin in (list, List):
        args = get_args(annotation)
        return [sample_value(args[0])] if args else []
    if annotation is bool:
        return True
    if annotation is int:
        return 1
    if annotation is float:
        return 1.0
    if annotation is str:
        return 'string'
    if annotation is datetime:
        return datetime(2020, 1, 1)
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return list(annotation)[0]
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation.model_construct()
    return None


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
    client = DRACOONClient(base_url=BASE_URL, client_id='client_id', client_secret='client_secret')
    client.connection = DRACOONConnection(datetime.now(), 'access_token', 3600, 'refresh_token')
    client.connected = True
    captured = {}

    for adapter_class in ADAPTERS:
        adapter = adapter_class(client)
        for name, method in inspect.getmembers(adapter, inspect.iscoroutinefunction):
            if name.startswith('_') or name in EXCLUDED:
                continue
            hints = get_type_hints(method)
            kwargs = {param.name: sample_value(hints.get(param.name))
                      for param in inspect.signature(method).parameters.values()
                      if param.default is inspect.Parameter.empty and param.kind is param.POSITIONAL_OR_KEYWORD}

            with respx.mock(assert_all_called=False) as router:
                router.route().respond(200, json={})
                try:
                    await method(**kwargs)
                except Exception:
                    # responses are not valid models - only the requests matter
                    pass
                captured[f'{adapter_class.__name__}.{name}'] = [record_request(call.request) for call in router.calls]

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
