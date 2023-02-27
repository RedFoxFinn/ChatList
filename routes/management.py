
from flask import abort, redirect, render_template, request, session, flash

from app import application
from tools.database_module import DB
from tools import chat_module as chats,\
    group_module as groups,\
    moderator_module as moderators,\
    topics_module as topics
from tools.validate_input import input_validation, link_input_validation

_admin_levels = ["ADMIN", "SUPER"]


@application.route("/management")
def management():
    _user = session.get("username")
    if _user is None:
        flash("Toiminto vaatii kirjautumisen", "warning")
        return redirect("/login")
    _status = session.get("user_status")
    if _status not in _admin_levels:
        flash("Toiminto vaatii ylläpitäjän oikeudet", "error")
        return redirect("/")
    localized = {
        "text": "Hallintapaneeli",
        "groups": "Ryhmien hallinta",
        "chats": "Keskusteluryhmien hallinta",
        "admins": "Pääkäyttäjien hallinta"
    }
    return render_template("management.html", local=localized)


@application.route("/management/chats")
def chat_management():
    localized = {
        "text": "Hallintapaneeli",
        "current_mode": "Keskusteluryhmien hallinta",
        "add_moderator": "Ylläpitäjän lisäys",
        "handle": "Nimimerkki",
        "chat_link": "Keskustelulinkki",
        "mod_submit": "Lisää ylläpitäjä",
        "add_new": "Keskusteluryhmän lisäys",
        "listing": "Keskusteluryhmälista",
        "groups": "Ryhmien hallinta",
        "chats": "Keskusteluryhmien hallinta",
        "admins": "Pääkäyttäjien hallinta",
        "chat_name": "Keskusteluryhmän nimi",
        "topic": "Aihe",
        "group": "Ryhmä",
        "link": "Linkki",
        "moderators": "Ylläpitäjät",
        "submit": "Lisää keskusteluryhmä",
        "update": "Päivitä",
        "tip_header":"Ohjeet ylläpitäjien lisäämiseen",
        "tip_mod_handle":"Ylläpitäjän nimimerkin pituus 3-32 merkkiä",
        "tip_mod_chat":"Linkki keskusteluun ylläpitäjän kanssa",
        "tip_characters":"Sallittuja merkkejä",
        "tip_letters":"Kirjaimet a-z sekä A-Z",
        "tip_numbers":"Numerot 0-9",
        "tip_forbidden":"Muut erikoismerkit kuin @,$,£,€,_,-,+ ja . eivät ole sallittuja ylläpitäjän nimimerkissä"
    }
    _topic_data = topics.get_topics()
    _group_data = groups.get_groups()
    _moderator_data = moderators.get_moderators()

    _user = session.get("username")
    _permission = session.get("user_status")

    if _user is not None and _permission is not None and _permission in _admin_levels:
        _chats = []
        _chats += chats.get_public_chats()
        _chats += chats.get_login_restricted_chats()
        _chats += chats.get_age_restricted_chats()
        _chats += chats.get_security_restricted_chats()
        return render_template("chat_management.html",
                               local=localized,
                               topic_options=_topic_data if len(
                                   _topic_data) > 0 else [],
                               group_options=_group_data if len(
                                   _group_data) > 0 else [],
                               moderator_options=_moderator_data if len(
                                   _moderator_data) > 0 else [],
                               showable=_chats,
                               management="True",
                               header={
                                   "public": "Julkiset",
                                   "login": "Kirjautuneille",
                                   "admin": "Rajoitetut"}
                               )
    flash("Toiminto vaatii kirjautumisen", "warning")
    return redirect("/login")


@application.route("/management/chats/<int:id_value>")
def manage_single_chat(id_value: int):
    return f"I will manage chat with id {id_value}"


@application.route("/handle_chat_adding", methods=["POST"])
def handle_chat_adding():
    if request.form["csrf_token"] != session.get("csrf_token"):
        return abort(403)
    _fields = [
        request.form["cname"],
        request.form["topic"],
        request.form["group"],
        request.form["link"],
        request.form["moderators"]
    ]
    _input_validations = [
        1 if input_validation(f) else 0 for f in _fields
    ]
    if sum(_input_validations) == 0:
        _fields[1] = topics.add_topic(_fields[1])
        input_data = {"cname": _fields[0], "topic": int(_fields[1]), "group": int(
            _fields[2]), "link": _fields[3], "moderators": [int(mod) for mod in _fields[4]]}
        if chats.add_chat(input_data):
            flash("Keskusteluryhmän lisääminen onnistui.", "success")
            return redirect("/management/chats")
        flash("Virheellinen syöte yhdessä tai useammassa kentistä.", "warning")
        return redirect("/management/chats")
    flash("Virheellinen syöte yhdessä tai useammassa kentistä.", "error")
    return redirect("/management/chats")


@application.route("/handle_moderator_adding", methods=["POST"])
def handle_moderator_adding():
    if request.form["csrf_token"] != session.get("csrf_token"):
        return abort(403)
    _fields = [request.form["handle"], request.form["chat_link"]]
    _input_validations = [
        1 if input_validation(_fields[0],handle_mode=True) else 0,
        1 if link_input_validation(_fields[1]) else 0
    ]
    if sum(_input_validations) == 2:
        _result = moderators.add_moderator(_fields[0],_fields[1])
        if _result == 'ADDED':
            _retry_values = session.get("retry_form_values")
            if _retry_values is not None:
                del session["retry_form_values"]
            flash("Ylläpitäjän lisääminen onnistui.", "success")
            return redirect("/management/chats")
        elif _result == 'UPDATED':
            _retry_values = session.get("retry_form_values")
            if _retry_values is not None:
                del session["retry_form_values"]
            flash("Ylläpitäjän tiedot päivitetty onnistuneesti.", "success")
            return redirect("/management/chats")
        session["retry_form_values"] = {"handle": _fields[0],"link": _fields[1]}
        flash("Odottamaton virhe: ".join(_result), "warning")
        return redirect("/management/chats")
    session["retry_form_values"] = {"handle": _fields[0],"link": _fields[1]}
    flash("Virheellinen syöte yhdessä tai useammassa kentistä. \
        Tarkista syöttämäsi tiedot.", "error")
    return redirect("/management/chats")


