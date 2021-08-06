from decimal import Decimal
from typing import Optional

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import desc

from arbeitszeit import entities, errors, use_cases
from arbeitszeit.datetime_service import DatetimeService
from project import database
from project.database import with_injection
from project.database.repositories import (
    CompanyRepository,
    CompanyWorkerRepository,
    MemberRepository,
    PlanRepository,
    ProductOfferRepository,
)
from project.extensions import db
from project.forms import ProductSearchForm
from project.models import Company, Offer, Plan

main_company = Blueprint(
    "main_company", __name__, template_folder="templates", static_folder="static"
)


@main_company.route("/company/profile")
@login_required
@with_injection
def profile(
    company_repository: CompanyRepository,
    company_worker_repository: CompanyWorkerRepository,
):
    user_type = session["user_type"]
    if user_type == "company":
        company = company_repository.get_by_id(current_user.id)
        worker = company_worker_repository.get_company_workers(company)
        if worker:
            having_workers = True
        else:
            having_workers = False
        return render_template("company/profile.html", having_workers=having_workers)
    elif user_type == "member":
        return redirect(url_for("auth.zurueck"))


@main_company.route("/company/work", methods=["GET", "POST"])
@login_required
@with_injection
def arbeit(
    company_repository: CompanyRepository,
    member_repository: MemberRepository,
    company_worker_repository: CompanyWorkerRepository,
):
    """shows workers and add workers to company."""
    if request.method == "POST":  # add worker to company
        company = company_repository.get_by_id(current_user.id)
        member = member_repository.get_member_by_id(request.form["member"])
        try:
            use_cases.add_worker_to_company(
                company_worker_repository,
                company,
                member,
            )
        except errors.CompanyDoesNotExist:
            flash("Angemeldeter Betrieb konnte nicht ermittelt werden.")
            return redirect(url_for("auth.start"))
        except errors.WorkerAlreadyAtCompany:
            flash("Mitglied ist bereits in diesem Betrieb beschäftigt.")
        except errors.WorkerDoesNotExist:
            flash("Mitglied existiert nicht.")
        database.commit_changes()
        return redirect(url_for("main_company.arbeit"))
    elif request.method == "GET":
        workers_list = company_worker_repository.get_company_workers(
            company_repository.get_by_id(current_user.id)
        )
        return render_template("company/work.html", workers_list=workers_list)


@main_company.route("/company/suchen", methods=["GET", "POST"])
@login_required
@with_injection
def suchen(
    query_products: use_cases.QueryProducts, offer_repository: ProductOfferRepository
):
    """search products in catalog."""
    search_form = ProductSearchForm(request.form)
    query: Optional[str] = None
    product_filter = use_cases.ProductFilter.by_name

    if request.method == "POST":
        query = search_form.data["search"] or None
        search_field = search_form.data["select"]  # Name, Beschr., Kategorie
        if search_field == "Name":
            product_filter = use_cases.ProductFilter.by_name
        elif search_field == "Beschreibung":
            product_filter = use_cases.ProductFilter.by_description
    results = [
        offer_repository.object_to_orm(offer)
        for offer in query_products(query, product_filter)
    ]
    if not results:
        flash("Keine Ergebnisse!")
    return render_template("company/search.html", form=search_form, results=results)


@main_company.route("/company/buy/<int:id>", methods=["GET", "POST"])
@login_required
@with_injection
def buy(
    id: int,
    purchase_product: use_cases.PurchaseProduct,
    product_offer_repository: ProductOfferRepository,
    company_repository: CompanyRepository,
):
    product_offer = product_offer_repository.get_by_id(id=id)
    buyer = company_repository.get_by_id(current_user.id)

    if request.method == "POST":  # if company buys
        purpose = (
            entities.PurposesOfPurchases.means_of_prod
            if request.form["category"] == "Produktionsmittel"
            else entities.PurposesOfPurchases.raw_materials
        )
        amount = int(request.form["amount"])
        purchase_product(
            product_offer,
            amount,
            purpose,
            buyer,
        )
        database.commit_changes()

        flash(f"Kauf von '{amount}'x '{product_offer.name}' erfolgreich!")
        return redirect("/company/suchen")

    return render_template("company/buy.html", offer=product_offer)


@main_company.route("/company/kaeufe")
@login_required
@with_injection
def my_purchases(
    query_purchases: use_cases.QueryPurchases,
):
    user_type = session["user_type"]

    if user_type == "member":
        return redirect(url_for("auth.zurueck"))
    else:
        session["user_type"] = "company"
        purchases = list(query_purchases(current_user))
        return render_template("company/my_purchases.html", purchases=purchases)


