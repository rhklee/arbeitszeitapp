from unittest import TestCase
from uuid import uuid4

from arbeitszeit.repositories import MessageRepository
from arbeitszeit.use_cases import (
    CheckForUnreadMessages,
    CheckForUnreadMessagesRequest,
    InviteWorkerToCompany,
    InviteWorkerToCompanyRequest,
)
from tests.data_generators import CompanyGenerator, MemberGenerator

from .dependency_injection import get_dependency_injector


class InviteWorkerTests(TestCase):
    def setUp(self) -> None:
        self.injector = get_dependency_injector()
        self.company_generator = self.injector.get(CompanyGenerator)
        self.company = self.company_generator.create_company()
        self.member_generator = self.injector.get(MemberGenerator)
        self.member = self.member_generator.create_member()
        self.invite_worker_to_company = self.injector.get(InviteWorkerToCompany)

    def test_can_successfully_invite_worker_which_was_not_previously_invited(
        self,
    ) -> None:
        response = self.invite_worker_to_company(
            InviteWorkerToCompanyRequest(
                company=self.company.id,
                worker=self.member.id,
            )
        )
        self.assertTrue(response.is_success)

    def test_cannot_invite_worker_twices(self) -> None:
        request = InviteWorkerToCompanyRequest(
            company=self.company.id,
            worker=self.member.id,
        )
        self.invite_worker_to_company(request)
        response = self.invite_worker_to_company(request)
        assert not response.is_success

    def test_can_invite_different_workers(self) -> None:
        first_member = self.member_generator.create_member()
        second_member = self.member_generator.create_member()
        self.invite_worker_to_company(
            InviteWorkerToCompanyRequest(
                company=self.company.id,
                worker=first_member.id,
            )
        )
        response = self.invite_worker_to_company(
            InviteWorkerToCompanyRequest(
                company=self.company.id,
                worker=second_member.id,
            )
        )
        self.assertTrue(response.is_success)

    def test_can_invite_same_worker_to_different_companies(self) -> None:
        first_company = self.company_generator.create_company()
        second_company = self.company_generator.create_company()
        self.invite_worker_to_company(
            InviteWorkerToCompanyRequest(
                company=first_company.id,
                worker=self.member.id,
            )
        )
        response = self.invite_worker_to_company(
            InviteWorkerToCompanyRequest(
                company=second_company.id,
                worker=self.member.id,
            )
        )
        self.assertTrue(response.is_success)

    def test_cannot_invite_worker_that_does_not_exist(self) -> None:
        response = self.invite_worker_to_company(
            InviteWorkerToCompanyRequest(
                company=self.company.id,
                worker=uuid4(),
            )
        )
        self.assertFalse(response.is_success)

    def test_cannot_invite_worker_to_company_that_does_not_exist(self) -> None:
        response = self.invite_worker_to_company(
            InviteWorkerToCompanyRequest(
                company=uuid4(),
                worker=self.member.id,
            )
        )
        self.assertFalse(response.is_success)

    def test_response_uuid_is_not_none_on_successful_invite(self) -> None:
        response = self.invite_worker_to_company(
            InviteWorkerToCompanyRequest(
                company=self.company.id,
                worker=self.member.id,
            )
        )
        self.assertIsNotNone(response.invite_id)

    def test_after_being_invited_the_member_has_unread_messages(self) -> None:
        self.invite_worker_to_company(
            InviteWorkerToCompanyRequest(
                company=self.company.id,
                worker=self.member.id,
            )
        )
        check_for_unread_messages = self.injector.get(CheckForUnreadMessages)
        response = check_for_unread_messages(
            CheckForUnreadMessagesRequest(
                user=self.member.id,
            )
        )
        self.assertTrue(response.has_unread_messages)

    def test_after_being_invited_the_member_has_received_a_message_with_the_correct_title(
        self,
    ) -> None:
        message_repository: MessageRepository
        self.invite_worker_to_company(
            InviteWorkerToCompanyRequest(
                company=self.company.id,
                worker=self.member.id,
            )
        )
        message_repository = self.injector.get(MessageRepository)  # type: ignore
        messages = list(message_repository.get_messages_to_user(self.member.id))
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertEqual(
            message.title, f"Company {self.company.name} invited you to join them"
        )
