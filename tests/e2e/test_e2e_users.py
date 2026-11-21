from dracoon.errors import HTTPNotFoundError

from tests.e2e.harness import E2ETestCase


class UserManagementTests(E2ETestCase):

    async def test_create_get_update_delete(self):
        user = await self.create_user()

        fetched = await self.dracoon.users.get_user(user_id=user.id)
        self.assertEqual(fetched.userName, user.userName)

        updated = await self.dracoon.users.update_user(user_id=user.id, user_update=self.dracoon.users.make_user_update(first_name='Updated', locked=True))
        self.assertEqual(updated.firstName, 'Updated')
        self.assertTrue(updated.isLocked)

        await self.dracoon.users.delete_user(user_id=user.id)
        with self.assertRaises(HTTPNotFoundError):
            await self.dracoon.users.get_user(user_id=user.id)

    async def test_list_filtered_by_login(self):
        user = await self.create_user()

        users = await self.dracoon.users.get_users(filter=f'userName:cn:{user.userName}')

        self.assertEqual([item.id for item in users.items], [user.id])

    async def test_attributes(self):
        user = await self.create_user()
        attribute = self.dracoon.users.make_custom_user_attribute(key='e2e', value='value')

        await self.dracoon.users.update_user_attributes(user_id=user.id, attributes=self.dracoon.users.make_attributes_update([attribute]))
        attributes = await self.dracoon.users.get_user_attributes(user_id=user.id)
        self.assertEqual({item.key: item.value for item in attributes.items}, {'e2e': 'value'})

        await self.dracoon.users.delete_user_attribute(user_id=user.id, key='e2e')
        self.assertEqual((await self.dracoon.users.get_user_attributes(user_id=user.id)).items, [])

    async def test_groups_and_roles(self):
        user = await self.create_user()
        group = await self.create_group()
        await self.dracoon.groups.add_group_users(group_id=group.id, user_list=[user.id])

        user_groups = await self.dracoon.users.get_user_groups(user_id=user.id, filter='isMember:eq:true')
        self.assertEqual([item.id for item in user_groups.items], [group.id])

        roles = await self.dracoon.users.get_user_roles(user_id=user.id)
        self.assertIsNotNone(roles.items)

    async def test_last_admin_rooms(self):
        user = await self.create_user()

        rooms = await self.dracoon.users.get_user_last_admin_rooms(user_id=user.id)

        self.assertEqual(rooms.items, [])
