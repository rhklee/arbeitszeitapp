from .models import Nutzer, Betriebe, Arbeiter, Angebote, Arbeit,\
    Produktionsmittel, Kaeufe, Auszahlungen
from sqlalchemy.sql import func
from .extensions import db
from graphviz import Graph
from sqlalchemy.orm import aliased

import datetime
from .models import KooperationenMitglieder
from sqlalchemy.sql import case


class SearchProducts():
    """
    All SQL-requests around searching in the catalog.
    Returns non-mutable _collections.result-Objects.
    """

    def get_angebote(self):
        """
        returns BaseQuery object with all products available
        (grouped results, active or not),
        with several columns, including the coop-price.
        """

        km = aliased(KooperationenMitglieder)
        km2 = aliased(KooperationenMitglieder)

        # subquery returns koop-preis
        subq = db.session.query(
            func.avg(Angebote.preis)).\
            select_from(km).\
            join(Angebote, km.mitglied == Angebote.id).\
            filter(Angebote.aktiv == True).\
            filter(km.kooperation == km2.kooperation).\
            group_by(km.kooperation).\
            as_scalar()

        qry = db.session.query(
            func.min(Angebote.id).label("id"),
            Angebote.name.label("angebot_name"),
            func.min(Angebote.p_kosten).label("p_kosten"),
            func.min(Angebote.v_kosten).label("v_kosten"),
            Betriebe.name.label("betrieb_name"),
            Betriebe.id.label("betrieb_id"),
            Betriebe.email,
            Angebote.beschreibung,
            Angebote.kategorie,
            Angebote.preis,
            func.count(Angebote.id).label("vorhanden"),
            km2.kooperation,
            case([(km2.kooperation == None, Angebote.preis), ], else_=subq).
            label("koop_preis")
            ).\
            select_from(Angebote).\
            join(Betriebe, Angebote.betrieb == Betriebe.id).\
            outerjoin(km2, Angebote.id == km2.mitglied).\
            group_by(
                Betriebe, Angebote.cr_date, "angebot_name",
                Angebote.beschreibung, Angebote.kategorie,
                Angebote.preis, km2.kooperation)

        return qry

    def get_angebot_by_id(self, angebote_id):
        """returns one angebot filtered by angebote_id."""
        return self.get_angebote().filter(Angebote.id == angebote_id).one()

    def get_angebote_aktiv(self, search_string="", search_field=""):
        """
        returns all aktive angebote.
        search string and search field may be optionally specified.
        """
        if search_string or search_field:
            if search_field == 'Name':
                angebote = self.get_angebote().filter(
                    Angebote.name.contains(search_string)).\
                    all()

            elif search_field == 'Beschreibung':
                angebote = self.get_angebote().filter(
                    Angebote.beschreibung.contains(search_string)).\
                        all()

            elif search_field == 'Kategorie':
                angebote = self.get_angebote().filter(
                    Angebote.kategorie.contains(search_string)).\
                        all()
        else:
            angebote = self.get_angebote().filter(Angebote.aktiv == True).all()
        return angebote