@application.route("/management/groups")
def group_management():
    localized = {
        "text": "Hallintapaneeli",
        "current_mode": "Ryhmien hallinta",
        "add_new": "Ryhmän lisäys",
        "listing": "Ryhmälista",
        "groups": "Ryhmien hallinta",
        "chats": "Keskusteluryhmien hallinta",
        "admins": "Pääkäyttäjien hallinta",
        "group_name": "Ryhmän nimi",
        "restriction_level": "Rajoitustaso",
        "submit": "Lisää ryhmä",
        "update": "Päivitä",
        "tip_header":"Ohjeet ryhmien lisäämiseen",
        "tip_groupname":"Ryhmän nimen pituus 3-32 merkkiä",
        "tip_characters":"Sallittuja merkkejä",
        "tip_letters":"Kirjaimet a-z sekä A-Z",
        "tip_numbers":"Numerot 0-9",
        "tip_forbidden":"Erikoismerkit eivät ole salittuja"
    }
    _restriction_opts = [("NONE", "Rajoittamaton"), ("LOGIN", "Kirjautuminen"),
                         ("AGE", "Ikärajoitettu"), ("SEC", "Turvaluokitettu")]
    _user = session.get("username")
    if _user is not None:
        data = groups.get_groups()
        return render_template(
            "group_management.html",
            local=localized,
            restriction_options=_restriction_opts,
            groups=data)
    flash("Toiminto vaatii kirjautumisen.", "warning")
    return redirect("/login")


@application.route("/management/groups/<int:id_value>")
def manage_single_group(id_value: int):
    _group = groups.get_group_by_id(id_value)
    _status = session.get("user_status")
    if _status is None or _status not in ["ADMIN", "SUPER"]:
        flash("Toiminto vaatii ylläpitäjän oikeudet")
        return redirect("/management")
    if _status in ["ADMIN", "SUPER"]:
        old_data = {"old_name": _group[1],
                    "old_restriction": _group[2], "id": _group[0]}
        localized = {
            "text": "Hallintapaneeli",
            "current_mode": "Ryhmän hallinta",
            "groups": "Ryhmien hallinta",
            "chats": "Keskusteluryhmien hallinta",
            "admins": "Ylläpitäjien hallinta",
            "group_name": "Ryhmän nimi",
            "restriction_level": "Rajoitustaso",
            "submit": "Päivitä ryhmä"
        }
        _restriction_opts = [("NONE", "Rajoittamaton"), ("LOGIN", "Kirjautuminen"),
                             ("AGE", "Ikärajoitettu"), ("SEC", "Turvaluokitettu")]
        return render_template(
            "single_group_management.html",
            local=localized,
            restriction_options=_restriction_opts,
            group=old_data)
    flash("Toiminto vaatii kirjautumisen pääkäyttäjänä", "info")
    return redirect("/login")


@application.route("/handle_group_adding", methods=["POST"])
def handle_group_adding():
    if request.form["csrf_token"] != session.get("csrf_token"):
        return abort(403)
    _fields = [request.form["gname"], request.form["restriction"]]
    _input_validations = [
        1 if input_validation(f) else 0 for f in _fields
    ]
    if sum(_input_validations) == 0:
        input_data = {"gname": _fields[0], "restrict": _fields[1]}
        sql = "INSERT INTO Groups (gname,restriction) VALUES (:gname,:restrict)"
        try:
            DB.session.execute(sql, input_data) # pylint: disable=no-member
            DB.session.commit() # pylint: disable=no-member
            flash("Ryhmän lisääminen onnistui", "success")
            return redirect("/management/groups")
        except:   # pylint: disable=bare-except
            flash("Virheellinen syöte yhdessä tai useammassa kentistä", "warning")
            return redirect("/management/groups")
    flash("Virheellinen syöte yhdessä tai useammassa kentistä", "error")
    return redirect("/management/groups")


@application.route("/handle_group_update", methods=["POST"])
def handle_group_update():
    if request.form["csrf_token"] != session.get("csrf_token"):
        return abort(403)
    _fields = [request.form["gname"],
               request.form["restriction"], request.form["id"]]
    _input_validations = [
        1 if input_validation(f) else 0 for f in _fields
    ]
    if sum(_input_validations) == 0:
        sql = f"UPDATE Groups SET gname='{_fields[0]}',\
          restriction='{_fields[1]}' WHERE id={_fields[2]}"
        try:
            DB.session.execute(sql) # pylint: disable=no-member
            DB.session.commit() # pylint: disable=no-member
            flash("Ryhmän päivittämimnen onnistui", "success")
            return redirect("/management/groups")
        except:   # pylint: disable=bare-except
            flash("Virheellinen syöte yhdessä tai useammassa kentistä. Tarkista antamasi syöte.", "warning")
            return redirect("/management/groups")
    flash("Virheellinen syöte yhdessä tai useammassa kentistä. Tarkista antamasi syöte.", "error")
    return redirect("/management/groups")


@application.route("/management/admins")
def admin_management():
    return "admin management will eventually be here. Soon<sup>TM</sup>"
