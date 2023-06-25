from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from arbeitszeit.datetime_service import DatetimeService
from arbeitszeit.password_hasher import PasswordHasher
from arbeitszeit.repositories import DatabaseGateway


@dataclass
class RegisterAccountantUseCase:
    @dataclass
    class Request:
        email: str
        name: str
        password: str

    @dataclass
    class Response:
        is_accepted: bool
        user_id: Optional[UUID]
        email_address: str

    password_hasher: PasswordHasher
    database: DatabaseGateway
    datetime_service: DatetimeService

    def register_accountant(self, request: Request) -> Response:
        accountants = self.database.get_accountants()
        if accountants.with_email_address(request.email):
            return self._failed_registration(request)
        if not self.database.get_email_addresses().with_address(request.email):
            self.database.create_email_address(
                address=request.email,
                confirmed_on=self.datetime_service.now(),
            )
        else:
            self.database.get_email_addresses().with_address(
                request.email
            ).update().set_confirmation_timestamp(self.datetime_service.now()).perform()
        user_id = self.database.create_accountant(
            email=request.email,
            name=request.name,
            password_hash=self.password_hasher.calculate_password_hash(
                request.password
            ),
        )
        return self.Response(
            is_accepted=True, user_id=user_id, email_address=request.email
        )

    def _failed_registration(self, request: Request) -> Response:
        return self.Response(
            is_accepted=False,
            user_id=None,
            email_address=request.email,
        )
