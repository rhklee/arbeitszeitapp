from tests.flask_integration.flask import ViewTestCase


class AnonymousUserTest(ViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.url = "/member/dashboard"

    def test_anonymous_user_gets_302(
        self,
    ):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_anonymous_user_gets_redirected_to_start_with_next_url_set_correctly(
        self,
    ):
        response = self.client.get(self.url)
        self.assertEqual(response.location, "/?next=%2Fmember%2Fdashboard")


class CompanyTest(ViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.url = "/member/dashboard"
        self.company = self.login_company(confirm_company=True)

    def test_company_gets_302(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_company_gets_redirected_to_start_page_with_next_url_set_correctly(
        self,
    ) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.location, "/?next=%2Fmember%2Fdashboard")


class UnconfirmedMemberTests(ViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.member = self.login_member(confirm_member=False)
        self.url = "/member/dashboard"

    def test_unconfirmed_member_gets_302(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_redirects_to_page_for_unconfirmed_members(self) -> None:
        response = self.client.get(self.url)
        assert response.location == "/member/unconfirmed"


class ConfirmedMemberTests(ViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.member = self.login_member(confirm_member=True)
        self.url = "/member/dashboard"

    def test_member_gets_200(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
