from datetime import datetime
from uuid import UUID, uuid4

from arbeitszeit.use_cases import (
    AcceptCooperationResponse,
    CooperationInfo,
    DenyCooperationResponse,
    ListCoordinationsResponse,
    ListedInboundCoopRequest,
    ListedOutboundCoopRequest,
    ListInboundCoopRequestsResponse,
    ListOutboundCoopRequestsResponse,
)
from arbeitszeit_web.session import UserRole
from arbeitszeit_web.show_my_cooperations import ShowMyCooperationsPresenter
from tests.presenters.base_test_case import BaseTestCase
from tests.translator import FakeTranslator

from .url_index import UrlIndexTestImpl

LIST_COORDINATIONS_RESPONSE_LEN_1 = ListCoordinationsResponse(
    coordinations=[
        CooperationInfo(
            id=uuid4(),
            creation_date=datetime.now(),
            name="coop name",
            definition="first paragraph\nsecond paragraph",
            count_plans_in_coop=3,
        )
    ]
)


def get_inbound_response_length_1(
    coop_id: UUID = None, plan_id: UUID = None, planner_id: UUID = None
) -> ListInboundCoopRequestsResponse:
    if coop_id is None:
        coop_id = uuid4()
    if plan_id is None:
        plan_id = uuid4()
    if planner_id is None:
        planner_id = uuid4()
    return ListInboundCoopRequestsResponse(
        cooperation_requests=[
            ListedInboundCoopRequest(
                coop_id=coop_id,
                coop_name="coop name",
                plan_id=plan_id,
                plan_name="plan name",
                planner_name="planner name",
                planner_id=planner_id,
            )
        ]
    )


def get_outbound_response_length_1(
    plan_id: UUID = None, coop_id: UUID = None
) -> ListOutboundCoopRequestsResponse:
    if plan_id is None:
        plan_id = uuid4()
    if coop_id is None:
        coop_id = uuid4()
    return ListOutboundCoopRequestsResponse(
        cooperation_requests=[
            ListedOutboundCoopRequest(
                plan_id=plan_id,
                plan_name="plan name",
                coop_id=coop_id,
                coop_name="coop name",
            )
        ]
    )


