from dataclasses import dataclass
from decimal import Decimal
from typing import List
from uuid import UUID

from arbeitszeit.repositories import DatabaseGateway


@dataclass
class ShowMyAccountsRequest:
    current_user: UUID


@dataclass
class ShowMyAccountsResponse:
    balances: List[Decimal]


@dataclass
class ShowMyAccounts:
    database: DatabaseGateway

    def __call__(self, request: ShowMyAccountsRequest) -> ShowMyAccountsResponse:
        accounts = dict(
            (account.id, balance)
            for account, balance in self.database.get_accounts()
            .owned_by_company(request.current_user)
            .joined_with_balance()
        )
        company = self.database.get_companies().with_id(request.current_user).first()
        assert company
        balances = [
            accounts[company.means_account],
            accounts[company.raw_material_account],
            accounts[company.work_account],
            accounts[company.product_account],
        ]
        return ShowMyAccountsResponse(balances=balances)
