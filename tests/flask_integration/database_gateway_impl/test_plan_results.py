from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from uuid import UUID, uuid4

from parameterized import parameterized

from arbeitszeit import records
from arbeitszeit.datetime_service import DatetimeService
from arbeitszeit.records import Plan, ProductionCosts
from arbeitszeit.use_cases.approve_plan import ApprovePlanUseCase
from arbeitszeit_flask.database import models
from arbeitszeit_flask.database.repositories import DatabaseGatewayImpl
from tests.control_thresholds import ControlThresholdsTestImpl
from tests.data_generators import (
    CompanyGenerator,
    ConsumptionGenerator,
    CooperationGenerator,
    PlanGenerator,
)
from tests.datetime_service import FakeDatetimeService
from tests.flask_integration.flask import FlaskTestCase


class PlanResultTests(FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.database_gateway = self.injector.get(DatabaseGatewayImpl)
        self.plan_generator = self.injector.get(PlanGenerator)
        self.datetime_service = self.injector.get(FakeDatetimeService)
        self.company_generator = self.injector.get(CompanyGenerator)

    def test_that_plan_gets_hidden(self) -> None:
        plan = self.plan_generator.create_plan()
        self.database_gateway.get_plans().with_id(plan).update().hide().perform()
        plan_from_repo = self.database_gateway.get_plans().with_id(plan).first()
        assert plan_from_repo
        assert plan_from_repo.hidden_by_user

    def test_that_availability_is_toggled_to_false(self) -> None:
        plan = self.plan_generator.create_plan(is_available=True)
        self.database_gateway.get_plans().with_id(
            plan
        ).update().toggle_product_availability().perform()
        plan_from_repo = self.database_gateway.get_plans().with_id(plan).first()
        assert plan_from_repo
        assert plan_from_repo.is_available == False

    def test_that_availability_is_toggled_to_true(self) -> None:
        plan = self.plan_generator.create_plan(is_available=False)
        self.database_gateway.get_plans().with_id(
            plan
        ).update().toggle_product_availability().perform()
        plan_from_repo = self.database_gateway.get_plans().with_id(plan).first()
        assert plan_from_repo
        assert plan_from_repo.is_available == True

    def test_create_plan_propagates_specified_arguments_to_created_plan(self) -> None:
        expected_planner = self.company_generator.create_company()
        plan = self.database_gateway.create_plan(
            creation_timestamp=(expected_timestamp := datetime(2000, 1, 1)),
            planner=expected_planner,
            production_costs=(
                expected_costs := ProductionCosts(Decimal(1), Decimal(2), Decimal(3))
            ),
            product_name=(expected_product_name := "test product name"),
            distribution_unit=(expected_distribution_unit := "test unit"),
            amount_produced=(expected_amount := 642),
            product_description=(expected_description := "test description"),
            duration_in_days=(expected_duration := 631),
            is_public_service=(expected_is_public_service := False),
        )
        assert plan.plan_creation_date == expected_timestamp
        assert plan.planner == expected_planner
        assert plan.production_costs == expected_costs
        assert plan.prd_name == expected_product_name
        assert plan.prd_unit == expected_distribution_unit
        assert plan.prd_amount == expected_amount
        assert plan.description == expected_description
        assert plan.timeframe == expected_duration
        assert plan.is_public_service == expected_is_public_service

    def test_that_created_plan_can_have_its_approval_date_changed(self) -> None:
        plan = self.create_plan()
        expected_approval_date = datetime(2000, 3, 2)
        self.database_gateway.get_plans().with_id(plan.id).update().set_approval_date(
            expected_approval_date
        ).perform()
        changed_plan = self.database_gateway.get_plans().with_id(plan.id).first()
        assert changed_plan
        assert changed_plan.approval_date == expected_approval_date

    def test_that_plan_gets_deleted(self) -> None:
        plan = self.create_plan()
        self.database_gateway.get_plans().with_id(plan.id).delete()
        assert not len(self.database_gateway.get_plans().with_id(plan.id))

    def test_that_plan_review_gets_deleted_when_plan_gets_deleted(self) -> None:
        plan = self.create_plan()
        assert self.database_gateway.db.session.query(models.PlanReview).all()
        self.database_gateway.get_plans().with_id(plan.id).delete()
        assert not self.database_gateway.db.session.query(models.PlanReview).all()

    def create_plan(self) -> Plan:
        return self.database_gateway.create_plan(
            creation_timestamp=datetime(2000, 1, 1),
            planner=self.company_generator.create_company(),
            production_costs=ProductionCosts(Decimal(1), Decimal(2), Decimal(3)),
            product_name="test product name",
            distribution_unit="test unit",
            amount_produced=642,
            product_description="test description",
            duration_in_days=631,
            is_public_service=False,
        )


class GetActivePlansTests(FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.database_gateway = self.injector.get(DatabaseGatewayImpl)
        self.plan_generator = self.injector.get(PlanGenerator)
        self.datetime_service = self.injector.get(FakeDatetimeService)
        self.company_generator = self.injector.get(CompanyGenerator)
        self.approve_plan_use_case = self.injector.get(ApprovePlanUseCase)

    def test_plans_can_be_ordered_by_creation_date_in_descending_order(
        self,
    ) -> None:
        creation_dates = [
            self.datetime_service.now_minus_ten_days(),
            self.datetime_service.now(),
            self.datetime_service.now_minus_20_hours(),
            self.datetime_service.now_minus_25_hours(),
            self.datetime_service.now_minus_one_day(),
        ]
        plans: List[UUID] = list()
        for timestamp in creation_dates:
            self.datetime_service.freeze_time(timestamp)
            plans.append(self.plan_generator.create_plan())
        self.datetime_service.unfreeze_time()
        retrieved_plans = list(
            self.database_gateway.get_plans()
            .ordered_by_creation_date(ascending=False)
            .limit(3)
        )
        assert len(retrieved_plans) == 3
        assert retrieved_plans[0].id == plans[1]
        assert retrieved_plans[1].id == plans[2]
        assert retrieved_plans[2].id == plans[4]

    def test_plans_can_be_ordered_by_activation_date_in_descending_order(
        self,
    ) -> None:
        activation_dates = [
            self.datetime_service.now_minus_ten_days(),
            self.datetime_service.now(),
            self.datetime_service.now_minus_20_hours(),
            self.datetime_service.now_minus_25_hours(),
            self.datetime_service.now_minus_one_day(),
        ]
        plans: List[UUID] = list()
        for timestamp in activation_dates:
            self.datetime_service.freeze_time(timestamp)
            plans.append(self.plan_generator.create_plan())
        self.datetime_service.unfreeze_time()
        retrieved_plans = list(
            self.database_gateway.get_plans()
            .ordered_by_activation_date(ascending=False)
            .limit(3)
        )
        assert len(retrieved_plans) == 3
        assert retrieved_plans[0].id == plans[1]
        assert retrieved_plans[1].id == plans[2]
        assert retrieved_plans[2].id == plans[4]

    def test_plans_can_be_ordered_by_planner_name(
        self,
    ) -> None:
        planner_names = ["1_name", "B_name", "d_name", "c_name"]
        planners = [
            self.company_generator.create_company_record(name=name)
            for name in planner_names
        ]
        plans: List[UUID] = list()
        for company in planners:
            plans.append(self.plan_generator.create_plan(planner=company.id))
        retrieved_plans = list(
            self.database_gateway.get_plans().ordered_by_planner_name().limit(3)
        )
        assert len(retrieved_plans) == 3
        assert retrieved_plans[0].id == plans[0]
        assert retrieved_plans[1].id == plans[1]
        assert retrieved_plans[2].id == plans[3]

    def test_that_plans_can_be_filtered_by_product_name(self) -> None:
        expected_plan = self.plan_generator.create_plan(
            product_name="Delivery of goods"
        )
        returned_plan = list(
            self.database_gateway.get_plans().with_product_name_containing(
                "Delivery of goods"
            )
        )
        assert returned_plan
        assert returned_plan[0].id == expected_plan

    def test_that_plans_can_be_filtered_by_substrings_of_product_name(
        self,
    ) -> None:
        expected_plan = self.plan_generator.create_plan(
            product_name="Delivery of goods"
        )
        returned_plan = list(
            self.database_gateway.get_plans().with_product_name_containing("very of go")
        )
        assert returned_plan
        assert returned_plan[0].id == expected_plan

    def test_that_query_plans_by_substring_of_plan_id_returns_plan(self) -> None:
        expected_plan = self.plan_generator.create_plan()
        query = str(expected_plan)[3:8]
        returned_plan = list(
            self.database_gateway.get_plans().with_id_containing(query)
        )
        assert returned_plan
        assert returned_plan[0].id == expected_plan

    def test_that_plans_that_ordering_by_creation_date_works_even_when_plan_activation_was_in_reverse_order(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        first_plan = self.plan_generator.create_plan(approved=False)
        self.datetime_service.freeze_time(datetime(2000, 1, 2))
        second_plan = self.plan_generator.create_plan(approved=False)
        self.datetime_service.freeze_time(datetime(2000, 1, 3))
        self.approve_plan_use_case.approve_plan(
            request=ApprovePlanUseCase.Request(
                plan=second_plan,
            )
        )
        self.datetime_service.freeze_time(datetime(2000, 1, 4))
        self.approve_plan_use_case.approve_plan(
            request=ApprovePlanUseCase.Request(
                plan=first_plan,
            )
        )
        plans = list(self.database_gateway.get_plans().ordered_by_creation_date())
        assert plans[0].id == first_plan
        assert plans[1].id == second_plan


class GetAllPlans(FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.company_generator = self.injector.get(CompanyGenerator)
        self.database_gateway = self.injector.get(DatabaseGatewayImpl)
        self.plan_generator = self.injector.get(PlanGenerator)
        self.datetime_service = self.injector.get(FakeDatetimeService)
        self.cooperation_generator = self.injector.get(CooperationGenerator)

    def test_that_without_any_plans_nothing_is_returned(self) -> None:
        assert not list(self.database_gateway.get_plans())

    def test_that_unapproved_plans_are_returned(self) -> None:
        self.plan_generator.create_plan(approved=False)
        assert list(self.database_gateway.get_plans())

    def test_that_approved_plans_are_returned(self) -> None:
        self.plan_generator.create_plan(approved=True)
        assert list(self.database_gateway.get_plans())

    def test_that_can_filter_unapproved_plans_from_results(self) -> None:
        self.plan_generator.create_plan(approved=False)
        assert not list(self.database_gateway.get_plans().that_are_approved())

    def test_can_filter_public_plans(self) -> None:
        self.plan_generator.create_plan(is_public_service=False)
        assert not list(self.database_gateway.get_plans().that_are_public())
        self.plan_generator.create_plan(is_public_service=True)
        assert list(self.database_gateway.get_plans().that_are_public())

    def test_can_filter_productive_plans(self) -> None:
        self.plan_generator.create_plan(is_public_service=True)
        assert not list(self.database_gateway.get_plans().that_are_productive())
        self.plan_generator.create_plan(is_public_service=False)
        assert list(self.database_gateway.get_plans().that_are_productive())

    def test_can_count_all_plans(self) -> None:
        self.plan_generator.create_plan()
        assert len(self.database_gateway.get_plans()) == 1
        self.plan_generator.create_plan()
        self.plan_generator.create_plan()
        assert len(self.database_gateway.get_plans()) == 3

    def test_can_filter_by_planner(self) -> None:
        planner = self.company_generator.create_company()
        self.plan_generator.create_plan()
        assert not self.database_gateway.get_plans().planned_by(planner)
        self.plan_generator.create_plan(planner=planner)
        assert self.database_gateway.get_plans().planned_by(planner)

    def test_can_filter_plans_by_multiple_planners(self) -> None:
        planner_1 = self.company_generator.create_company()
        planner_2 = self.company_generator.create_company()
        self.plan_generator.create_plan()
        self.plan_generator.create_plan(planner=planner_1)
        self.plan_generator.create_plan(planner=planner_2)
        assert (
            len(self.database_gateway.get_plans().planned_by(planner_1, planner_2)) == 2
        )

    def test_can_get_plan_by_its_id(self) -> None:
        expected_plan = self.plan_generator.create_plan()
        assert expected_plan in [
            p.id for p in self.database_gateway.get_plans().with_id(expected_plan)
        ]

    def test_can_filter_plans_by_multiple_ids(self) -> None:
        expected_plan_1 = self.plan_generator.create_plan()
        expected_plan_2 = self.plan_generator.create_plan()
        other_plan = self.plan_generator.create_plan()
        results = [
            p.id
            for p in self.database_gateway.get_plans().with_id(
                expected_plan_1, expected_plan_2
            )
        ]
        assert expected_plan_1 in results
        assert expected_plan_2 in results
        assert other_plan not in results

    def test_nothing_is_returned_if_plan_with_specified_uuid_is_not_present(
        self,
    ) -> None:
        self.plan_generator.create_plan()
        assert not self.database_gateway.get_plans().with_id(uuid4())

    def test_can_filter_results_for_unreviewed_plans(self) -> None:
        self.plan_generator.create_plan(approved=True)
        assert not self.database_gateway.get_plans().without_completed_review()

    def test_filtering_unreviewed_plans_will_still_contain_unreviewed_plans(
        self,
    ) -> None:
        self.plan_generator.create_plan(approved=False)
        assert self.database_gateway.get_plans().without_completed_review()

    def test_that_plans_with_open_cooperation_request_can_be_filtered(self) -> None:
        coop = self.cooperation_generator.create_cooperation()
        requesting_plan = self.plan_generator.create_plan(requested_cooperation=coop)
        non_requesting_plan = self.plan_generator.create_plan()
        results = self.database_gateway.get_plans().with_open_cooperation_request()
        assert requesting_plan in [plan.id for plan in results]
        assert non_requesting_plan not in [plan.id for plan in results]

    def test_that_plans_with_open_cooperation_request_at_specific_coop_can_be_filtered(
        self,
    ) -> None:
        coop = self.cooperation_generator.create_cooperation()
        other_coop = self.cooperation_generator.create_cooperation()
        plan_requesting_at_coop = self.plan_generator.create_plan(
            requested_cooperation=coop
        )
        plan_requesting_at_other_coop = self.plan_generator.create_plan(
            requested_cooperation=other_coop
        )
        results = self.database_gateway.get_plans().with_open_cooperation_request(
            cooperation=coop
        )
        assert plan_requesting_at_coop in [plan.id for plan in results]
        assert plan_requesting_at_other_coop not in [plan.id for plan in results]

    def test_can_filter_for_cooperating_plans(self):
        coop = self.cooperation_generator.create_cooperation()
        cooperating_plan = self.plan_generator.create_plan(cooperation=coop)
        non_cooperating_plan = self.plan_generator.create_plan(cooperation=None)
        results = self.database_gateway.get_plans().that_are_cooperating()
        assert cooperating_plan in [plan.id for plan in results]
        assert non_cooperating_plan not in [plan.id for plan in results]

    def test_plan_without_cooperation_is_considered_to_be_only_plan_in_its_own_cooperation(
        self,
    ) -> None:
        plan = self.plan_generator.create_plan(cooperation=None)
        cooperating_plans = (
            self.database_gateway.get_plans().that_are_in_same_cooperation_as(plan)
        )
        assert len(cooperating_plans) == 1
        assert plan in [p.id for p in cooperating_plans]

    def test_that_plans_outside_of_cooperation_are_excluded_when_filtering_for_cooperating_plans(
        self,
    ) -> None:
        coop = self.cooperation_generator.create_cooperation()
        plan1 = self.plan_generator.create_plan(cooperation=coop)
        plan2 = self.plan_generator.create_plan(cooperation=coop)
        self.plan_generator.create_plan(requested_cooperation=None)
        cooperating_plans = (
            self.database_gateway.get_plans().that_are_in_same_cooperation_as(plan1)
        )
        assert len(cooperating_plans) == 2
        assert plan1 in [p.id for p in cooperating_plans]
        assert plan2 in [p.id for p in cooperating_plans]

    def test_can_filter_plans_that_are_part_of_any_cooperation(self) -> None:
        cooperation = self.cooperation_generator.create_cooperation()
        self.plan_generator.create_plan(cooperation=cooperation)
        plans = self.database_gateway.get_plans().that_are_part_of_cooperation()
        assert plans

    def test_can_filter_plans_from_multiple_cooperations(self) -> None:
        cooperation1 = self.cooperation_generator.create_cooperation()
        cooperation2 = self.cooperation_generator.create_cooperation()
        self.plan_generator.create_plan(cooperation=cooperation1)
        self.plan_generator.create_plan(cooperation=cooperation2)
        plans = self.database_gateway.get_plans().that_are_part_of_cooperation(
            cooperation1, cooperation2
        )
        assert len(plans) == 2

    def test_correct_plans_in_cooperation_returned(self) -> None:
        coop = self.cooperation_generator.create_cooperation()
        plan1 = self.plan_generator.create_plan(cooperation=coop)
        plan2 = self.plan_generator.create_plan(cooperation=coop)
        plan3 = self.plan_generator.create_plan(requested_cooperation=None)
        plans = self.database_gateway.get_plans().that_are_part_of_cooperation(coop)
        assert len(plans) == 2
        assert plans.with_id(plan1)
        assert plans.with_id(plan2)
        assert not plans.with_id(plan3)

    def test_nothing_returned_when_no_plans_in_cooperation(self) -> None:
        coop = self.cooperation_generator.create_cooperation()
        self.plan_generator.create_plan(requested_cooperation=None)
        plans = self.database_gateway.get_plans().that_are_part_of_cooperation(coop)
        assert len(plans) == 0

    def test_possible_to_add_and_to_remove_plan_to_cooperation(self) -> None:
        cooperation = self.cooperation_generator.create_cooperation()
        plan = self.plan_generator.create_plan()

        self.database_gateway.get_plans().with_id(plan).update().set_cooperation(
            cooperation
        ).perform()
        plan_from_orm = self.database_gateway.get_plans().with_id(plan).first()
        assert plan_from_orm
        assert plan_from_orm.cooperation == cooperation

        self.database_gateway.get_plans().with_id(plan).update().set_cooperation(
            None
        ).perform()
        plan_from_orm = self.database_gateway.get_plans().with_id(plan).first()
        assert plan_from_orm
        assert plan_from_orm.cooperation is None

    def test_can_set_approval_date(self) -> None:
        plan = self.plan_generator.create_plan()
        plans = self.database_gateway.get_plans().with_id(plan)
        expected_approval_date = datetime(2000, 3, 2)
        assert plans.update().set_approval_date(expected_approval_date).perform()
        assert all(plan.approval_date == expected_approval_date for plan in plans)


class GetStatisticsTests(FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.company_generator = self.injector.get(CompanyGenerator)
        self.database_gateway = self.injector.get(DatabaseGatewayImpl)
        self.plan_generator = self.injector.get(PlanGenerator)
        self.datetime_service = self.injector.get(FakeDatetimeService)
        self.cooperation_generator = self.injector.get(CooperationGenerator)

    def test_with_no_plans_that_average_planning_duration_is_0(self) -> None:
        stats = self.database_gateway.get_plans().get_statistics()
        assert stats.average_plan_duration_in_days == Decimal(0)

    def test_with_no_plans_that_planning_costs_are_0(self) -> None:
        stats = self.database_gateway.get_plans().get_statistics()
        assert stats.total_planned_costs == ProductionCosts.zero()

    def test_with_one_active_plan_that_average_duration_is_exactly_the_length_of_that_plan(
        self,
    ) -> None:
        self.plan_generator.create_plan(timeframe=3)
        stats = self.database_gateway.get_plans().get_statistics()
        assert stats.average_plan_duration_in_days == Decimal(3)

    def test_with_two_active_plans_the_average_duration_is_the_mean_of_those_plans(
        self,
    ) -> None:
        self.plan_generator.create_plan(timeframe=3)
        self.plan_generator.create_plan(timeframe=5)
        stats = self.database_gateway.get_plans().get_statistics()
        assert stats.average_plan_duration_in_days == Decimal(4)

    def test_with_one_active_plan_the_total_planned_costs_is_exactly_that_plans_cost(
        self,
    ) -> None:
        expected_costs = ProductionCosts(
            labour_cost=Decimal(4), resource_cost=Decimal(3), means_cost=Decimal(5)
        )
        self.plan_generator.create_plan(costs=expected_costs)
        stats = self.database_gateway.get_plans().get_statistics()
        assert stats.total_planned_costs == expected_costs

    def test_with_two_active_plans_the_total_planned_costs_is_exactly_the_sum_of_plans_costs(
        self,
    ) -> None:
        self.plan_generator.create_plan(
            costs=ProductionCosts(
                means_cost=Decimal(2),
                resource_cost=Decimal(6),
                labour_cost=Decimal(8),
            )
        )
        self.plan_generator.create_plan(
            costs=ProductionCosts(
                means_cost=Decimal(3),
                resource_cost=Decimal(7),
                labour_cost=Decimal(9),
            )
        )
        stats = self.database_gateway.get_plans().get_statistics()
        assert stats.total_planned_costs == ProductionCosts(
            means_cost=Decimal(5),
            resource_cost=Decimal(13),
            labour_cost=Decimal(17),
        )


class ThatWereActivatedBeforeTests(FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.database_gateway = self.injector.get(DatabaseGatewayImpl)
        self.plan_generator = self.injector.get(PlanGenerator)
        self.datetime_service = self.injector.get(FakeDatetimeService)

    def test_plan_activated_before_a_specified_timestamp_are_included_in_the_result(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        self.plan_generator.create_plan()
        assert self.database_gateway.get_plans().that_were_activated_before(
            datetime(2000, 1, 2)
        )

    def test_plan_activated_exactly_at_a_specified_timestamp_are_included_in_the_result(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        self.plan_generator.create_plan()
        assert self.database_gateway.get_plans().that_were_activated_before(
            datetime(2000, 1, 1)
        )

    def test_plan_activated_after_a_specified_timestamp_are_excluded_from_result(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        self.plan_generator.create_plan()
        assert not self.database_gateway.get_plans().that_were_activated_before(
            datetime(1999, 12, 31)
        )


class ThatWillExpireAfterTests(FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.database_gateway = self.injector.get(DatabaseGatewayImpl)
        self.plan_generator = self.injector.get(PlanGenerator)
        self.datetime_service = self.injector.get(FakeDatetimeService)

    def test_that_plan_that_will_expire_after_specified_date_is_included_in_results(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        self.plan_generator.create_plan(timeframe=1)
        assert self.database_gateway.get_plans().that_will_expire_after(
            datetime(2000, 1, 1)
        )

    def test_that_plan_that_will_expire_exactly_at_specified_timestamp_is_not_included_in_results(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        self.plan_generator.create_plan(timeframe=1)
        assert not self.database_gateway.get_plans().that_will_expire_after(
            datetime(2000, 1, 2)
        )

    def test_plan_that_will_expire_before_specified_timestamp_is_not_included_in_result(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        self.plan_generator.create_plan(timeframe=1)
        assert not self.database_gateway.get_plans().that_will_expire_after(
            datetime(2000, 1, 3)
        )


class ThatAreExpiredAsOfTests(FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.database_gateway = self.injector.get(DatabaseGatewayImpl)
        self.plan_generator = self.injector.get(PlanGenerator)
        self.datetime_service = self.injector.get(FakeDatetimeService)

    def test_that_plan_that_will_expire_after_specified_date_is_not_included_in_results(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        self.plan_generator.create_plan(timeframe=1)
        assert not self.database_gateway.get_plans().that_are_expired_as_of(
            datetime(2000, 1, 1)
        )

    def test_that_plan_that_will_expire_exactly_at_specified_timestamp_is_included_in_results(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        self.plan_generator.create_plan(timeframe=1)
        assert self.database_gateway.get_plans().that_are_expired_as_of(
            datetime(2000, 1, 2)
        )

    def test_plan_that_will_expire_before_specified_timestamp_is_included_in_result(
        self,
    ) -> None:
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        self.plan_generator.create_plan(timeframe=1)
        assert self.database_gateway.get_plans().that_are_expired_as_of(
            datetime(2000, 1, 3)
        )


class ThatAreNotHiddenTests(FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.database_gateway = self.injector.get(DatabaseGatewayImpl)
        self.plan_generator = self.injector.get(PlanGenerator)

    def test_that_plan_that_is_not_hidden_will_show_in_results(self) -> None:
        self.plan_generator.create_plan()
        assert self.database_gateway.get_plans().that_are_not_hidden()

    def test_that_plan_that_is_hidden_is_not_in_result_set(self) -> None:
        self.plan_generator.create_plan()
        self.database_gateway.get_plans().update().hide().perform()
        assert not self.database_gateway.get_plans().that_are_not_hidden()


class JoinedWithPlannerAndCooperatingPlansTests(FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.database_gateway = self.injector.get(DatabaseGatewayImpl)
        self.plan_generator = self.injector.get(PlanGenerator)
        self.cooperation_generator = self.injector.get(CooperationGenerator)
        self.datetime_service = self.injector.get(DatetimeService)  # type: ignore

    def test_that_one_result_is_yieled_with_one_cooperating_plan_in_db(self) -> None:
        cooperation = self.cooperation_generator.create_cooperation()
        self.plan_generator.create_plan(cooperation=cooperation)
        assert (
            len(
                self.database_gateway.get_plans().joined_with_planner_and_cooperating_plans(
                    self.datetime_service.now()
                )
            )
            == 1
        )

    def test_that_two_results_are_yieled_with_two_cooperating_plans_in_db(self) -> None:
        cooperation = self.cooperation_generator.create_cooperation()
        self.plan_generator.create_plan(cooperation=cooperation)
        self.plan_generator.create_plan(cooperation=cooperation)
        assert (
            len(
                self.database_gateway.get_plans().joined_with_planner_and_cooperating_plans(
                    self.datetime_service.now()
                )
            )
            == 2
        )

    def test_that_each_plan_has_two_cooperating_plans_in_result_with_two_plans_in_cooperation(
        self,
    ) -> None:
        cooperation = self.cooperation_generator.create_cooperation()
        self.plan_generator.create_plan(cooperation=cooperation)
        self.plan_generator.create_plan(cooperation=cooperation)
        results = (
            self.database_gateway.get_plans().joined_with_planner_and_cooperating_plans(
                self.datetime_service.now()
            )
        )
        assert results
        for v in results:
            assert len(v[2]) == 2

    def test_that_production_costs_for_cooperating_plans_are_as_they_were_created(
        self,
    ) -> None:
        cooperation = self.cooperation_generator.create_cooperation()
        self.plan_generator.create_plan(
            cooperation=cooperation,
            costs=records.ProductionCosts(
                means_cost=Decimal(1),
                resource_cost=Decimal(2),
                labour_cost=Decimal(3),
            ),
        )
        results = (
            self.database_gateway.get_plans().joined_with_planner_and_cooperating_plans(
                self.datetime_service.now()
            )
        )
        assert results
        for v in results:
            assert v[2][0].production_costs == Decimal(6)

    def test_that_amount_for_cooperating_plans_are_as_they_were_created(
        self,
    ) -> None:
        cooperation = self.cooperation_generator.create_cooperation()
        self.plan_generator.create_plan(cooperation=cooperation, amount=123)
        results = (
            self.database_gateway.get_plans().joined_with_planner_and_cooperating_plans(
                self.datetime_service.now()
            )
        )
        assert results
        for v in results:
            assert v[2][0].amount == 123

    def test_that_duration_for_cooperating_plans_are_as_they_were_created(
        self,
    ) -> None:
        cooperation = self.cooperation_generator.create_cooperation()
        self.plan_generator.create_plan(cooperation=cooperation, timeframe=234)
        results = (
            self.database_gateway.get_plans().joined_with_planner_and_cooperating_plans(
                self.datetime_service.now()
            )
        )
        assert results
        for v in results:
            assert v[2][0].duration_in_days == 234

    def test_that_no_plan_is_cooperating_with_two_plans_that_are_not_in_coop(
        self,
    ) -> None:
        self.plan_generator.create_plan()
        self.plan_generator.create_plan()
        results = (
            self.database_gateway.get_plans().joined_with_planner_and_cooperating_plans(
                self.datetime_service.now()
            )
        )
        assert results
        for v in results:
            assert not v[2]


class JoinedWithProvidedProductAmountTests(FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.database_gateway = self.injector.get(DatabaseGatewayImpl)
        self.plan_generator = self.injector.get(PlanGenerator)
        self.consumption_generator = self.injector.get(ConsumptionGenerator)
        self.control_thresholds = self.injector.get(ControlThresholdsTestImpl)
        self.control_thresholds.set_allowed_overdraw_of_member_account(10000)

    @parameterized.expand(
        [
            ([], [], 0),
            ([1], [], 1),
            ([1, 2], [], 3),
            ([], [1], 1),
            ([1], [2], 3),
            ([1, 1], [1, 1], 4),
        ]
    )
    def test_that_after_some_consumptions_the_correct_amount_of_provided_product_is_calculated(
        self,
        productive_consumptions: List[int],
        private_consumptions: List[int],
        expected_amount: int,
    ) -> None:
        plan = self.plan_generator.create_plan()
        for amount in productive_consumptions:
            self.consumption_generator.create_fixed_means_consumption(
                plan=plan, amount=amount
            )
        for amount in private_consumptions:
            self.consumption_generator.create_private_consumption(
                plan=plan, amount=amount
            )
        result = (
            self.database_gateway.get_plans()
            .joined_with_provided_product_amount()
            .first()
        )
        assert result
        _, queried_amount = result
        assert queried_amount == expected_amount

    @parameterized.expand(
        [
            ([], [], 0),
            ([1], [2], 3),
        ]
    )
    def test_provided_product_amount_is_correct_even_with_other_plans_having_consumptions_too(
        self,
        productive_consumptions: List[int],
        private_consumptions: List[int],
        expected_amount: int,
    ) -> None:
        plan = self.plan_generator.create_plan()
        self.consumption_generator.create_fixed_means_consumption()
        self.consumption_generator.create_private_consumption()
        for amount in productive_consumptions:
            self.consumption_generator.create_fixed_means_consumption(
                plan=plan, amount=amount
            )
        for amount in private_consumptions:
            self.consumption_generator.create_private_consumption(
                plan=plan, amount=amount
            )
        result = (
            self.database_gateway.get_plans()
            .with_id(plan)
            .joined_with_provided_product_amount()
            .first()
        )
        assert result
        _, queried_amount = result
        assert queried_amount == expected_amount


class ThatRequestCooperationWithCoordinatorTests(FlaskTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.company_generator = self.injector.get(CompanyGenerator)
        self.database_gateway = self.injector.get(DatabaseGatewayImpl)
        self.plan_generator = self.injector.get(PlanGenerator)
        self.datetime_service = self.injector.get(FakeDatetimeService)
        self.cooperation_generator = self.injector.get(CooperationGenerator)

    def test_possible_to_set_and_unset_requested_cooperation_attribute(self):
        cooperation = self.cooperation_generator.create_cooperation()
        plan = self.plan_generator.create_plan()
        plan_result = self.database_gateway.get_plans().with_id(plan)
        plan_result.update().set_requested_cooperation(cooperation).perform()
        assert plan_result.that_request_cooperation_with_coordinator()
        plan_result.update().set_requested_cooperation(None).perform()
        assert not plan_result.that_request_cooperation_with_coordinator()

    def test_correct_inbound_requests_are_returned(self) -> None:
        coordinator = self.company_generator.create_company()
        coop = self.cooperation_generator.create_cooperation(coordinator=coordinator)
        requesting_plan1 = self.plan_generator.create_plan(requested_cooperation=coop)
        requesting_plan2 = self.plan_generator.create_plan(requested_cooperation=coop)
        other_coop = self.cooperation_generator.create_cooperation()
        self.plan_generator.create_plan(requested_cooperation=other_coop)
        inbound_requests = (
            self.database_gateway.get_plans().that_request_cooperation_with_coordinator(
                coordinator
            )
        )
        assert len(inbound_requests) == 2
        assert requesting_plan1 in map(lambda p: p.id, inbound_requests)
        assert requesting_plan2 in map(lambda p: p.id, inbound_requests)

    def test_that_plans_where_coordination_was_passed_on_are_ignored(self) -> None:
        self.datetime_service.freeze_time(datetime(2000, 1, 1))
        original_coordinator = self.company_generator.create_company()
        new_coordinator = self.company_generator.create_company()
        cooperation = self.cooperation_generator.create_cooperation(
            coordinator=original_coordinator
        )
        self.datetime_service.advance_time(timedelta(days=1))
        self.database_gateway.create_coordination_tenure(
            company=new_coordinator,
            cooperation=cooperation,
            start_date=self.datetime_service.now(),
        )
        self.datetime_service.advance_time(timedelta(days=1))
        self.plan_generator.create_plan(requested_cooperation=cooperation)
        assert not self.database_gateway.get_plans().that_request_cooperation_with_coordinator(
            original_coordinator
        )
