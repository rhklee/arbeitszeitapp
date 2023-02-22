from decimal import Decimal

from arbeitszeit.entities import PurposesOfPurchases
from arbeitszeit.use_cases.query_purchases import QueryPurchases
from arbeitszeit_web.presenters.company_purchases_presenter import (
    CompanyPurchasesPresenter,
    ViewModel,
)
from tests.data_generators import CompanyGenerator, MemberGenerator, PurchaseGenerator
from tests.datetime_service import FakeDatetimeService
from tests.presenters.base_test_case import BaseTestCase
from tests.presenters.dependency_injection import get_dependency_injector
from tests.translator import FakeTranslator


class TestPresenter(BaseTestCase):
    def setUp(self) -> None:
        self.injector = get_dependency_injector()
        self.query_purchases = self.injector.get(QueryPurchases)
        self.member_generator = self.injector.get(MemberGenerator)
        self.purchase_generator = self.injector.get(PurchaseGenerator)
        self.company_generator = self.injector.get(CompanyGenerator)
        self.datetime_service = self.injector.get(FakeDatetimeService)
        self.translator = self.injector.get(FakeTranslator)

    def test_show_purchases_from_member(self):
        presenter = self.injector.get(CompanyPurchasesPresenter)  # DUT

        now = self.datetime_service.now()

        member = self.member_generator.create_member_entity()

        self.purchase_generator.create_purchase_by_member(
            buyer=member,
            purchase_date=now,
            amount=123,
            price_per_unit=Decimal(7),
        )
        self.purchase_generator.create_purchase_by_member(
            buyer=member,
            purchase_date=now,
            amount=2,
            price_per_unit=Decimal(70),
        )

        presentation = presenter.present(self.query_purchases(member))  # DUT

        assert isinstance(presentation, ViewModel)

        assert presentation.purchases[
            0
        ].purchase_date == FakeDatetimeService().format_datetime(
            now, zone="Europe/Berlin"
        )
        assert presentation.purchases[0].product_name == "Produkt A"
        assert (
            presentation.purchases[0].product_description
            == "Beschreibung für Produkt A."
        )
        assert presentation.purchases[0].purpose == self.translator.gettext(
            "Consumption"
        )
        assert presentation.purchases[0].price_per_unit == "7.00"
        assert presentation.purchases[0].amount == "123"
        assert presentation.purchases[0].price_total == "861.00"

        assert presentation.purchases[
            1
        ].purchase_date == FakeDatetimeService().format_datetime(
            now, zone="Europe/Berlin"
        )
        assert presentation.purchases[1].product_name == "Produkt A"
        assert (
            presentation.purchases[1].product_description
            == "Beschreibung für Produkt A."
        )
        assert presentation.purchases[1].purpose == self.translator.gettext(
            "Consumption"
        )
        assert presentation.purchases[1].price_per_unit == "70.00"
        assert presentation.purchases[1].amount == "2"
        assert presentation.purchases[1].price_total == "140.00"

    def test_show_purchases_from_company(self):
        presenter = self.injector.get(CompanyPurchasesPresenter)  # DUT

        now = self.datetime_service.now()

        company = self.company_generator.create_company_entity()
        self.purchase_generator.create_purchase_by_company(
            buyer=company,
            purchase_date=now,
            amount=321,
            price_per_unit=Decimal(7.89),
            purpose=PurposesOfPurchases.raw_materials,
        )

        self.purchase_generator.create_purchase_by_company(
            buyer=company,
            purchase_date=now,
            amount=1,
            price_per_unit=Decimal(100000),
            purpose=PurposesOfPurchases.means_of_prod,
        )

        presentation = presenter.present(self.query_purchases(company))  # DUT

        assert isinstance(presentation, ViewModel)

        assert presentation.purchases[
            0
        ].purchase_date == FakeDatetimeService().format_datetime(
            now, zone="Europe/Berlin"
        )
        assert presentation.purchases[0].product_name == "Produkt A"
        assert (
            presentation.purchases[0].product_description
            == "Beschreibung für Produkt A."
        )
        assert presentation.purchases[0].purpose == self.translator.gettext(
            "Liquid means of production"
        )
        assert presentation.purchases[0].price_per_unit == "7.89"
        assert presentation.purchases[0].amount == "321"
        assert presentation.purchases[0].price_total == "2532.69"

        assert presentation.purchases[
            1
        ].purchase_date == FakeDatetimeService().format_datetime(
            now, zone="Europe/Berlin"
        )
        assert presentation.purchases[1].product_name == "Produkt A"
        assert (
            presentation.purchases[1].product_description
            == "Beschreibung für Produkt A."
        )
        assert presentation.purchases[1].purpose == self.translator.gettext(
            "Fixed means of production"
        )
        assert presentation.purchases[1].price_per_unit == "100000.00"
        assert presentation.purchases[1].amount == "1"
        assert presentation.purchases[1].price_total == "100000.00"
