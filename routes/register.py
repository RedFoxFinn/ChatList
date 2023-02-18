
from flask import redirect, render_template, request, session, flash

from app import application
from tools import config_module as config, admin_module as admins, user_module as users
from tools.validate_input import input_validation, validate_reg_or_log
from tools.password_tools import validate_password_on_register

@application.route("/register")
def register():
    _user = session.get("username")
    if _user is not None:
        return redirect("/")
    localized = ["Rekisteröityminen palveluun", "Käyttäjänimi", "Salasana",
                  "Toista salasana", "Rekisteröitymistunnus", "Rekisteröidy"]
    return render_template("registration.html",
                            text=localized[0],
                            username=localized[1],
                            password=localized[2],
                            repeat_password=localized[3],
                            registration_code=localized[4],
                            submit=localized[5])


@application.route("/handle_registration", methods=["POST"])
def handle_registration():
    __fields = [
        request.form["new_username"],
        request.form["new_password"],
        request.form["new_password_repeat"],
        request.form["registration_code"]
    ]
    __field_validations = [
        1 if validate_reg_or_log(__fields[0], "USERNAME") else 0,
        1 if validate_reg_or_log(__fields[1], "PASSWORD") else 0,
        1 if validate_reg_or_log(__fields[2], "PASSWORD") else 0
    ]
    if (1 if input_validation(f) else 0 for f in __fields) == 0 and\
        sum(__field_validations) == 3:
        validation = validate_password_on_register(__fields[1], __fields[2])
        if __fields[3] == config.REG_CODE and validation is not None:
            _result = users.register(__fields[0], validation)
            if _result is not None:
                flash("Rekisteröityminen onnistui!", "success")
                if (_result[0] == 1 or users.count() == 1) and admins.register_admin(_result[0]):
                    flash("Tunnus rekisteröity pääkäyttäjäksi", "success")
                return redirect("/login")
            flash("Käyttäjätunnus on jo käytössä", "info")
            return redirect("/register")
        flash("Virheellinen syöte yhdessä tai useammassa kentistä", "warning")
        return redirect("/register")
    flash("Virheellinen syöte yhdessä tai useammassa kentistä", "error")
    return redirect("/register")