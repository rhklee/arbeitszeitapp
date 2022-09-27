from uuid import UUID

from arbeitszeit.use_cases import (
    InviteWorkerToCompanyUseCase,
    ShowWorkInvites,
    ShowWorkInvitesRequest,
)

from .base_test_case import BaseTestCase


class ShowWorkInvitesTests(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.show_work_invites = self.injector.get(ShowWorkInvites)
        self.member: UUID = self.member_generator.create_member().id
        self.company: UUID = self.company_generator.create_company().id
        self.invite_worker_to_company = self.injector.get(InviteWorkerToCompanyUseCase)

    def test_no_invites_are_shown_when_none_was_sent(self) -> None:
        request = ShowWorkInvitesRequest(member=self.member)
        response = self.show_work_invites(request)
        self.assertFalse(response.invites)

    def test_invites_are_shown_when_worker_was_previously_invited(self) -> None:
        self.invite_worker_to_company(
            InviteWorkerToCompanyUseCase.Request(
                company=self.company,
                worker=self.member,
            )
        )
        response = self.show_work_invites(
            ShowWorkInvitesRequest(
                member=self.member,
            )
        )
        self.assertTrue(response.invites)

    def test_show_which_company_sent_the_invite(self) -> None:
        self.invite_worker_to_company(
            InviteWorkerToCompanyUseCase.Request(
                company=self.company,
                worker=self.member,
            )
        )
        response = self.show_work_invites(
            ShowWorkInvitesRequest(
                member=self.member,
            )
        )
        self.assertEqual(response.invites[0].company_id, self.company)
