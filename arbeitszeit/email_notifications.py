"""This module contains all possible types of email notifications that
the arbeitszeitapp can issue and the interface by which the use cases
request those notifications to be sent.
"""
from dataclasses import dataclass
from typing import Protocol, Type, Union, get_args
from uuid import UUID

from typing_extensions import TypeAlias


@dataclass
class MemberRegistration:
    email_address: str


@dataclass
class CompanyRegistration:
    email_address: str


@dataclass
class AccountantNotificationAboutNewPlan:
    product_name: str
    plan_id: UUID
    accountant_name: str
    accountant_email_address: str


@dataclass
class AccountantInvitation:
    email_address: str


@dataclass
class WorkerInvitation:
    worker_email: str
    invite: UUID


@dataclass
class EmailChangeConfirmation:
    old_email_address: str
    new_email_address: str


@dataclass
class CooperationRequestEmail:
    coordinator_email_address: str
    coordinator_name: str


@dataclass
class CoordinationTransferRequest:
    candidate_email: str
    candidate_name: str
    cooperation_name: str
    transfer_request: UUID


# This type definition can be used by implementations of the
# EmailSender protocol for static type checking purposes. Keep this
# list alphabetically sorted.
Message: TypeAlias = Union[
    AccountantInvitation,
    AccountantNotificationAboutNewPlan,
    CompanyRegistration,
    CooperationRequestEmail,
    CoordinationTransferRequest,
    EmailChangeConfirmation,
    MemberRegistration,
    WorkerInvitation,
]
# Implementations can rely on this set to contain all possible message
# types.
all_message_types: set[Type] = set(get_args(Message))


class EmailSender(Protocol):
    def send_email(self, message: Message) -> None:
        ...
