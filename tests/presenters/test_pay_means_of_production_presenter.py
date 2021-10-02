from unittest import TestCase

from arbeitszeit.use_cases.pay_means_of_production import PayMeansOfProductionResponse
from arbeitszeit_web.pay_means_of_production import PayMeansOfProductionPresenter


class PayMeansOfProductionTests(TestCase):
    def test_show_confirmation_when_payment_was_successful(self) -> None:
        presenter = PayMeansOfProductionPresenter()
        view_model = presenter.present(
            PayMeansOfProductionResponse(
                rejection_reason=None,
            )
        )
        self.assertIn("Erfolgreich bezahlt.", view_model.notifications)

    def test_missing_plan_show_correct_notification(self) -> None:
        presenter = PayMeansOfProductionPresenter()
        view_model = presenter.present(
            PayMeansOfProductionResponse(
                rejection_reason=PayMeansOfProductionResponse.RejectionReason.plan_not_found,
            )
        )
        self.assertIn("Plan existiert nicht.", view_model.notifications)

    def test_invalid_purpose_shows_correct_notification(self) -> None:
        presenter = PayMeansOfProductionPresenter()
        view_model = presenter.present(
            PayMeansOfProductionResponse(
                rejection_reason=PayMeansOfProductionResponse.RejectionReason.invalid_purpose,
            )
        )
        self.assertIn(
            "Der angegebene Verwendungszweck is ungültig.", view_model.notifications
        )
