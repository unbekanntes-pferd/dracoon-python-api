"""
Helpers to call every public API adapter method with arguments generated from its type hints.
Used by the request snapshot and the error contract tests.
"""
import inspect
from datetime import datetime
from enum import Enum
from typing import List, Union, get_args, get_origin, get_type_hints

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

ADAPTERS = [DRACOONBranding, DRACOONConfig, DRACOONEvents, DRACOONGroups, DRACOONNodes, DRACOONPublic, DRACOONPublicBranding,
            DRACOONReports, DRACOONRoles, DRACOONSettings, DRACOONShares, DRACOONUser, DRACOONUsers]

# transfers are covered by test_uploads.py / test_downloads.py
EXCLUDED = {'upload_unencrypted', 'upload_encrypted', 'upload_s3_unencrypted', 'upload_s3_encrypted'}


def sample_value(annotation, in_model: bool = False, name: str = ''):
    """ deterministic sample argument for a type hint (values inside models are JSON ready - model_construct skips validation) """
    origin = get_origin(annotation)
    if origin is Union:
        return sample_value(next(arg for arg in get_args(annotation) if arg is not type(None)), in_model)
    if origin in (list, List):
        args = get_args(annotation)
        return [sample_value(args[0], in_model)] if args else []
    if annotation is bool:
        return True
    if annotation is int:
        return 1
    if annotation is float:
        return 1.0
    if annotation is str:
        return f'{BASE_URL}/string' if name.lower().endswith('url') else 'string'
    if annotation is datetime:
        return '2020-01-01T00:00:00' if in_model else datetime(2020, 1, 1)
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        member = list(annotation)[0]
        return member.value if in_model else member
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation.model_construct(**{field: sample_value(info.annotation, in_model=True, name=field)
                                             for field, info in annotation.model_fields.items() if info.is_required()})
    return None


def make_client(raise_on_err: bool = False) -> DRACOONClient:
    """ client with a valid (fake) connection """
    client = DRACOONClient(base_url=BASE_URL, client_id='client_id', client_secret='client_secret', raise_on_err=raise_on_err)
    client.connection = DRACOONConnection(datetime.now(), 'access_token', 3600, 'refresh_token')
    client.connected = True
    return client


def adapter_methods(client: DRACOONClient):
    """ yields (name, bound method, sample kwargs) for all public async adapter methods """
    for adapter_class in ADAPTERS:
        adapter = adapter_class(client)
        for name, method in inspect.getmembers(adapter, inspect.iscoroutinefunction):
            if name.startswith('_') or name in EXCLUDED:
                continue
            hints = get_type_hints(method)
            kwargs = {param.name: sample_value(hints.get(param.name), name=param.name)
                      for param in inspect.signature(method).parameters.values()
                      if param.default is inspect.Parameter.empty and param.kind is param.POSITIONAL_OR_KEYWORD}
            yield f'{adapter_class.__name__}.{name}', method, kwargs