class CompositionOfPrices():
    """
    All SQL-requests around the topic of (graphical) representations of
    the composition of prices.
    """
    def get_table_of_composition(self, angebote_id):
        """
        makes a sql request to the db, gives back the composition of price
        (preiszusammensetzung) in table format of the specified Angebot.
        """
        angebote1 = aliased(Angebote)
        angebote2 = aliased(Angebote)
        angebote3 = aliased(Angebote)
        angebote4 = aliased(Angebote)
        angebote5 = aliased(Angebote)

        produktionsmittel1 = aliased(Produktionsmittel)
        produktionsmittel2 = aliased(Produktionsmittel)
        produktionsmittel3 = aliased(Produktionsmittel)
        produktionsmittel4 = aliased(Produktionsmittel)
        produktionsmittel5 = aliased(Produktionsmittel)

        kaeufe2 = aliased(Kaeufe)
        kaeufe3 = aliased(Kaeufe)
        kaeufe4 = aliased(Kaeufe)
        kaeufe5 = aliased(Kaeufe)

        first_level = db.session.query(
            angebote1.id.label("angebot1"), angebote1.name.label("name1"),
            angebote1.p_kosten.label("p1"),
            angebote1.v_kosten.label("v1"), angebote1.preis.label("preis1"),
            produktionsmittel1.prozent_gebraucht.label("proz_gebr2"),
            produktionsmittel1.kauf.label("kauf2"),
            kaeufe2.angebot.label("angebot2"), angebote2.name.label("name2"),
            angebote2.preis.label("preis2"),
            (angebote2.preis*(produktionsmittel1.prozent_gebraucht/100))
            .label("kosten2"),
            produktionsmittel2.prozent_gebraucht.label("proz_gebr3"),
            produktionsmittel2.kauf.label("kauf3"),
            kaeufe3.angebot.label("angebot3"), angebote3.name.label("name3"),
            angebote3.preis.label("preis3"),
            (angebote3.preis*(produktionsmittel2.prozent_gebraucht/100)).
            label("kosten3"),
            produktionsmittel3.prozent_gebraucht.label("proz_gebr4"),
            produktionsmittel3.kauf.label("kauf4"),
            kaeufe4.angebot.label("angebot4"), angebote4.name.label("name4"),
            angebote4.preis.label("preis4"),
            (angebote4.preis*(produktionsmittel3.prozent_gebraucht/100)).
            label("kosten4"),
            produktionsmittel4.prozent_gebraucht.label("proz_gebr5"),
            produktionsmittel4.kauf.label("kauf5"),
            kaeufe5.angebot.label("angebot5"), angebote5.name.label("name5"),
            angebote5.preis.label("preis5"),
            (angebote5.preis*(produktionsmittel4.prozent_gebraucht/100)).
            label("kosten5"),
            produktionsmittel5.prozent_gebraucht.label("proz_gebr6"),
            produktionsmittel5.kauf.label("kauf6"))\
            .select_from(angebote1).filter(angebote1.id == angebote_id).\
            outerjoin(
                produktionsmittel1, angebote1.id == produktionsmittel1.angebot)

        second_level = first_level.outerjoin(
            kaeufe2, produktionsmittel1.kauf == kaeufe2.id).\
            outerjoin(angebote2, kaeufe2.angebot == angebote2.id).\
            outerjoin(produktionsmittel2,
                      angebote2.id == produktionsmittel2.angebot)

        third_level = second_level.outerjoin(
            kaeufe3, produktionsmittel2.kauf == kaeufe3.id).\
            outerjoin(angebote3, kaeufe3.angebot == angebote3.id).\
            outerjoin(
                produktionsmittel3, angebote3.id == produktionsmittel3.angebot)

        fourth_level = third_level.outerjoin(
            kaeufe4, produktionsmittel3.kauf == kaeufe4.id).\
            outerjoin(angebote4, kaeufe4.angebot == angebote4.id).\
            outerjoin(
                produktionsmittel4, angebote4.id == produktionsmittel4.angebot)

        fifth_level = fourth_level.outerjoin(
            kaeufe5, produktionsmittel4.kauf == kaeufe5.id).\
            outerjoin(angebote5, kaeufe5.angebot == angebote5.id).\
            outerjoin(
                produktionsmittel5, angebote5.id == produktionsmittel5.angebot)

        table_of_composition = fifth_level
        return table_of_composition

    def get_positions_in_table(self, base_query):
        """
        takes a 'flask_sqlalchemy.BaseQuery' and creates list of dictionaries
        that stores the info, in which row and column of the database table
        the angebote are positioned
        """
        col1, col2, col3, col4, col5 = [], [], [], [], []
        for row in base_query:
            col1.append(row.name1)
            col2.append(row.name2)
            col3.append(row.name3)
            col4.append(row.name4)
            col5.append(row.name5)
        list_of_cols = [col1, col2, col3, col4, col5]

        cols_dict = []
        for r in range(len(list_of_cols)):
            list1 = []
            for c, i in enumerate(list_of_cols[r]):
                keys_in_list1 = []
                for j in list1:
                    if j.keys():
                        keys_in_list1.append(list(j.keys())[0])

                if i in list(keys_in_list1):
                    for item in list1:
                        if list(item.keys())[0] == i:
                            item[i].append(c)
                elif i is None:
                    pass
                else:
                    list1.append({i: [c]})
            cols_dict.append(list1)
        return cols_dict

    def create_dots(self, cols_dict, table_of_composition):
        """
        creates dot nodes and edges based on position of angebote in cols_dict/
        the database table. If angebot x is in the same row and next
        column of angebot y, x is child of y and will be connected with an
        edge.
        """
        dot = Graph(comment='Graph zur Preiszusammensetzung', format="svg")
        for cnt, col in enumerate(cols_dict):
            if cnt == 0:  # if first column (should be all the same angebot)
                angebot_0 = list(col[0].keys())[0]
                dot.node(
                    f"{angebot_0}_{cnt}",
                    f"{angebot_0}, "
                    f"Preis: {round(table_of_composition[0].preis1, 2)} Std.")
                dot.node(
                    f"{angebot_0}_v_{cnt}",
                    f"Arbeitskraft: \
{round(table_of_composition[0].v1, 2)} Std.")
                dot.edge(f"{angebot_0}_{cnt}", f"{angebot_0}_v_{cnt}")
            else:  # the following columns
                for j in col:
                    current_angebot = list(j.keys())[0]
                    current_position = list(j.values())[0]
                    if cnt == 1:
                        current_kosten = round(
                            table_of_composition[current_position[0]].
                            kosten2, 2)
                        dot.node(
                            f"{current_angebot}_{cnt}",
                            f"{current_angebot}, \
Kosten: {current_kosten} Std.")
                    elif cnt in [2, 3, 4]:
                        dot.node(
                            f"{current_angebot}_{cnt}", f"{current_angebot}")

                    parent_angebote_list = cols_dict[cnt-1]
                    for par in parent_angebote_list:
                        parent_angebot = list(par.keys())[0]
                        parent_positions = list(par.values())[0]
                        for cur_pos in current_position:
                            if cur_pos in parent_positions:
                                # create edge between parent and current node
                                dot.edge(
                                    f"{parent_angebot}_{cnt-1}",
                                    f"{current_angebot}_{cnt}")
                                break  # only one match is enough
        return dot


