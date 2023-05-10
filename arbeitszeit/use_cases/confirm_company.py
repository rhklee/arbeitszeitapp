from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from arbeitszeit.datetime_service import DatetimeService
from arbeitszeit.repositories import CompanyRepository


@dataclass
class ConfirmCompanyUseCase:
    @dataclass
    class Request:
        email_address: str

    @dataclass
    class Response:
        is_confirmed: bool
        user_id: Optional[UUID]

    company_repository: CompanyRepository
    datetime_service: DatetimeService

    def confirm_company(self, request: Request) -> Response:
        company = (
            self.company_repository.get_companies()
            .with_email_address(request.email_address)
            .first()
        )
        if not company:
            return self.Response(
                user_id=None,
                is_confirmed=False,
            )
        elif company.confirmed_on is None:
            self.company_repository.confirm_company(
                company.id, self.datetime_service.now()
            )
            return self.Response(is_confirmed=True, user_id=company.id)
        else:
            return self.Response(is_confirmed=False, user_id=None)
