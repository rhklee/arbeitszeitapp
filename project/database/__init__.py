from __future__ import annotations

from datetime import date, datetime, timedelta
from functools import wraps

from flask_sqlalchemy import SQLAlchemy
from injector import (
    Binder,
    CallableProvider,
    ClassProvider,
    Injector,
    InstanceProvider,
    inject,
)

from arbeitszeit import entities
from arbeitszeit import repositories as interfaces
from arbeitszeit.datetime_service import DatetimeService
from project.extensions import db
from project.models import Company, Member

from .repositories import (
    AccountingRepository,
    AccountOwnerRepository,
    AccountRepository,
    CompanyRepository,
    CompanyWorkerRepository,
    MemberRepository,
    PlanRepository,
    ProductOfferRepository,
    PurchaseRepository,
    TransactionRepository,
)

__all__ = [
    "AccountRepository",
    "AccountingRepository",
    "CompanyRepository",
    "CompanyWorkerRepository",
    "MemberRepository",
    "PlanRepository",
    "ProductOfferRepository",
    "PurchaseRepository",
    "TransactionRepository",
    "commit_changes",
    "get_company_by_mail",
    "with_injection",
]


def configure_injector(binder: Binder) -> None:
    binder.bind(
        interfaces.OfferRepository,  # type: ignore
        to=ClassProvider(ProductOfferRepository),
    )
    binder.bind(
        interfaces.TransactionRepository,  # type: ignore
        to=ClassProvider(TransactionRepository),
    )
    binder.bind(
        interfaces.CompanyWorkerRepository,  # type: ignore
        to=ClassProvider(CompanyWorkerRepository),
    )
    binder.bind(
        interfaces.PurchaseRepository,  # type: ignore
        to=ClassProvider(PurchaseRepository),
    )
    binder.bind(
        entities.SocialAccounting,
        to=CallableProvider(get_social_accounting),
    )
    binder.bind(
        interfaces.AccountRepository,  # type: ignore
        to=ClassProvider(AccountRepository),
    )
    binder.bind(
        interfaces.MemberRepository,  # type: ignore
        to=ClassProvider(MemberRepository),
    )
    binder.bind(
        interfaces.CompanyRepository,  # type: ignore
        to=ClassProvider(CompanyRepository),
    )
    binder.bind(
        interfaces.PurchaseRepository,  # type: ignore
        to=ClassProvider(PurchaseRepository),
    )
    binder.bind(
        interfaces.PlanRepository,  # type: ignore
        to=ClassProvider(PlanRepository),
    )
    binder.bind(
        interfaces.AccountOwnerRepository,  # type: ignore
        to=ClassProvider(AccountOwnerRepository),
    )
    binder.bind(
        interfaces.OfferRepository,  # type: ignore
        to=ClassProvider(ProductOfferRepository),
    )
    binder.bind(
        DatetimeService,  # type: ignore
        to=ClassProvider(RealtimeDatetimeService),
    )
    binder.bind(
        SQLAlchemy,
        to=InstanceProvider(db),
    )


class RealtimeDatetimeService(DatetimeService):
    def now(self) -> datetime:
        return datetime.now()

    def today(self) -> date:
        return datetime.today()

    def past_plan_activation_date(self, timedelta_days: int = 1) -> datetime:
        if self.now().hour < self.time_of_plan_activation:
            past_day = self.today() - timedelta(days=timedelta_days)
            past_date = datetime(
                past_day.year,
                past_day.month,
                past_day.day,
                hour=self.time_of_plan_activation,
            )
        else:
            past_day = self.today() - timedelta(days=timedelta_days - 1)
            past_date = datetime(
                past_day.year,
                past_day.month,
                past_day.day,
                hour=self.time_of_plan_activation,
            )
        return past_date


@inject
def get_social_accounting(
    accounting_repo: AccountingRepository,
) -> entities.SocialAccounting:
    return accounting_repo.get_or_create_social_accounting()


_injector = Injector(configure_injector)


def with_injection(original_function):
    """When you wrap a function, make sure that the parameters to be
    injected come after the the parameters that the caller should
    provide.
    """

    @wraps(original_function)
    def wrapped_function(*args, **kwargs):
        return _injector.call_with_injection(
            inject(original_function), args=args, kwargs=kwargs
        )

    return wrapped_function


def commit_changes():
    db.session.commit()


# User


def get_user_by_mail(email) -> Member:
    """returns first user in User, filtered by email."""
    member = Member.query.filter_by(email=email).first()
    return member


# Company


def get_company_by_mail(email) -> Company:
    """returns first company in Company, filtered by mail."""
    company = Company.query.filter_by(email=email).first()
    return company
