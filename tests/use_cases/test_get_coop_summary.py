from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable
from uuid import uuid4

from pytest import approx

from arbeitszeit.entities import ProductionCosts
from arbeitszeit.use_cases.get_coop_summary import (
    GetCoopSummary,
    GetCoopSummaryRequest,
    GetCoopSummaryResponse,
    GetCoopSummarySuccess,
)

from .base_test_case import BaseTestCase


class GetCoopSummaryTests(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.get_coop_summary = self.injector.get(GetCoopSummary)

    def test_that_none_is_returned_when_cooperation_does_not_exist(self) -> None:
        requester = self.company_generator.create_company_entity()
        summary = self.get_coop_summary(GetCoopSummaryRequest(requester.id, uuid4()))
        assert summary is None

    def test_that_requester_is_correctly_defined_as_equal_to_coordinator(self) -> None:
        requester = self.company_generator.create_company_entity()
        coop = self.cooperation_generator.create_cooperation(coordinator=requester)
        summary = self.get_coop_summary(GetCoopSummaryRequest(requester.id, coop.id))
        self.assert_success(summary, lambda s: s.requester_is_coordinator == True)

    def test_that_requester_is_correctly_defined_as_different_from_coordinator(
        self,
    ) -> None:
        requester = self.company_generator.create_company_entity()
        coop = self.cooperation_generator.create_cooperation()
        summary = self.get_coop_summary(GetCoopSummaryRequest(requester.id, coop.id))
        self.assert_success(summary, lambda s: s.requester_is_coordinator == False)

    def test_that_correct_amount_of_associated_plans_are_shown(self) -> None:
        requester = self.company_generator.create_company_entity()
        plan1 = self.plan_generator.create_plan()
        plan2 = self.plan_generator.create_plan()
        coop = self.cooperation_generator.create_cooperation(plans=[plan1, plan2])
        summary = self.get_coop_summary(GetCoopSummaryRequest(requester.id, coop.id))
        self.assert_success(summary, lambda s: len(s.plans) == 2)

    def test_that_correct_coordinator_id_is_shown(self) -> None:
        requester = self.company_generator.create_company_entity()
        plan1 = self.plan_generator.create_plan()
        plan2 = self.plan_generator.create_plan()
        coop = self.cooperation_generator.create_cooperation(
            plans=[plan1, plan2], coordinator=requester.id
        )
        summary = self.get_coop_summary(GetCoopSummaryRequest(requester.id, coop.id))
        self.assert_success(summary, lambda s: s.current_coordinator == requester.id)

    def test_that_correct_coordinator_id_is_shown_when_several_cooperations_exist(
        self,
    ) -> None:
        requester = self.company_generator.create_company_entity()
        plan1 = self.plan_generator.create_plan()
        plan2 = self.plan_generator.create_plan()

        self.cooperation_generator.create_cooperation()
        coop = self.cooperation_generator.create_cooperation(
            plans=[plan1, plan2], coordinator=requester.id
        )
        self.cooperation_generator.create_cooperation()

        summary = self.get_coop_summary(GetCoopSummaryRequest(requester.id, coop.id))
        self.assert_success(summary, lambda s: s.current_coordinator == requester.id)

    def test_that_if_cooperation_has_two_coordinations_the_current_coordinator_is_shown(
        self,
    ) -> None:
        coordinator = self.company_generator.create_company()
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        cooperation = self.cooperation_generator.create_cooperation(
            coordinator=coordinator
        )
        self.datetime_service.advance_time(timedelta(days=1))
        current_coordination = (
            self.coordination_tenure_generator.create_coordination_tenure(
                cooperation=cooperation.id
            )
        )
        summary = self.get_coop_summary(GetCoopSummaryRequest(uuid4(), cooperation.id))
        self.assert_success(
            summary, lambda s: s.current_coordinator == current_coordination.company
        )

    def test_that_correct_coordinator_name_is_shown(self) -> None:
        expected_coordinator_name = "expected coordinator name"
        coordinator = self.company_generator.create_company(
            name=expected_coordinator_name
        )
        requester = self.company_generator.create_company_entity()
        coop = self.cooperation_generator.create_cooperation(coordinator=coordinator)
        summary = self.get_coop_summary(GetCoopSummaryRequest(requester.id, coop.id))
        self.assert_success(
            summary, lambda s: s.current_coordinator_name == expected_coordinator_name
        )

    def test_that_correct_info_of_associated_plan_is_shown(self) -> None:
        requester = self.company_generator.create_company_entity()
        plan1 = self.plan_generator.create_plan(
            costs=ProductionCosts(Decimal(2), Decimal(2), Decimal(1)),
            amount=10,
        )
        plan2 = self.plan_generator.create_plan(
            costs=ProductionCosts(Decimal(4), Decimal(4), Decimal(2)),
            amount=10,
        )
        coop = self.cooperation_generator.create_cooperation(plans=[plan1, plan2])
        summary = self.get_coop_summary(GetCoopSummaryRequest(requester.id, coop.id))
        self.assert_success(summary, lambda s: len(s.plans) == 2)
        assert summary is not None
        assert summary.plans[0].plan_id == plan1.id
        assert summary.plans[0].plan_name == plan1.prd_name
        assert summary.plans[0].plan_individual_price == approx(Decimal("0.5"))
        assert summary.plans[0].plan_coop_price == approx(Decimal("0.75"))

    def test_that_inactive_plans_do_not_show_up_in_cooperation_summary(self) -> None:
        requester = self.company_generator.create_company()
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        plan = self.plan_generator.create_plan(timeframe=1)
        coop = self.cooperation_generator.create_cooperation(plans=[plan])
        self.datetime_service.advance_time(timedelta(days=2))
        summary = self.get_coop_summary(GetCoopSummaryRequest(requester, coop.id))
        self.assert_success(summary, lambda s: len(s.plans) == 0)

    def assert_success(
        self,
        response: GetCoopSummaryResponse,
        assertion: Callable[[GetCoopSummarySuccess], bool],
    ) -> None:
        assert isinstance(response, GetCoopSummarySuccess)
        assert assertion(response)