@main_company.route("/company/create_plan", methods=["GET", "POST"])
@login_required
@with_injection
def create_plan(
    original_plan_id: Optional[int],
    seek_approval: use_cases.SeekApproval,
    plan_repository: PlanRepository,
):
    original_plan_id = request.args.get("original_plan_id")
    original_plan = (
        plan_repository.get_by_id(original_plan_id) if original_plan_id else None
    )

    if request.method == "POST":  # Button "Plan erstellen"
        plan_data = dict(request.form)

        new_plan_orm = Plan(
            plan_creation_date=DatetimeService().now(),
            planner=current_user.id,
            costs_p=float(plan_data["costs_p"]),
            costs_r=float(plan_data["costs_r"]),
            costs_a=float(plan_data["costs_a"]),
            prd_name=plan_data["prd_name"],
            prd_unit=plan_data["prd_unit"],
            prd_amount=int(plan_data["prd_amount"]),
            description=plan_data["description"],
            timeframe=int(plan_data["timeframe"]),
            social_accounting=1,
        )
        db.session.add(new_plan_orm)
        database.commit_changes()
        new_plan = plan_repository.object_from_orm(new_plan_orm)

        is_approved = seek_approval(new_plan, original_plan)
        database.commit_changes()

        if is_approved:
            flash("Plan erfolgreich erstellt und genehmigt. Kredit wurde gewährt.")
            return redirect("/company/my_plans")
        else:
            flash(f"Plan nicht genehmigt. Grund:\n{new_plan.approval_reason}")
            return redirect(
                url_for("main_company.create_plan", original_plan_id=original_plan_id)
            )

    return render_template("company/create_plan.html", original_plan=original_plan)


@main_company.route("/company/my_plans", methods=["GET", "POST"])
@login_required
@with_injection
def my_plans(
    plan_repository: PlanRepository,
):
    plans_approved = [
        plan_repository.object_from_orm(plan)
        for plan in current_user.plans.filter_by(
            approved=True,
        ).all()
    ]

    for plan in plans_approved:
        use_cases.calculate_plan_expiration_and_check_if_expired(plan)
    database.commit_changes()

    plans_expired = [plan for plan in plans_approved if plan.expired]
    plans_not_expired = [plan for plan in plans_approved if not plan.expired]

    return render_template(
        "company/my_plans.html",
        plans=plans_not_expired,
        plans_expired=plans_expired,
    )


@main_company.route("/company/create_offer/<int:plan_id>", methods=["GET", "POST"])
@login_required
def create_offer(plan_id):
    if request.method == "POST":  # create offer
        name = request.form["name"]
        description = request.form["description"]
        prd_amount = int(request.form["prd_amount"])

        new_offer = Offer(
            plan_id=plan_id,
            cr_date=DatetimeService().now(),
            name=name,
            description=description,
            amount_available=prd_amount,
            active=True,
        )

        db.session.add(new_offer)
        db.session.commit()
        return render_template("company/create_offer_in_app.html", offer=new_offer)

    plan = Plan.query.filter_by(id=plan_id).first()
    return render_template("company/create_offer.html", plan=plan)


@main_company.route("/company/my_accounts")
@login_required
def my_accounts():
    my_company = Company.query.get(current_user.id)
    my_accounts = my_company.accounts.all()

    all_transactions = []  # date, sender, receiver, p, r, a, prd, purpose

    for my_account in my_accounts:
        # all my sent transactions
        for sent_trans in my_account.transactions_sent.all():
            if sent_trans.receiving_account.account_type.name == "member":
                receiver_name = f"Mitglied: {sent_trans.receiving_account.member.name} ({sent_trans.receiving_account.member.id})"
            elif sent_trans.receiving_account.account_type.name in [
                "p",
                "r",
                "a",
                "prd",
            ]:
                receiver_name = f"Betrieb: {sent_trans.receiving_account.company.name} ({sent_trans.receiving_account.company.id})"
            else:
                receiver_name = "Öff. Buchhaltung"

            change_p, change_r, change_a, change_prd = ("", "", "", "")
            if my_account.account_type.name == "p":
                change_p = -sent_trans.amount
            elif my_account.account_type.name == "r":
                change_r = -sent_trans.amount
            elif my_account.account_type.name == "a":
                change_a = -sent_trans.amount
            elif my_account.account_type.name == "prd":
                change_prd = -sent_trans.amount

            all_transactions.append(
                [
                    sent_trans.date,
                    "Ich",
                    receiver_name,
                    change_p,
                    change_r,
                    change_a,
                    change_prd,
                    sent_trans.purpose,
                ]
            )

        # all my received transactions
        for received_trans in my_account.transactions_received.all():
            if received_trans.sending_account.account_type.name == "accounting":
                sender_name = "Öff. Buchhaltung"
            elif received_trans.sending_account.account_type.name == "member":
                sender_name = f"Mitglied: {received_trans.sending_account.member.name} ({received_trans.sending_account.member.id})"
            elif received_trans.sending_account.account_type.name in [
                "p",
                "r",
                "a",
                "prd",
            ]:
                sender_name = f"Betrieb: {received_trans.sending_account.company.name} ({received_trans.sending_account.company.id})"

            change_p, change_r, change_a, change_prd = ("", "", "", "")
            if my_account.account_type.name == "p":
                change_p = received_trans.amount
            elif my_account.account_type.name == "r":
                change_r = received_trans.amount
            elif my_account.account_type.name == "a":
                change_a = received_trans.amount
            elif my_account.account_type.name == "prd":
                change_prd = received_trans.amount

            all_transactions.append(
                [
                    received_trans.date,
                    sender_name,
                    "Ich",
                    change_p,
                    change_r,
                    change_a,
                    change_prd,
                    received_trans.purpose,
                ]
            )

    all_transactions_sorted = sorted(all_transactions, reverse=True)

    my_balances = []
    for type in ["p", "r", "a", "prd"]:
        balance = my_company.accounts.filter_by(account_type=type).first().balance
        my_balances.append(balance)

    return render_template(
        "company/my_accounts.html",
        my_balances=my_balances,
        all_transactions=all_transactions_sorted,
    )


