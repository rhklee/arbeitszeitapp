"""Business logic"""

from . import sql


class SocialAccounting:
    def check_plan(self):
        pass

    def grant_credits_to_company(self):
        pass

    def publish_products(self):
        pass


class Company:
    def add_new_worker(self, user_id, company_id):
        """add new workers to company."""
        sql.add_new_worker_to_company(user_id, company_id)

    def buy_product(self, buyer_type, product, buyer):
        sql.kaufen(buyer_type, product, buyer)

    def delete_product(self, product):
        """delete own product from catalog."""
        sql.delete_product(product)

    def send_plan(self, p, r, a, prd_name, prd_unit, prd_amount, timeframe):
        """send plan."""
        accounting.check_plan()
        accounting.grant_credits_to_company()
        accounting.publish_products()


accounting = SocialAccounting()
company = Company()
