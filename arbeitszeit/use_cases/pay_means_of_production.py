from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Tuple
from uuid import UUID

from arbeitszeit.datetime_service import DatetimeService
from arbeitszeit.entities import Company, Plan, PurposesOfPurchases
from arbeitszeit.price_calculator import PriceCalculator
from arbeitszeit.repositories import (
    CompanyRepository,
    PlanRepository,
    PurchaseRepository,
    TransactionRepository,
)


@dataclass
class PayMeansOfProductionRequest:
    buyer: UUID
    plan: UUID
    amount: int
    purpose: PurposesOfPurchases


@dataclass
class PayMeansOfProductionResponse:
    class RejectionReason(Exception, Enum):
        plan_not_found = auto()
        invalid_purpose = auto()
        cannot_buy_public_service = auto()
        plan_is_not_active = auto()
        buyer_is_planner = auto()

    rejection_reason: Optional[RejectionReason]

    @property
    def is_rejected(self) -> bool:
        return self.rejection_reason is not None


@dataclass(frozen=True)
class PayMeansOfProduction:
    plan_repository: PlanRepository
    company_repository: CompanyRepository
    price_calculator: PriceCalculator
    purchase_repository: PurchaseRepository
    datetime_service: DatetimeService
    transaction_repository: TransactionRepository

    def __call__(
        self, request: PayMeansOfProductionRequest
    ) -> PayMeansOfProductionResponse:
        try:
            plan, buyer, purpose = self._validate_request(request)
        except PayMeansOfProductionResponse.RejectionReason as reason:
            return PayMeansOfProductionResponse(rejection_reason=reason)
        self.record_purchase(
            plan=plan, amount=request.amount, purpose=request.purpose, buyer_id=buyer.id
        )
        self.create_transaction(
            buyer=buyer, plan=plan, amount=request.amount, purpose=purpose
        )
        return PayMeansOfProductionResponse(rejection_reason=None)

    def _validate_request(
        self, request: PayMeansOfProductionRequest
    ) -> Tuple[Plan, Company, PurposesOfPurchases]:
        plan = self._validate_plan(request)
        return (
            plan,
            self._validate_buyer_is_not_planner(request, plan),
            self._validate_purpose(request),
        )

    def _validate_plan(self, request: PayMeansOfProductionRequest) -> Plan:
        plan = self.plan_repository.get_plans().with_id(request.plan).first()
        if plan is None:
            raise PayMeansOfProductionResponse.RejectionReason.plan_not_found
        if not plan.is_active:
            raise PayMeansOfProductionResponse.RejectionReason.plan_is_not_active
        if plan.is_public_service:
            raise PayMeansOfProductionResponse.RejectionReason.cannot_buy_public_service
        return plan

    def _validate_buyer_is_not_planner(
        self, request: PayMeansOfProductionRequest, plan: Plan
    ) -> Company:
        if plan.planner == request.buyer:
            raise PayMeansOfProductionResponse.RejectionReason.buyer_is_planner
        buyer = self.company_repository.get_companies().with_id(request.buyer).first()
        assert buyer is not None
        return buyer

    def _validate_purpose(
        self, request: PayMeansOfProductionRequest
    ) -> PurposesOfPurchases:
        if request.purpose not in (
            PurposesOfPurchases.means_of_prod,
            PurposesOfPurchases.raw_materials,
        ):
            raise PayMeansOfProductionResponse.RejectionReason.invalid_purpose
        return request.purpose

    def record_purchase(
        self, plan: Plan, amount: int, purpose: PurposesOfPurchases, buyer_id: UUID
    ) -> None:
        price_per_unit = self.price_calculator.calculate_cooperative_price(plan)
        self.purchase_repository.create_purchase_by_company(
            purchase_date=self.datetime_service.now(),
            plan=plan.id,
            buyer=buyer_id,
            price_per_unit=price_per_unit,
            amount=amount,
            purpose=purpose,
        )

    def create_transaction(
        self, amount: int, purpose: PurposesOfPurchases, buyer: Company, plan: Plan
    ) -> None:
        coop_price = amount * self.price_calculator.calculate_cooperative_price(plan)
        individual_price = amount * self.price_calculator.calculate_individual_price(
            plan
        )
        if purpose == PurposesOfPurchases.means_of_prod:
            sending_account = buyer.means_account
        elif purpose == PurposesOfPurchases.raw_materials:
            sending_account = buyer.raw_material_account
        planner = self.company_repository.get_companies().with_id(plan.planner).first()
        assert planner
        self.transaction_repository.create_transaction(
            date=self.datetime_service.now(),
            sending_account=sending_account,
            receiving_account=planner.product_account,
            amount_sent=coop_price,
            amount_received=individual_price,
            purpose=f"Plan-Id: {plan.id}",
        )
