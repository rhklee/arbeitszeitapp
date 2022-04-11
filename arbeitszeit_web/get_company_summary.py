from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List

from arbeitszeit.use_cases.get_company_summary import (
    GetCompanySummarySuccess,
    PlanDetails,
)
from arbeitszeit_web.url_index import PlanSummaryUrlIndex


@dataclass
class PlanDetailsWeb:
    id: str
    name: str
    url: str


@dataclass
class GetCompanySummaryViewModel:
    id: str
    name: str
    email: str
    registered_on: datetime
    active_plans: List[PlanDetailsWeb]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GetCompanySummarySuccessPresenter:
    plan_index: PlanSummaryUrlIndex

    def present(
        self, use_case_response: GetCompanySummarySuccess
    ) -> GetCompanySummaryViewModel:
        return GetCompanySummaryViewModel(
            str(use_case_response.id),
            use_case_response.name,
            use_case_response.email,
            use_case_response.registered_on,
            [self._get_plan_details(plan) for plan in use_case_response.active_plans],
        )

    def _get_plan_details(self, plan_details: PlanDetails) -> PlanDetailsWeb:
        return PlanDetailsWeb(
            str(plan_details.id),
            plan_details.name,
            self.plan_index.get_plan_summary_url(plan_details.id),
        )
