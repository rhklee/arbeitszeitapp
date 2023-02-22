from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterator, Union
from uuid import UUID

from arbeitszeit.entities import Company, Member, Purchase, PurposesOfPurchases
from arbeitszeit.repositories import PlanRepository, PurchaseRepository


@dataclass
class PurchaseQueryResponse:
    purchase_date: datetime
    plan_id: UUID
    product_name: str
    product_description: str
    purpose: PurposesOfPurchases
    price_per_unit: Decimal
    amount: int
    price_total: Decimal


@dataclass
class QueryPurchases:
    purchase_repository: PurchaseRepository
    plan_repository: PlanRepository

    def __call__(
        self,
        user: Union[Member, Company],
    ) -> Iterator[PurchaseQueryResponse]:
        purchases = self.purchase_repository.get_purchases()
        if isinstance(user, Member):
            purchases = purchases.where_buyer_is_member(member=user.id)
        else:
            purchases = purchases.where_buyer_is_company(company=user.id)
        return (
            self._purchase_to_response_model(purchase)
            for purchase in purchases.ordered_by_creation_date(ascending=False)
        )

    def _purchase_to_response_model(self, purchase: Purchase) -> PurchaseQueryResponse:
        plan = self.plan_repository.get_plans().with_id(purchase.plan).first()
        assert plan
        return PurchaseQueryResponse(
            purchase_date=purchase.purchase_date,
            plan_id=purchase.plan,
            product_name=plan.prd_name,
            product_description=plan.description,
            purpose=purchase.purpose,
            price_per_unit=purchase.price_per_unit,
            amount=purchase.amount,
            price_total=purchase.price_per_unit * purchase.amount,
        )