# Kaufen

def kaufen(kaufender_type, angebot, kaeufer_id):
    """
    buy product.
    """
    # aktuellen (koop-)preis erhalten:
    preis = SearchProducts().get_angebot_by_id(angebot.id).koop_preis

    # kauefe aktualisieren
    if kaufender_type == "betriebe":
        kaufender = Betriebe
        new_kauf = Kaeufe(kauf_date=datetime.datetime.now(),
                          angebot=angebot.id,
                          type_nutzer=False,
                          betrieb=kaeufer_id,
                          nutzer=None,
                          kaufpreis=preis)
        db.session.add(new_kauf)
        db.session.commit()
    elif kaufender_type == "nutzer":
        kaufender = Nutzer
        new_kauf = Kaeufe(kauf_date=datetime.datetime.now(),
                          angebot=angebot.id,
                          type_nutzer=True,
                          betrieb=None,
                          nutzer=kaeufer_id,
                          kaufpreis=preis)
        db.session.add(new_kauf)
        db.session.commit()

    # angebote aktiv = False
    angebot.aktiv = False
    db.session.commit()

    # guthaben käufer verringern
    kaeufer = db.session.query(kaufender).\
        filter(kaufender.id == kaeufer_id).first()
    kaeufer.guthaben -= preis
    db.session.commit()

    # guthaben des anbietenden betriebes erhöhen
    anbietender_betrieb_id = angebot.betrieb
    anbietender_betrieb = Betriebe.query.filter_by(
        id=anbietender_betrieb_id).first()
    anbietender_betrieb.guthaben += preis  # angebot.p_kosten
    db.session.commit()


# User

def get_user_by_mail(email):
    """returns first user in User, filtered by email."""
    nutzer = Nutzer.query.filter_by(email=email).first()
    return nutzer


def get_user_by_id(id):
    """returns first user in User, filtered by id."""
    nutzer = Nutzer.query.filter_by(id=id).first()
    return nutzer


def add_new_user(email, name, password):
    """
    adds a new user to User.
    """
    new_user = Nutzer(
        email=email,
        name=name,
        password=password)
    db.session.add(new_user)
    db.session.commit()


def get_purchases(user_id):
    """returns all purchases made by user."""
    purchases = db.session.query(
        Kaeufe.id,
        Angebote.name,
        Angebote.beschreibung,
        func.round(Angebote.preis, 2).
        label("preis")
        ).\
        select_from(Kaeufe).\
        filter_by(nutzer=user_id).\
        join(Angebote, Kaeufe.angebot == Angebote.id).\
        all()
    return purchases


