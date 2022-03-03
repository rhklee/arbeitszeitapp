from dataclasses import dataclass

from arbeitszeit.use_cases import StatisticsResponse
from arbeitszeit_web.translator import Translator


@dataclass
class GetStatisticsViewModel:
    registered_companies_count: str
    registered_members_count: str
    active_plans_count: str
    active_plans_public_count: str
    average_timeframe_days: str
    planned_work_hours: str
    planned_resources_hours: str
    planned_means_hours: str


@dataclass
class GetStatisticsPresenter:
    translator: Translator

    def present(self, use_case_response: StatisticsResponse) -> GetStatisticsViewModel:
        average_timeframe = self.translator.ngettext(
            "%(num).2f day", "%(num).2f days", use_case_response.avg_timeframe
        )
        planned_work = self.translator.ngettext(
            "%(num).2f hour", "%(num).2f hours", use_case_response.planned_work
        )
        planned_liquid_means = self.translator.ngettext(
            "%(num).2f hour", "%(num).2f hours", use_case_response.planned_resources
        )
        planned_fixed_means = self.translator.ngettext(
            "%(num).2f hour", "%(num).2f hours", use_case_response.planned_means
        )
        return GetStatisticsViewModel(
            planned_resources_hours=planned_liquid_means,
            planned_work_hours=planned_work,
            planned_means_hours=planned_fixed_means,
            registered_companies_count=str(
                use_case_response.registered_companies_count
            ),
            registered_members_count=str(use_case_response.registered_members_count),
            active_plans_count=str(use_case_response.active_plans_count),
            active_plans_public_count=str(use_case_response.active_plans_public_count),
            average_timeframe_days=average_timeframe,
        )
