from datetime import datetime
from decimal import Decimal
from unittest import TestCase
from uuid import uuid4

from arbeitszeit.use_cases.get_company_summary import (
    AccountBalances,
    Expectations,
    GetCompanySummarySuccess,
    PlanDetails,
)
from arbeitszeit_web.get_company_summary import (
    Deviation,
    GetCompanySummarySuccessPresenter,
)
from tests.control_thresholds import ControlThresholdsTestImpl
from tests.translator import FakeTranslator

from .dependency_injection import get_dependency_injector
from .url_index import PlanSummaryUrlIndexTestImpl

RESPONSE_WITH_2_PLANS = GetCompanySummarySuccess(
    id=uuid4(),
    name="Company Name",
    email="comp_mail@cp.org",
    registered_on=datetime(2022, 1, 2),
    expectations=Expectations(
        Decimal("1"), Decimal("2"), Decimal("3"), Decimal("-4.561")
    ),
    account_balances=AccountBalances(
        Decimal("1"), Decimal("2"), Decimal("3"), Decimal("-4.561")
    ),
    deviations_relative=[
        Decimal("Infinity"),
        Decimal("20"),
        Decimal("-300"),
        Decimal("-4.561"),
    ],
    plan_details=[
        PlanDetails(
            uuid4(),
            "name_1",
            True,
            sales_volume=Decimal(5),
            sales_balance=Decimal(-5),
            deviation_relative=Decimal(-100),
        ),
        PlanDetails(
            uuid4(),
            "name_2",
            False,
            sales_volume=Decimal(2),
            sales_balance=Decimal(-4),
            deviation_relative=Decimal(-200),
        ),
    ],
)


class GetCompanySummaryPresenterTests(TestCase):
    def setUp(self) -> None:
        self.injector = get_dependency_injector()
        self.presenter = self.injector.get(GetCompanySummarySuccessPresenter)
        self.control_thresholds = self.injector.get(ControlThresholdsTestImpl)

    def test_company_id_is_shown(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(view_model.id, str(RESPONSE_WITH_2_PLANS.id))

    def test_company_name_is_shown(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(view_model.name, RESPONSE_WITH_2_PLANS.name)

    def test_company_email_is_shown(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(view_model.email, RESPONSE_WITH_2_PLANS.email)

    def test_company_register_date_is_formatted_correctly(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(view_model.registered_on, "02.01.2022")

    def test_expectations_are_shown_as_list_of_strings(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(view_model.expectations, ["1.00", "2.00", "3.00", "-4.56"])

    def test_company_account_balances_is_shown_as_list_of_strings(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(view_model.account_balances, ["1.00", "2.00", "3.00", "-4.56"])

    def test_company_relative_deviations_is_list_of_four_deviation_objects(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(len(view_model.deviations_relative), 4)
        self.assertIsInstance(view_model.deviations_relative[0], Deviation)

    def test_company_relative_deviations_shows_correct_percentages_and_critical_status(
        self,
    ):
        self.control_thresholds.set_acceptable_relative_account_deviation(20)
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        expected_percentages = ["inf", "20", "-300", "-5"]
        expected_is_critical = [True, False, True, False]
        for count, deviation in enumerate(view_model.deviations_relative):
            self.assertEqual(deviation.percentage, expected_percentages[count])
            self.assertEqual(deviation.is_critical, expected_is_critical[count])


class PlansOfCompanyTests(TestCase):
    def setUp(self) -> None:
        self.injector = get_dependency_injector()
        self.presenter = self.injector.get(GetCompanySummarySuccessPresenter)
        self.plan_index = self.injector.get(PlanSummaryUrlIndexTestImpl)
        self.translator = self.injector.get(FakeTranslator)
        self.control_thresholds = self.injector.get(ControlThresholdsTestImpl)

    def test_ids_of_plans_are_shown(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(
            view_model.plan_details[0].id,
            str(RESPONSE_WITH_2_PLANS.plan_details[0].id),
        )
        self.assertEqual(
            view_model.plan_details[1].id,
            str(RESPONSE_WITH_2_PLANS.plan_details[1].id),
        )

    def test_names_of_plans_are_shown(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(
            view_model.plan_details[0].name,
            str(RESPONSE_WITH_2_PLANS.plan_details[0].name),
        )
        self.assertEqual(
            view_model.plan_details[1].name,
            str(RESPONSE_WITH_2_PLANS.plan_details[1].name),
        )

    def test_urls_of_plans_are_shown(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(
            view_model.plan_details[0].url,
            self.plan_index.get_plan_summary_url(
                RESPONSE_WITH_2_PLANS.plan_details[0].id
            ),
        )
        self.assertEqual(
            view_model.plan_details[1].url,
            self.plan_index.get_plan_summary_url(
                RESPONSE_WITH_2_PLANS.plan_details[1].id
            ),
        )

    def test_status_of_plans_are_shown(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(
            view_model.plan_details[0].status,
            self.translator.gettext("Active"),
        )
        self.assertEqual(
            view_model.plan_details[1].status,
            self.translator.gettext("Inactive"),
        )

    def test_planned_sales_volume_and_balance_of_plans_are_shown(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(
            view_model.plan_details[0].sales_volume,
            f"{round(RESPONSE_WITH_2_PLANS.plan_details[0].sales_volume, 2)}",
        )
        self.assertEqual(
            view_model.plan_details[0].sales_balance,
            f"{round(RESPONSE_WITH_2_PLANS.plan_details[0].sales_balance, 2)}",
        )

    def test_relative_deviation_of_plan_is_shown(self):
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertEqual(
            view_model.plan_details[0].deviation_relative.percentage,
            f"{round(RESPONSE_WITH_2_PLANS.plan_details[0].deviation_relative)}",
        )

    def test_that_relative_deviation_is_marked_as_critical_if_it_exceeds_threshold(
        self,
    ):
        self.control_thresholds.set_acceptable_relative_account_deviation(33)
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertTrue(view_model.plan_details[0].deviation_relative.is_critical)

    def test_that_relative_deviation_is_not_marked_as_critical_if_it_does_not_exceed_threshold(
        self,
    ):
        self.control_thresholds.set_acceptable_relative_account_deviation(100)
        view_model = self.presenter.present(RESPONSE_WITH_2_PLANS)
        self.assertFalse(view_model.plan_details[0].deviation_relative.is_critical)
