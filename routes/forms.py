from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Regexp

forms_blueprint = Blueprint('forms', __name__)

class TradeLinkForm(FlaskForm):
    tradelink = StringField(
        "TradeLink",
        validators=[
            DataRequired(message="O TradeLink é obrigatório."),
            Regexp(
                r"^https://steamcommunity\.com/tradeoffer/new/\?partner=\d+&token=[\w-]+$",
                message="Insira um TradeLink válido do Steam."
            )
        ]
    )
    submit = SubmitField("Acessar")
