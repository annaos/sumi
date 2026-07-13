import os
import tempfile
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from telegram import (
    Chat,
    ChatMember,
    ChatMemberAdministrator,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberUpdated,
    Update,
    User,
)

import src.members.registry as member
import src.members.events as membership
from src.handlers.member_handlers import chat_member_update
from src.members.reconcile import reconcile_members

CHAT_ID = -123


def _user(user_id=5, name="Rosa", username="rosa"):
    return User(id=user_id, first_name=name, is_bot=False, username=username)


class MembersDirectoryTestCase(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.members_dir = tmp.name
        for target in ("src.members.registry.HISTORY_MEMBERS_DIRECTORY",
                       "src.members.events.HISTORY_MEMBERS_DIRECTORY"):
            patcher = patch(target, self.members_dir)
            patcher.start()
            self.addCleanup(patcher.stop)


class MemberHelpersTestCase(MembersDirectoryTestCase):

    def test_add_member_ignores_duplicate_of_active_member(self):
        member.add_member(CHAT_ID, _user())
        member.add_member(CHAT_ID, _user())
        self.assertEqual(1, len(member.get_all_members(CHAT_ID)))

    def test_left_member_disappears_from_active_members(self):
        member.add_member(CHAT_ID, _user())
        member.left_member(CHAT_ID, _user())
        self.assertEqual([], member.get_all_members(CHAT_ID))

    def test_rejoin_after_leave_creates_new_active_entry(self):
        member.add_member(CHAT_ID, _user())
        member.left_member(CHAT_ID, _user())
        member.add_member(CHAT_ID, _user())
        self.assertEqual(1, len(member.get_all_members(CHAT_ID)))

    def test_get_chat_ids_lists_chats_with_member_files(self):
        member.add_member(CHAT_ID, _user())
        member.add_member(-456, _user())
        membership.add_entry(-789, _user(), True)
        self.assertEqual([-456, CHAT_ID], member.get_chat_ids())


class MembershipHistoryDedupTestCase(MembersDirectoryTestCase):

    def test_same_event_within_dedup_window_is_recorded_once(self):
        membership.add_entry(CHAT_ID, _user(), True)
        membership.add_entry(CHAT_ID, _user(), True)
        self.assertEqual(1, len(membership.get_last_entries(CHAT_ID, 10)))

    def test_different_status_is_recorded(self):
        membership.add_entry(CHAT_ID, _user(), True)
        membership.add_entry(CHAT_ID, _user(), False)
        self.assertEqual(2, len(membership.get_last_entries(CHAT_ID, 10)))

    def test_different_user_is_recorded(self):
        membership.add_entry(CHAT_ID, _user(user_id=5), True)
        membership.add_entry(CHAT_ID, _user(user_id=6, name="Sven"), True)
        self.assertEqual(2, len(membership.get_last_entries(CHAT_ID, 10)))


def _chat_member_update(old_state, new_state):
    user = _user()
    updated = ChatMemberUpdated(
        chat=Chat(id=CHAT_ID, type=Chat.GROUP, title="Test Chat"),
        from_user=user,
        date=datetime.now(),
        old_chat_member=old_state(user),
        new_chat_member=new_state(user),
    )
    return Update(update_id=1, chat_member=updated)


def _admin(user):
    return ChatMemberAdministrator(user=user, can_be_edited=False, is_anonymous=False,
                                   can_manage_chat=True, can_delete_messages=True,
                                   can_manage_video_chats=True, can_restrict_members=True,
                                   can_promote_members=False, can_change_info=True,
                                   can_invite_users=True, can_post_stories=False,
                                   can_edit_stories=False, can_delete_stories=False)


class ChatMemberUpdateHandlerTestCase(MembersDirectoryTestCase):

    async def test_leave_without_service_message_marks_member_as_left(self):
        member.add_member(CHAT_ID, _user())

        await chat_member_update(_chat_member_update(ChatMemberMember, ChatMemberLeft), Mock())

        self.assertEqual([], member.get_all_members(CHAT_ID))
        self.assertEqual("leave", membership.get_last_entries(CHAT_ID, 1)[0]["status"])

    async def test_join_adds_member(self):
        await chat_member_update(_chat_member_update(ChatMemberLeft, ChatMemberMember), Mock())

        self.assertEqual(1, len(member.get_all_members(CHAT_ID)))
        self.assertEqual("join", membership.get_last_entries(CHAT_ID, 1)[0]["status"])

    async def test_promotion_to_admin_is_not_a_join_or_leave(self):
        member.add_member(CHAT_ID, _user())

        await chat_member_update(_chat_member_update(ChatMemberMember, _admin), Mock())

        self.assertEqual(1, len(member.get_all_members(CHAT_ID)))
        self.assertEqual([], membership.get_last_entries(CHAT_ID, 10))


class ReconcileMembersTestCase(MembersDirectoryTestCase):

    def setUp(self):
        super().setUp()
        env = patch.dict(os.environ, {"ACTIVE_CHAT_IDS": str(CHAT_ID)})
        env.start()
        self.addCleanup(env.stop)

    def _context(self, statuses):
        async def get_chat_member(chat_id, user_id):
            return Mock(status=statuses[user_id])
        return SimpleNamespace(bot=SimpleNamespace(get_chat_member=AsyncMock(side_effect=get_chat_member)))

    async def test_silently_left_member_is_marked_as_left(self):
        member.add_member(CHAT_ID, _user(user_id=5, name="Rosa"))
        member.add_member(CHAT_ID, _user(user_id=6, name="Sven", username="sven"))

        context = self._context({5: ChatMember.LEFT, 6: ChatMember.MEMBER})
        await reconcile_members(context)

        active = member.get_all_members(CHAT_ID)
        self.assertEqual(["Sven"], [m["fullname"] for m in active])
        self.assertEqual("leave", membership.get_last_entries(CHAT_ID, 1)[0]["status"])

    async def test_banned_member_is_marked_as_left(self):
        member.add_member(CHAT_ID, _user(user_id=5))

        await reconcile_members(self._context({5: ChatMember.BANNED}))

        self.assertEqual([], member.get_all_members(CHAT_ID))

    async def test_member_without_id_is_kept_and_not_queried(self):
        members = [{"id": None, "username": None, "fullname": "Ghost", "join_at": None}]
        member._write_members_json(CHAT_ID, members)

        context = self._context({})
        await reconcile_members(context)

        context.bot.get_chat_member.assert_not_awaited()
        self.assertEqual(1, len(member.get_all_members(CHAT_ID)))

    async def test_inactive_chat_is_not_reconciled(self):
        inactive_chat = -777
        member.add_member(inactive_chat, _user(user_id=5))

        context = self._context({5: ChatMember.LEFT})
        await reconcile_members(context)

        context.bot.get_chat_member.assert_not_awaited()
        self.assertEqual(1, len(member.get_all_members(inactive_chat)))

    async def test_api_error_keeps_member(self):
        member.add_member(CHAT_ID, _user(user_id=5))
        from telegram.error import TelegramError
        context = SimpleNamespace(bot=SimpleNamespace(
            get_chat_member=AsyncMock(side_effect=TelegramError("boom"))))

        await reconcile_members(context)

        self.assertEqual(1, len(member.get_all_members(CHAT_ID)))


if __name__ == '__main__':
    unittest.main()
