"""
Error contract for all API adapter methods (HTTP 404 on every request):
- raise_on_err=True: raises the typed DRACOONHttpError subclass (HTTPNotFoundError)
- default (raise_on_err=False): no exception, returns None (error is logged)

KNOWN_BROKEN_* list methods violating the contract today. They are strict: a listed method that
fulfills the contract fails the test, so the lists shrink with every fix.
"""
import asyncio
import warnings
import unittest

import respx

from dracoon.errors import HTTPNotFoundError
from tests.adapter_harness import adapter_methods, make_client

ERROR_RESPONSE = {"code": 404, "message": "Not found", "errorCode": -40000}

# method default is raise_on_err=True (public default - kept)
RAISES_BY_DEFAULT = {'DRACOONGroups.get_group'}

# B18: no raise_for_status - HTTP errors are never raised
KNOWN_BROKEN_RAISE = {'DRACOONNodes.get_parents'}

# B11: HTTP error ends in ValidationError / TypeError / UnboundLocalError or a model parsed from the error body
KNOWN_BROKEN_DEFAULT = {
    'DRACOONBranding.get_branding',
    'DRACOONBranding.update_branding',
    'DRACOONConfig.get_algorithms',
    'DRACOONConfig.get_classification_policies',
    'DRACOONConfig.get_current_product_package',
    'DRACOONConfig.get_general_settings',
    'DRACOONConfig.get_infrastructure_properties',
    'DRACOONConfig.get_password_policies',
    'DRACOONConfig.get_product_packages',
    'DRACOONConfig.get_s3_tags',
    'DRACOONConfig.get_system_defaults',
    'DRACOONEvents.get_events',
    'DRACOONEvents.get_permissions',
    'DRACOONEvents.get_rooms',
    'DRACOONGroups.add_group_users',
    'DRACOONGroups.create_group',
    'DRACOONGroups.delete_group_users',
    'DRACOONGroups.get_group_last_admin_rooms',
    'DRACOONGroups.get_group_roles',
    'DRACOONGroups.get_group_users',
    'DRACOONGroups.get_groups',
    'DRACOONGroups.update_group',
    'DRACOONNodes.add_favorite',
    'DRACOONNodes.add_node_comment',
    'DRACOONNodes.check_s3_upload',
    'DRACOONNodes.complete_upload',
    'DRACOONNodes.config_room',
    'DRACOONNodes.copy_nodes',
    'DRACOONNodes.create_folder',
    'DRACOONNodes.create_room',
    'DRACOONNodes.create_upload_channel',
    'DRACOONNodes.encrypt_room',
    'DRACOONNodes.get_deleted_node',
    'DRACOONNodes.get_deleted_nodes',
    'DRACOONNodes.get_download_url',
    'DRACOONNodes.get_file_versions',
    'DRACOONNodes.get_missing_file_keys',
    'DRACOONNodes.get_node',
    'DRACOONNodes.get_node_comments',
    'DRACOONNodes.get_node_versions',
    'DRACOONNodes.get_nodes',
    'DRACOONNodes.get_parents',
    'DRACOONNodes.get_pending_assignments',
    'DRACOONNodes.get_room_events',
    'DRACOONNodes.get_room_groups',
    'DRACOONNodes.get_room_users',
    'DRACOONNodes.get_room_webhooks',
    'DRACOONNodes.get_s3_urls',
    'DRACOONNodes.get_user_file_key',
    'DRACOONNodes.move_nodes',
    'DRACOONNodes.search_nodes',
    'DRACOONNodes.update_file',
    'DRACOONNodes.update_folder',
    'DRACOONNodes.update_room',
    'DRACOONNodes.update_room_webhooks',
    'DRACOONPublic.get_auth_ad_info',
    'DRACOONPublic.get_auth_openid_info',
    'DRACOONPublic.get_system_info',
    'DRACOONPublicBranding.get_public_branding',
    'DRACOONPublicBranding.get_public_branding_image',
    'DRACOONReports.get_reports',
    'DRACOONRoles.assign_groups_to_role',
    'DRACOONRoles.assign_users_to_role',
    'DRACOONRoles.get_groups_with_role',
    'DRACOONRoles.get_roles',
    'DRACOONRoles.get_users_with_role',
    'DRACOONRoles.remove_groups_from_role',
    'DRACOONRoles.remove_users_from_role',
    'DRACOONSettings.create_webhook',
    'DRACOONSettings.get_settings',
    'DRACOONSettings.get_webhook',
    'DRACOONSettings.get_webhook_event_types',
    'DRACOONSettings.get_webhooks',
    'DRACOONSettings.update_settings',
    'DRACOONSettings.update_webhook',
    'DRACOONShares.create_file_request',
    'DRACOONShares.create_share',
    'DRACOONShares.get_file_request',
    'DRACOONShares.get_file_requests',
    'DRACOONShares.get_share',
    'DRACOONShares.get_shares',
    'DRACOONShares.update_file_request',
    'DRACOONShares.update_share',
    'DRACOONUser.get_account_information',
    'DRACOONUser.get_user_keypair',
    'DRACOONUser.update_account_information',
    'DRACOONUsers.create_user',
    'DRACOONUsers.get_user',
    'DRACOONUsers.get_user_attributes',
    'DRACOONUsers.get_user_groups',
    'DRACOONUsers.get_user_last_admin_rooms',
    'DRACOONUsers.get_user_roles',
    'DRACOONUsers.get_users',
    'DRACOONUsers.update_user',
}


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

    def assert_contract(self, outcomes: dict, expected: dict, known_broken: set):
        for name, outcome in outcomes.items():
            with self.subTest(method=name):
                if name in known_broken:
                    self.assertNotEqual(outcome, expected[name], f'{name} fulfills the contract - remove it from the known broken list')
                else:
                    self.assertEqual(outcome, expected[name])

    def test_raise_on_err_raises_http_error(self):
        outcomes = asyncio.run(call_with_not_found(raise_on_err=True))
        expected = {name: HTTPNotFoundError.__name__ for name in outcomes}

        self.assert_contract(outcomes, expected, KNOWN_BROKEN_RAISE)

    def test_default_returns_none(self):
        outcomes = asyncio.run(call_with_not_found(raise_on_err=False))
        expected = {name: HTTPNotFoundError.__name__ if name in RAISES_BY_DEFAULT else 'None' for name in outcomes}

        self.assert_contract(outcomes, expected, KNOWN_BROKEN_DEFAULT)


if __name__ == '__main__':
    unittest.main()
