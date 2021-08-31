import enum
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional
from uuid import UUID

from injector import inject

from arbeitszeit.entities import ProductOffer
from arbeitszeit.repositories import OfferRepository


class ProductFilter(enum.Enum):
    by_name = enum.auto()
    by_description = enum.auto()


@dataclass
class ProductQueryResponse:
    offer_id: UUID
    seller_name: str
    seller_email: str
    plan_id: UUID
    product_name: str
    product_description: str
    price_per_unit: Decimal
    is_public_service: bool


@inject
@dataclass
class QueryProducts:
    offer_repository: OfferRepository

    def __call__(
        self, query: Optional[str], filter_by: ProductFilter
    ) -> Iterable[ProductQueryResponse]:
        if query is None:
            found_offers = self.offer_repository.all_active_offers()
        elif filter_by == ProductFilter.by_name:
            found_offers = self.offer_repository.query_offers_by_name(query)
        else:
            found_offers = self.offer_repository.query_offers_by_description(query)
        return (self._offer_to_response_model(offer) for offer in found_offers)

    def _offer_to_response_model(self, offer: ProductOffer) -> ProductQueryResponse:
        return ProductQueryResponse(
            offer_id=offer.id,
            seller_name=offer.plan.planner.name,
            seller_email=offer.plan.planner.email,
            plan_id=offer.plan.id,
            product_name=offer.name,
            product_description=offer.description,
            price_per_unit=offer.price_per_unit(),
            is_public_service=offer.plan.is_public_service,
        )
