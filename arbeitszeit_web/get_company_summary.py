from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List

from arbeitszeit.use_cases.get_company_summary import (
    GetCompanySummarySuccess,
    PlanDetails,
)
from arbeitszeit_web.translator import Translator
from arbeitszeit_web.url_index import PlanSummaryUrlIndex


@dataclass
class PlanDetailsWeb:
    id: str
    name: str
    url: str
    status: str
    sales_volume: str
    sales_balance: str
    deviation_relative: str


@dataclass
class GetCompanySummaryViewModel:
    id: str
    name: str
    email: str
    registered_on: datetime
    account_balances: List[str]
    plan_details: List[PlanDetailsWeb]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GetCompanySummarySuccessPresenter:
    plan_index: PlanSummaryUrlIndex
    translator: Translator

    def present(
        self, use_case_response: GetCompanySummarySuccess
    ) -> GetCompanySummaryViewModel:
        return GetCompanySummaryViewModel(
            id=str(use_case_response.id),
            name=use_case_response.name,
            email=use_case_response.email,
            registered_on=use_case_response.registered_on,
            account_balances=[
                "%(num).2f" % dict(num=use_case_response.account_balances.means),
                "%(num).2f" % dict(num=use_case_response.account_balances.raw_material),
                "%(num).2f" % dict(num=use_case_response.account_balances.work),
                "%(num).2f" % dict(num=use_case_response.account_balances.product),
            ],
            plan_details=[
                self._get_plan_details(plan) for plan in use_case_response.plan_details
            ],
        )

    def _get_plan_details(self, plan_details: PlanDetails) -> PlanDetailsWeb:
        return PlanDetailsWeb(
            id=str(plan_details.id),
            name=plan_details.name,
            url=self.plan_index.get_plan_summary_url(plan_details.id),
            status=self.translator.gettext("Active")
            if plan_details.is_active
            else self.translator.gettext("Inactive"),
            sales_volume=f"{round(plan_details.sales_volume, 2)}",
            sales_balance=f"{round(plan_details.sales_balance, 2)}",
            deviation_relative=f"{round(plan_details.deviation_relative)}",
        )
