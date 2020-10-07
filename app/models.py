import logging
from app import db

logger = logging.getLogger('flask.app')


class Recipes(db.Model):
    __tablename__ = "Recipes"
    id = db.Column(db.Integer, name="ID", primary_key=True)
    recipe_name = db.Column(db.String, name="RecipeName", unique=True)
    default_weight = db.Column(db.Integer, name="DefaultWeight")
    bagging = db.Column(db.Boolean, name="Bagging")
    washing = db.Column(db.Boolean, name="Washing")

    lines = db.relationship('ProductionLines', backref="current_recipe")


class ProductionLines(db.Model):
    __tablename__ = "ProductionLines"
    id = db.Column(db.Integer, name="ID", primary_key=True)
    line_name = db.Column(db.String, name="LineName", unique=True, nullable=False)
    bagging = db.Column(db.Boolean, name="Bagging")
    washing = db.Column(db.Boolean, name="Washing")
    current_device_ip = db.Column(db.String, unique=True, name="CurrentDeviceIP")
    current_recipe_name = db.Column(db.String, db.ForeignKey("Recipes.RecipeName"), name="CurrentRecipe")
    last_recipe_change = db.Column(db.DateTime, name="LastRecipeChange")
    trays_since_change = db.Column(db.Integer, name="TraysSinceChange", default=0)

    antenna = db.relationship("Antennas", backref="production_line")


class TransactionsLog(db.Model):
    __tablename__ = "TransactionsLog"
    id = db.Column(db.Integer, name="ID", primary_key=True)
    transaction_datetime = db.Column(db.DateTime, name="TransactionDateTime")
    rfid = db.Column(db.String, name="RFID")
    read_point = db.Column(db.String, name="ReadPoint")
    tray_recipe_name = db.Column(db.String,  db.ForeignKey("Recipes.RecipeName"), name="TrayRecipe")
    tray_status = db.Column(db.String, name="TrayStatus")
    selected_recipe_name = db.Column(db.String, db.ForeignKey("Recipes.RecipeName"), name="SelectedRecipe")
    weight = db.Column(db.Integer, name="Weight")


class Trays(db.Model):
    __tablename__ = "ItemLog"
    id = db.Column(db.Integer, name="ID", primary_key=True)
    rfid = db.Column(db.String, name="RFID")
    current_tray_status = db.Column(db.String, name="CurrentTrayStatus")
    current_recipe_name = db.Column(db.String, db.ForeignKey("Recipes.RecipeName"), name="CurrentRecipe")
    current_weight = db.Column(db.String, name="CurrentWeight")
    created_date = db.Column(db.Date, name="CreatedDate")
    destroyed_date = db.Column(db.Date, name="DestroyedDate")


class Antennas(db.Model):
    __tablename__ = "Antennas"
    id = db.Column(db.Integer, name="ID", primary_key=True)
    antenna_port = db.Column(db.Integer, name="AntennaPort", nullable=False)
    position_name = db.Column(db.String, name="PositionName", unique=True, nullable=False)
    production_line_name = db.Column(db.String, db.ForeignKey("ProductionLines.LineName"), name="ProductionLine", nullable=False)
    start = db.Column(db.Boolean, nullable=False)
    end = db.Column(db.Boolean, nullable=False)