class ShowMyCooperationsPresenterTests(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.url_index = self.injector.get(UrlIndexTestImpl)
        self.translator = FakeTranslator()
        self.presenter = self.injector.get(ShowMyCooperationsPresenter)

    def test_coordinations_are_presented_correctly(self):
        presentation = self.presenter.present(
            LIST_COORDINATIONS_RESPONSE_LEN_1,
            get_inbound_response_length_1(),
            AcceptCooperationResponse(rejection_reason=None),
            DenyCooperationResponse(rejection_reason=None),
            get_outbound_response_length_1(),
            None,
        )
        self.assertEqual(len(presentation.list_of_coordinations.rows), 1)
        self.assertEqual(
            presentation.list_of_coordinations.rows[0].coop_id,
            str(LIST_COORDINATIONS_RESPONSE_LEN_1.coordinations[0].id),
        )
        coop_id = LIST_COORDINATIONS_RESPONSE_LEN_1.coordinations[0].id
        self.assertEqual(
            presentation.list_of_coordinations.rows[0].coop_summary_url,
            self.url_index.get_coop_summary_url(
                coop_id=coop_id, user_role=UserRole.company
            ),
        )
        self.assertEqual(
            presentation.list_of_coordinations.rows[0].coop_creation_date,
            str(LIST_COORDINATIONS_RESPONSE_LEN_1.coordinations[0].creation_date),
        )
        self.assertEqual(
            presentation.list_of_coordinations.rows[0].coop_name,
            LIST_COORDINATIONS_RESPONSE_LEN_1.coordinations[0].name,
        )
        self.assertEqual(
            presentation.list_of_coordinations.rows[0].coop_definition,
            ["first paragraph", "second paragraph"],
        )
        self.assertEqual(
            presentation.list_of_coordinations.rows[0].count_plans_in_coop,
            str(LIST_COORDINATIONS_RESPONSE_LEN_1.coordinations[0].count_plans_in_coop),
        )

    def test_successfull_accept_request_response_is_presented_correctly(self):
        presentation_success = self.presenter.present(
            LIST_COORDINATIONS_RESPONSE_LEN_1,
            get_inbound_response_length_1(),
            AcceptCooperationResponse(rejection_reason=None),
            None,
            get_outbound_response_length_1(),
            None,
        )
        self.assertTrue(presentation_success.accept_message_success)
        self.assertFalse(presentation_success.deny_message_success)
        self.assertEqual(
            len(presentation_success.accept_message),
            1,
        )
        self.assertEqual(
            presentation_success.accept_message[0],
            self.translator.gettext("Cooperation request has been accepted."),
        )

    def test_successfull_deny_request_response_is_presented_correctly(self):
        presentation_success = self.presenter.present(
            LIST_COORDINATIONS_RESPONSE_LEN_1,
            get_inbound_response_length_1(),
            None,
            DenyCooperationResponse(rejection_reason=None),
            get_outbound_response_length_1(),
            None,
        )
        self.assertTrue(presentation_success.deny_message_success)
        self.assertFalse(presentation_success.accept_message_success)
        self.assertEqual(
            len(presentation_success.deny_message),
            1,
        )
        self.assertEqual(
            presentation_success.deny_message[0],
            self.translator.gettext("Cooperation request has been denied."),
        )

    def test_failed_accept_request_response_is_presented_correctly(self):
        presentation_failure = self.presenter.present(
            LIST_COORDINATIONS_RESPONSE_LEN_1,
            get_inbound_response_length_1(),
            AcceptCooperationResponse(
                rejection_reason=AcceptCooperationResponse.RejectionReason.plan_not_found
            ),
            None,
            get_outbound_response_length_1(),
            None,
        )
        self.assertFalse(presentation_failure.accept_message_success)
        self.assertFalse(presentation_failure.deny_message_success)
        self.assertEqual(
            len(presentation_failure.accept_message),
            1,
        )
        self.assertEqual(
            presentation_failure.accept_message[0],
            self.translator.gettext("Plan or cooperation not found."),
        )

    def test_failed_deny_request_response_is_presented_correctly(self):
        presentation_failure = self.presenter.present(
            LIST_COORDINATIONS_RESPONSE_LEN_1,
            get_inbound_response_length_1(),
            None,
            DenyCooperationResponse(
                rejection_reason=DenyCooperationResponse.RejectionReason.plan_not_found
            ),
            get_outbound_response_length_1(),
            None,
        )
        self.assertFalse(presentation_failure.deny_message_success)
        self.assertFalse(presentation_failure.accept_message_success)
        self.assertEqual(
            len(presentation_failure.deny_message),
            1,
        )
        self.assertEqual(
            presentation_failure.deny_message[0],
            self.translator.gettext("Plan or cooperation not found."),
        )

    def test_successfull_cancel_request_response_is_presented_correctly(self):
        presentation = self.presenter.present(
            LIST_COORDINATIONS_RESPONSE_LEN_1,
            get_inbound_response_length_1(),
            None,
            None,
            get_outbound_response_length_1(),
            True,
        )
        self.assertTrue(presentation.cancel_message_success)
        self.assertEqual(
            len(presentation.cancel_message),
            1,
        )
        self.assertEqual(
            presentation.cancel_message[0],
            self.translator.gettext("Cooperation request has been canceled."),
        )

    def test_failed_cancel_request_response_is_presented_correctly(self):
        presentation = self.presenter.present(
            LIST_COORDINATIONS_RESPONSE_LEN_1,
            get_inbound_response_length_1(),
            None,
            None,
            get_outbound_response_length_1(),
            False,
        )
        self.assertFalse(presentation.cancel_message_success)
        self.assertEqual(
            len(presentation.cancel_message),
            1,
        )
        self.assertEqual(
            presentation.cancel_message[0],
            self.translator.gettext("Error: Not possible to cancel request."),
        )


class InboundTest(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.presenter = self.injector.get(ShowMyCooperationsPresenter)
        self.url_index = self.injector.get(UrlIndexTestImpl)
        self.COOP_ID = uuid4()
        self.PLAN_ID = uuid4()
        self.PLANNER_ID = uuid4()
        self.view_model = self.presenter.present(
            LIST_COORDINATIONS_RESPONSE_LEN_1,
            get_inbound_response_length_1(
                coop_id=self.COOP_ID, plan_id=self.PLAN_ID, planner_id=self.PLANNER_ID
            ),
            AcceptCooperationResponse(rejection_reason=None),
            DenyCooperationResponse(rejection_reason=None),
            get_outbound_response_length_1(),
            None,
        )

    def test_inbound_coop_name_is_presented(self):
        self.assertTrue(
            self.view_model.list_of_inbound_coop_requests.rows[0].coop_name,
        )

    def test_inbound_plan_name_is_presented(self):
        self.assertTrue(
            self.view_model.list_of_inbound_coop_requests.rows[0].plan_name,
        )

    def test_inbound_planner_name_is_presented(self):
        self.assertTrue(
            self.view_model.list_of_inbound_coop_requests.rows[0].planner_name,
        )

    def test_inbound_coop_id_is_presented_correctly(self):
        self.assertEqual(
            self.view_model.list_of_inbound_coop_requests.rows[0].coop_id,
            str(self.COOP_ID),
        )

    def test_inbound_plan_id_is_presented_correctly(self):
        self.assertEqual(
            self.view_model.list_of_inbound_coop_requests.rows[0].plan_id,
            str(self.PLAN_ID),
        )

    def test_inbound_plan_url_is_presented_correctly(self):
        self.assertEqual(
            self.view_model.list_of_inbound_coop_requests.rows[0].plan_url,
            self.url_index.get_plan_summary_url(
                user_role=UserRole.company, plan_id=self.PLAN_ID
            ),
        )

    def test_inbound_planner_url_is_presented_correctly(self):
        self.assertEqual(
            self.view_model.list_of_inbound_coop_requests.rows[0].planner_url,
            self.url_index.get_company_summary_url(
                user_role=UserRole.company, company_id=self.PLANNER_ID
            ),
        )


class OutboundTest(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.presenter = self.injector.get(ShowMyCooperationsPresenter)
        self.url_index = self.injector.get(UrlIndexTestImpl)
        self.COOP_ID = uuid4()
        self.PLAN_ID = uuid4()
        self.view_model = self.presenter.present(
            LIST_COORDINATIONS_RESPONSE_LEN_1,
            get_inbound_response_length_1(),
            AcceptCooperationResponse(rejection_reason=None),
            DenyCooperationResponse(rejection_reason=None),
            get_outbound_response_length_1(plan_id=self.PLAN_ID, coop_id=self.COOP_ID),
            None,
        )

    def test_outbound_plan_id_is_presented_correctly(self):
        self.assertEqual(
            self.view_model.list_of_outbound_coop_requests.rows[0].plan_id,
            str(self.PLAN_ID),
        )

    def test_outbound_coop_id_is_presented_correctly(self):
        self.assertEqual(
            self.view_model.list_of_outbound_coop_requests.rows[0].coop_id,
            str(self.COOP_ID),
        )

    def test_outbound_coop_name_is_presented(self):
        self.assertTrue(
            self.view_model.list_of_outbound_coop_requests.rows[0].coop_name,
        )

    def test_outbound_plan_name_is_presented(self):
        self.assertTrue(
            self.view_model.list_of_outbound_coop_requests.rows[0].plan_name,
        )

    def test_outbound_plan_url_is_presented_correctly(self):
        self.assertEqual(
            self.view_model.list_of_outbound_coop_requests.rows[0].plan_url,
            self.url_index.get_plan_summary_url(
                user_role=UserRole.company, plan_id=self.PLAN_ID
            ),
        )
