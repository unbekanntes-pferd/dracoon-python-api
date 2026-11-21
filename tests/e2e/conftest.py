"""
E2E test run setup: a new keypair with a random secret for the e2e user (encrypted transfers).
Done once per run before any test - with pytest-xdist in the controller, the secret is handed to the workers.
"""
import asyncio
import os

import pytest

from tests.e2e.harness import CRYPTO_SECRET, crypto_configured, reset_keypair


def pytest_sessionstart(session):
    config = session.config
    # xdist worker: secret from the controller
    if hasattr(config, 'workerinput'):
        if CRYPTO_SECRET in config.workerinput:
            os.environ[CRYPTO_SECRET] = config.workerinput[CRYPTO_SECRET]
        return
    # never use a secret from the environment - the keypair is replaced
    os.environ.pop(CRYPTO_SECRET, None)
    if crypto_configured() and not config.option.collectonly:
        os.environ[CRYPTO_SECRET] = asyncio.run(reset_keypair())


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node):
    """ xdist hook (controller): runs after pytest_sessionstart """
    if CRYPTO_SECRET in os.environ:
        node.workerinput[CRYPTO_SECRET] = os.environ[CRYPTO_SECRET]
