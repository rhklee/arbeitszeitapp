from typing import List

from arbeitszeit.entities import ProductOffer
from arbeitszeit.use_cases import CreateOfferResponse, DeleteOffer
from tests.data_generators import OfferGenerator

from .dependency_injection import injection_test
from .repositories import OfferRepository


def offer_in_offers(offer: CreateOfferResponse, offers: List[ProductOffer]) -> bool:
    for o in offers:
        if o.id == offer.id:
            return True
    return False


@injection_test
def test_that_offer_gets_deleted(
    offer_repo: OfferRepository,
    delete_offer: DeleteOffer,
    offer_generator: OfferGenerator,
):
    offer = offer_generator.create_offer()
    assert len(offer_repo.offers) == 1
    delete_offer(offer.id)
    assert len(offer_repo.offers) == 0


@injection_test
def test_that_correct_offer_gets_deleted(
    offer_repo: OfferRepository,
    delete_offer: DeleteOffer,
    offer_generator: OfferGenerator,
):
    offer1 = offer_generator.create_offer()
    offer2 = offer_generator.create_offer()
    offer3 = offer_generator.create_offer()
    assert len(offer_repo.offers) == 3
    delete_offer(offer1.id)
    assert len(offer_repo.offers) == 2
    assert not offer_in_offers(offer1, offer_repo.offers)
    assert offer_in_offers(offer2, offer_repo.offers)
    assert offer_in_offers(offer3, offer_repo.offers)


@injection_test
def test_that_correct_offer_id_is_shown_after_deletion_of_offer(
    delete_offer: DeleteOffer,
    offer_generator: OfferGenerator,
):
    offer = offer_generator.create_offer()
    response = delete_offer(offer.id)
    assert response.offer_id == offer.id
