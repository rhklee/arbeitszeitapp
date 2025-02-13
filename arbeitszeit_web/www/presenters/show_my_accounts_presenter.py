from dataclasses import dataclass

from arbeitszeit.use_cases.show_my_accounts import ShowMyAccountsResponse


@dataclass
class ViewModel:
    balance_fixed: str
    is_fixed_positive: bool
    balance_liquid: str
    is_liquid_positive: bool
    balance_work: str
    is_work_positive: bool
    balance_product: str
    is_product_positive: bool


class ShowMyAccountsPresenter:
    def present(self, use_case_response: ShowMyAccountsResponse) -> ViewModel:
        balances = [str(round(balance, 2)) for balance in use_case_response.balances]
        signs = [balance >= 0 for balance in use_case_response.balances]

        return ViewModel(
            balance_fixed=balances[0],
            is_fixed_positive=signs[0],
            balance_liquid=balances[1],
            is_liquid_positive=signs[1],
            balance_work=balances[2],
            is_work_positive=signs[2],
            balance_product=balances[3],
            is_product_positive=signs[3],
        )
