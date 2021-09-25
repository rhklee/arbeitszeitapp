from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from arbeitszeit import errors, use_cases
from arbeitszeit_web.get_member_profile_info import GetMemberProfileInfoPresenter
from arbeitszeit_web.get_statistics import GetStatisticsPresenter
from arbeitszeit_web.query_products import (
    QueryProductsController,
    QueryProductsPresenter,
)
from project.database import (
    AccountRepository,
    CompanyRepository,
    MemberRepository,
    PlanRepository,
    commit_changes,
)
from project.dependency_injection import with_injection
from project.forms import ProductSearchForm
from project.views import QueryProductsView

main_member = Blueprint(
    "main_member", __name__, template_folder="templates", static_folder="static"
)


def user_is_member():
    return True if session["user_type"] == "member" else False


@main_member.route("/member/kaeufe")
@login_required
@with_injection
def my_purchases(
    query_purchases: use_cases.QueryPurchases, member_repository: MemberRepository
):
    if not user_is_member():
        return redirect(url_for("auth.zurueck"))

    member = member_repository.get_member_by_id(current_user.id)
    purchases = list(query_purchases(member))
    return render_template("member/my_purchases.html", purchases=purchases)


@main_member.route("/member/suchen", methods=["GET", "POST"])
@login_required
@with_injection
def suchen(
    query_products: use_cases.QueryProducts,
    presenter: QueryProductsPresenter,
    controller: QueryProductsController,
):
    if not user_is_member():
        return redirect(url_for("auth.zurueck"))
    template_name = "member/query_products.html"
    search_form = ProductSearchForm(request.form)
    view = QueryProductsView(
        search_form, query_products, presenter, controller, template_name
    )
    if request.method == "POST":
        return view.respond_to_post()
    else:
        return view.respond_to_get()


@main_member.route("/member/pay_consumer_product", methods=["GET", "POST"])
@commit_changes
@login_required
@with_injection
def pay_consumer_product(
    pay_consumer_product: use_cases.PayConsumerProduct,
    company_repository: CompanyRepository,
    member_repository: MemberRepository,
    plan_repository: PlanRepository,
):
    if not user_is_member():
        return redirect(url_for("auth.zurueck"))

    if request.method == "POST":
        sender = member_repository.get_member_by_id(current_user.id)
        plan = plan_repository.get_plan_by_id(request.form["plan_id"])
        pieces = int(request.form["amount"])
        try:
            pay_consumer_product(
                sender,
                plan,
                pieces,
            )
            flash("Produkt erfolgreich bezahlt.")
        except errors.PlanIsInactive:
            flash(
                "Der angegebene Plan ist nicht aktuell. Bitte wende dich an den Verkäufer, um eine aktuelle Plan-ID zu erhalten."
            )
    return render_template("member/pay_consumer_product.html")


@main_member.route("/member/profile")
@login_required
@with_injection
def profile(
    get_member_profile: use_cases.GetMemberProfileInfo,
    presenter: GetMemberProfileInfoPresenter,
):
    if not user_is_member():
        return redirect(url_for("auth.zurueck"))
    member_profile = get_member_profile(current_user.id)
    view_model = presenter.present(member_profile)
    return render_template(
        "member/profile.html",
        view_model=view_model,
    )


@main_member.route("/member/my_account")
@login_required
@with_injection
def my_account(
    member_repository: MemberRepository,
    get_transaction_infos: use_cases.GetTransactionInfos,
    account_repository: AccountRepository,
):
    if not user_is_member():
        return redirect(url_for("auth.zurueck"))

    member = member_repository.object_from_orm(current_user)
    list_of_trans_infos = get_transaction_infos(member)

    return render_template(
        "member/my_account.html",
        all_transactions_info=list_of_trans_infos,
        my_balance=account_repository.get_account_balance(member.account),
    )


@main_member.route("/member/statistics")
@login_required
@with_injection
def statistics(
    get_statistics: use_cases.GetStatistics,
    presenter: GetStatisticsPresenter,
):
    if not user_is_member():
        return redirect(url_for("auth.zurueck"))

    use_case_response = get_statistics()
    view_model = presenter.present(use_case_response)
    return render_template("member/statistics.html", view_model=view_model)


@main_member.route("/member/hilfe")
@login_required
def hilfe():
    if not user_is_member():
        return redirect(url_for("auth.zurueck"))

    return render_template("member/help.html")