@main_company.route("/company/transfer_to_worker", methods=["GET", "POST"])
@login_required
@with_injection
def transfer_to_worker(
    send_work_certificates_to_worker: use_cases.SendWorkCertificatesToWorker,
    company_repository: CompanyRepository,
    member_repository: MemberRepository,
):
    if request.method == "POST":
        company = company_repository.get_by_id(current_user.id)
        worker = member_repository.get_member_by_id(request.form["member_id"])
        amount = Decimal(request.form["amount"])

        try:
            send_work_certificates_to_worker(
                company,
                worker,
                amount,
            )
            database.commit_changes()
            flash("Erfolgreich überwiesen.")
        except errors.WorkerNotAtCompany:
            flash("Mitglied ist nicht in diesem Betrieb beschäftigt.")
        except errors.WorkerDoesNotExist:
            flash("Mitglied existiert nicht.")

    return render_template("company/transfer_to_worker.html")


@main_company.route("/company/transfer_to_company", methods=["GET", "POST"])
@login_required
@with_injection
def transfer_to_company(
    pay_means_of_production: use_cases.PayMeansOfProduction,
    company_repository: CompanyRepository,
    plan_repository: PlanRepository,
):
    if request.method == "POST":
        sender = company_repository.get_by_id(current_user.id)
        plan = plan_repository.get_by_id(request.form["plan_id"])
        receiver = company_repository.get_by_id(request.form["company_id"])
        pieces = int(request.form["amount"])
        purpose = (
            entities.PurposesOfPurchases.means_of_prod
            if request.form["category"] == "Produktionsmittel"
            else entities.PurposesOfPurchases.raw_materials
        )
        try:
            pay_means_of_production(
                sender,
                receiver,
                plan,
                pieces,
                purpose,
            )
            database.commit_changes()
            flash("Erfolgreich bezahlt.")
        except errors.CompanyIsNotPlanner:
            flash("Der angegebene Plan gehört nicht zum angegebenen Betrieb.")
        except errors.CompanyDoesNotExist:
            flash("Der Betrieb existiert nicht.")
        except errors.PlanDoesNotExist:
            flash("Der Plan existiert nicht.")

    return render_template("company/transfer_to_company.html")


@main_company.route("/company/my_offers")
@login_required
def my_offers():
    my_company = Company.query.filter_by(id=current_user.id).first()
    my_plans = my_company.plans.all()
    my_offers = []
    for plan in my_plans:
        for offer in plan.offers.all():
            if offer.active == True:
                my_offers.append(offer)

    return render_template("company/my_offers.html", offers=my_offers)


@main_company.route("/company/delete_offer", methods=["GET", "POST"])
@login_required
@with_injection
def delete_offer(
    product_offer_repository: ProductOfferRepository,
):
    offer_id = request.args.get("id")
    product_offer = product_offer_repository.get_by_id(offer_id)
    if request.method == "POST":
        use_cases.deactivate_offer(product_offer)
        database.commit_changes()
        flash("Löschen des Angebots erfolgreich.")
        return redirect(url_for("main_company.my_offers"))

    return render_template("company/delete_offer.html", offer=product_offer)


@main_company.route("/company/cooperate", methods=["GET", "POST"])
@login_required
def cooperate():
    # under construction
    pass
    return render_template("company/cooperate.html")


@main_company.route("/company/hilfe")
@login_required
def hilfe():
    return render_template("company/help.html")
