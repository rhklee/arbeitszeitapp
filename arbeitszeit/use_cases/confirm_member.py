from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from arbeitszeit.repositories import DatabaseGateway


@dataclass
class ConfirmMemberUseCase:
    @dataclass
    class Request:
        email_address: str

    @dataclass
    class Response:
        is_confirmed: bool
        member: Optional[UUID] = None

    database: DatabaseGateway

    def confirm_member(self, request: Request) -> Response:
        record = (
            self.database.get_members()
            .with_email_address(request.email_address)
            .joined_with_email_address()
            .first()
        )
        if not record:
            return self.Response(is_confirmed=False)
        member, email = record
        if email.confirmed_on:
            return self.Response(is_confirmed=False, member=None)
        else:
            self.database.get_email_addresses().with_address(
                request.email_address
            ).update().set_confirmation_timestamp(datetime.min).perform()
            return self.Response(is_confirmed=True, member=member.id)
