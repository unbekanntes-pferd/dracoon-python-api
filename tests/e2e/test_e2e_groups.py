from dracoon.errors import HTTPNotFoundError

from tests.e2e.harness import E2ETestCase


class GroupManagementTests(E2ETestCase):

    async def test_create_get_update_delete(self):
        group = await self.create_group()

        fetched = await self.dracoon.groups.get_group(group_id=group.id)
        self.assertEqual(fetched.name, group.name)

        new_name = self.unique_name('renamed')
        updated = await self.dracoon.groups.update_group(group_id=group.id, group_update=self.dracoon.groups.make_group_update(name=new_name))
        self.assertEqual(updated.name, new_name)

        await self.dracoon.groups.delete_group(group_id=group.id)
        with self.assertRaises(HTTPNotFoundError):
            await self.dracoon.groups.get_group(group_id=group.id)

    async def test_list_filtered_by_name(self):
        group = await self.create_group()

        groups = await self.dracoon.groups.get_groups(filter=f'name:cn:{group.name}')

        self.assertEqual([item.id for item in groups.items], [group.id])

    async def test_members(self):
        group = await self.create_group()
        users = [await self.create_user() for _ in range(2)]
        user_ids = {user.id for user in users}

        updated = await self.dracoon.groups.add_group_users(group_id=group.id, user_list=list(user_ids))
        self.assertEqual(updated.cntUsers, 2)
        members = await self.dracoon.groups.get_group_users(group_id=group.id, filter='isMember:eq:true')
        self.assertEqual({item.userInfo.id for item in members.items}, user_ids)

        updated = await self.dracoon.groups.delete_group_users(group_id=group.id, user_list=list(user_ids))
        self.assertEqual(updated.cntUsers, 0)

    async def test_roles_and_last_admin_rooms(self):
        group = await self.create_group()

        roles = await self.dracoon.groups.get_group_roles(group_id=group.id)
        rooms = await self.dracoon.groups.get_group_last_admin_rooms(group_id=group.id)

        self.assertIsNotNone(roles.items)
        self.assertEqual(rooms.items, [])
