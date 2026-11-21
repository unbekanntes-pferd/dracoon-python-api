from tests.e2e.harness import E2ETestCase, env


class UserProfileTests(E2ETestCase):
    """ the e2e user's own account is shared state: read-only except one update that is restored """

    async def test_account_information(self):
        account = await self.dracoon.user.get_account_information(more_info=True)

        self.assertEqual(account.userName, env('E2E_USER_NAME'))
        self.assertEqual(account.id, self.dracoon.user_info.id)

    async def test_update_account_information(self):
        account = await self.dracoon.user.get_account_information()
        restore = self.dracoon.user.make_account_update(last_name=account.lastName)
        self.addAsyncCleanup(self.dracoon.user.update_account_information, account_update=restore)

        new_name = self.unique_name()
        updated = await self.dracoon.user.update_account_information(account_update=self.dracoon.user.make_account_update(last_name=new_name))

        self.assertEqual(updated.lastName, new_name)