def get_workplaces(user_id):
    """returns all workplaces the user is assigned to."""
    workplaces = db.session.query(Betriebe)\
        .select_from(Arbeiter).\
        filter_by(nutzer=user_id).\
        join(Betriebe, Arbeiter.betrieb == Betriebe.id).\
        all()
    return workplaces


def new_withdrawal(user_id, amount, code):
    """register new withdrawal and withdraw amount from user's account."""
    new_withdrawal = Auszahlungen(
        type_nutzer=True,
        nutzer=user_id,
        betrag=amount,
        code=code)
    db.session.add(new_withdrawal)
    db.session.commit()

    # betrag vom guthaben des users abziehen
    nutzer = db.session.query(Nutzer).\
        filter(Nutzer.id == user_id).\
        first()
    nutzer.guthaben -= amount
    db.session.commit()


# Company

def get_company_by_mail(email):
    """returns first company in Company, filtered by mail."""
    betrieb = Betriebe.query.filter_by(email=email).first()
    return betrieb


def add_new_company(email, name, password):
    """
    adds a new company to Company.
    """
    new_company = Betriebe(
        email=email,
        name=name,
        password=password)
    db.session.add(new_company)
    db.session.commit()


def get_workers(betrieb_id):
    """get all workers working in a company."""
    workers = db.session.query(Nutzer.id, Nutzer.name).\
        select_from(Arbeiter).join(Nutzer).\
        filter(Arbeiter.betrieb == betrieb_id).group_by(Nutzer.id).all()
    return workers


def get_worker_in_company(worker_id, company_id):
    """get specific worker in a company."""
    arbeiter = Arbeiter.query.filter_by(
        nutzer=worker_id, betrieb=company_id).\
        first()
    return arbeiter


def get_hours_worked(betrieb_id):
    """get all hours worked in a company."""
    hours_worked = db.session.query(
        Nutzer.id, Nutzer.name,
        func.concat(func.sum(Arbeit.stunden), " Std.").
        label('summe_stunden')
        ).select_from(Angebote).\
        filter(Angebote.betrieb == betrieb_id).\
        join(Arbeit).join(Nutzer).group_by(Nutzer.id).\
        order_by(func.sum(Arbeit.stunden).desc()).all()
    return hours_worked


def get_means_of_prod(betrieb_id):
    """
    returns tuple of active and inactive means of prouction of company.
    """
    produktionsmittel_qry = db.session.query(
        Kaeufe.id,
        Angebote.name,
        Angebote.beschreibung,
        func.round(Kaeufe.kaufpreis, 2).
        label("kaufpreis"),
        func.round(
            func.coalesce(
                func.sum(Produktionsmittel.prozent_gebraucht), 0), 2).
        label("prozent_gebraucht"))\
        .select_from(Kaeufe)\
        .filter(Kaeufe.betrieb == betrieb_id).\
        outerjoin(Produktionsmittel,
                  Kaeufe.id == Produktionsmittel.kauf).\
        join(Angebote, Kaeufe.angebot == Angebote.id).\
        group_by(Kaeufe, Angebote, Produktionsmittel.kauf)

    produktionsmittel_aktiv = produktionsmittel_qry.\
        having(func.coalesce(func.sum(Produktionsmittel.prozent_gebraucht).
               label("prozent_gebraucht"), 0).
               label("prozent_gebraucht") < 100).all()
    produktionsmittel_inaktiv = produktionsmittel_qry.\
        having(func.coalesce(func.sum(Produktionsmittel.prozent_gebraucht).
               label("prozent_gebraucht"), 0).
               label("prozent_gebraucht") == 100).all()

    return (produktionsmittel_aktiv, produktionsmittel_inaktiv)


# Worker

def get_first_worker(betrieb_id):
    """get first worker in Worker."""
    worker = Arbeiter.query.filter_by(betrieb=betrieb_id).first()
    return worker


def add_new_worker_to_company(nutzer_id, betrieb_id):
    """
    adds a new worker to Company.
    """
    new_worker = Arbeiter(
        nutzer=nutzer_id,
        betrieb=betrieb_id)
    db.session.add(new_worker)
    db.session.commit()


# Angebote

def get_angebot_by_id(id):
    """get first angebot, filtered by id"""
    angebot = db.session.query(Angebote).\
        filter(Angebote.id == id).first()
    return angebot
