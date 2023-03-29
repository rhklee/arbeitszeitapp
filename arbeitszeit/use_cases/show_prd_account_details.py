from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from itertools import accumulate
from typing import List, Optional, Union
from uuid import UUID

from arbeitszeit.entities import Company, Member
from arbeitszeit.repositories import AccountRepository, CompanyRepository
from arbeitszeit.transactions import TransactionTypes, UserAccountingService


@dataclass
class ShowPRDAccountDetailsUseCase:
    @dataclass
    class Buyer:
        buyer_is_member: bool
        buyer_id: UUID
        buyer_name: str

    @dataclass
    class TransactionInfo:
        transaction_type: TransactionTypes
        date: datetime
        transaction_volume: Decimal
        purpose: str
        buyer: Optional[ShowPRDAccountDetailsUseCase.Buyer]

    @dataclass
    class PlotDetails:
        timestamps: List[datetime]
        accumulated_volumes: List[Decimal]

    @dataclass
    class Response:
        company_id: UUID
        transactions: List[ShowPRDAccountDetailsUseCase.TransactionInfo]
        account_balance: Decimal
        plot: ShowPRDAccountDetailsUseCase.PlotDetails

    accounting_service: UserAccountingService
    company_repository: CompanyRepository
    account_repository: AccountRepository

    def __call__(self, company_id: UUID) -> Response:
        company = self.company_repository.get_companies().with_id(company_id).first()
        assert company
        transactions = [
            self.TransactionInfo(
                transaction_type=row.transaction_type,
                date=row.transaction.date,
                transaction_volume=row.volume,
                purpose=row.transaction.purpose,
                buyer=self._create_buyer_info(
                    self.accounting_service.get_buyer(
                        row.transaction_type, row.transaction
                    )
                ),
            )
            for row in self.accounting_service.get_statement_of_account(
                company, [company.product_account]
            )
        ]
        account_balance = self.account_repository.get_account_balance(
            company.product_account
        )
        plot = self.PlotDetails(
            timestamps=self._get_plot_dates(transactions),
            accumulated_volumes=self._get_plot_volumes(transactions),
        )
        return self.Response(
            company_id=company_id,
            transactions=transactions,
            account_balance=account_balance,
            plot=plot,
        )

    def _get_plot_dates(self, transactions: List[TransactionInfo]) -> List[datetime]:
        timestamps = [t.date for t in transactions]
        timestamps.reverse()
        return timestamps

    def _get_plot_volumes(self, transactions: List[TransactionInfo]) -> List[Decimal]:
        volumes = [t.transaction_volume for t in transactions]
        volumes.reverse()
        volumes_cumsum = list(accumulate(volumes))
        return volumes_cumsum

    def _create_buyer_info(
        self, buyer: Union[Company, Member, None]
    ) -> Optional[ShowPRDAccountDetailsUseCase.Buyer]:
        if not buyer:
            return None
        return self.Buyer(
            buyer_is_member=True if isinstance(buyer, Member) else False,
            buyer_id=buyer.id,
            buyer_name=buyer.get_name(),
        )
