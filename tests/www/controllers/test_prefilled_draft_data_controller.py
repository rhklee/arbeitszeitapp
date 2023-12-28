from decimal import Decimal
from uuid import uuid4

from arbeitszeit.use_cases.create_plan_draft import Request
from arbeitszeit_web.www.controllers.create_draft_controller import (
    CreateDraftController,
)
from tests.forms import DraftForm
from tests.www.base_test_case import BaseTestCase


class ControllerTests(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.controller = self.injector.get(CreateDraftController)
        self.fake_form = DraftForm(
            prd_name="test name",
            description="test description",
            timeframe=14,
            prd_unit="1 piece",
            prd_amount=10,
            costs_p=Decimal("10.5"),
            costs_r=Decimal("15"),
            costs_a=Decimal("20"),
            is_public_service=True,
        )
        self.session.login_company(uuid4())

    def test_import_of_data_returns_a_request_object(self):
        request = self.controller.import_form_data(self.fake_form)
        assert isinstance(request, Request)

    def test_import_of_data_transforms_prd_name_string_to_correct_string(self):
        request = self.controller.import_form_data(self.fake_form)
        assert request.product_name == "test name"

    def test_import_of_data_transforms_description_string_to_correct_string(self):
        request = self.controller.import_form_data(self.fake_form)
        assert request.description == "test description"

    def test_import_of_data_transforms_timeframe_integer_to_correct_integer(self):
        request = self.controller.import_form_data(self.fake_form)
        assert request.timeframe_in_days == 14

    def test_import_of_data_transforms_prd_unit_string_to_correct_string(self):
        request = self.controller.import_form_data(self.fake_form)
        assert request.production_unit == "1 piece"

    def test_import_of_data_transforms_prd_amount_integer_to_correct_integer(self):
        request = self.controller.import_form_data(self.fake_form)
        assert request.production_amount == 10

    def test_import_of_data_transforms_cost_decimals_to_correct_decimals(self):
        request = self.controller.import_form_data(self.fake_form)
        assert request.costs.means_cost == Decimal(10.5)
        assert request.costs.resource_cost == Decimal(15)
        assert request.costs.labour_cost == Decimal(20)

    def test_import_of_data_transforms_productive_or_public_string_to_correct_bool_when_public_service(
        self,
    ):
        request = self.controller.import_form_data(self.fake_form)
        assert request.is_public_service == True

    def test_import_of_data_transforms_productive_or_public_string_to_correct_bool_when_productive(
        self,
    ):
        is_public_service_field = self.fake_form.is_public_service_field()
        is_public_service_field.value = False
        request = self.controller.import_form_data(self.fake_form)
        assert request.is_public_service == False
