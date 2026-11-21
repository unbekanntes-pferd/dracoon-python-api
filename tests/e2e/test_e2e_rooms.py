from dracoon.errors import HTTPNotFoundError
from dracoon.nodes.models import NodeType, UpdateRoomGroups, UpdateRoomUsers

from tests.e2e.harness import E2ETestCase


class RoomTests(E2ETestCase):

    async def create_own_room(self):
        """ room with own permissions (not inherited) - the e2e user is room admin """
        return await self.create_room(inherit_perms=False, admin_ids=[self.dracoon.user_info.id])

    async def test_create_get_update_delete(self):
        room = await self.create_room()
        self.assertEqual(room.type, NodeType.room)
        self.assertEqual(room.parentId, self.room_id)

        fetched = await self.dracoon.nodes.get_node(node_id=room.id)
        self.assertEqual(fetched.name, room.name)

        new_name = self.unique_name('renamed')
        updated = await self.dracoon.nodes.update_room(node_id=room.id, room_update=self.dracoon.nodes.make_room_update(name=new_name, notes='e2e'))
        self.assertEqual(updated.name, new_name)
        self.assertEqual(updated.notes, 'e2e')

        await self.dracoon.nodes.delete_node(node_id=room.id)
        with self.assertRaises(HTTPNotFoundError):
            await self.dracoon.nodes.get_node(node_id=room.id)

    async def test_config(self):
        room = await self.create_own_room()

        configured = await self.dracoon.nodes.config_room(node_id=room.id, config_update=self.dracoon.nodes.make_room_config(recycle_bin_period=1))

        self.assertEqual(configured.recycleBinRetentionPeriod, 1)

    async def test_room_users(self):
        room = await self.create_own_room()
        user = await self.create_user()

        permissions = self.dracoon.nodes.make_permissions(manage=False)
        users_update = UpdateRoomUsers(items=[self.dracoon.nodes.make_permission_update(id=user.id, permission=permissions)])
        await self.dracoon.nodes.update_room_users(room_id=room.id, users_update=users_update)

        room_users = await self.dracoon.nodes.get_room_users(room_id=room.id, filter=f'userId:eq:{user.id}')
        self.assertEqual([item.userInfo.id for item in room_users.items], [user.id])
        self.assertTrue(room_users.items[0].isGranted)
        self.assertFalse(room_users.items[0].permissions.manage)

        await self.dracoon.nodes.delete_room_users(room_id=room.id, user_list=[user.id])
        room_users = await self.dracoon.nodes.get_room_users(room_id=room.id, filter=f'userId:eq:{user.id}|isGranted:eq:true')
        self.assertEqual(room_users.items, [])

    async def test_room_groups(self):
        room = await self.create_own_room()
        group = await self.create_group()

        permissions = self.dracoon.nodes.make_permissions(manage=False)
        groups_update = UpdateRoomGroups(items=[self.dracoon.nodes.make_permission_update(id=group.id, permission=permissions)])
        await self.dracoon.nodes.update_room_groups(room_id=room.id, groups_update=groups_update)

        room_groups = await self.dracoon.nodes.get_room_groups(room_id=room.id, filter=f'groupId:eq:{group.id}')
        self.assertEqual([item.id for item in room_groups.items], [group.id])
        self.assertTrue(room_groups.items[0].isGranted)

        await self.dracoon.nodes.delete_room_groups(room_id=room.id, group_list=[group.id])
        room_groups = await self.dracoon.nodes.get_room_groups(room_id=room.id, filter=f'groupId:eq:{group.id}|isGranted:eq:true')
        self.assertEqual(room_groups.items, [])
