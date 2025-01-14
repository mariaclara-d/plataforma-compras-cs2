from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

forms_blueprint = Blueprint('forms', __name__)

class TradeLinkForm(FlaskForm):
    tradelink = StringField("TradeLink", validators=[DataRequired()])
    submit = SubmitField("Acessar")
