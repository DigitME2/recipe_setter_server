import logging
from app import db

logger = logging.getLogger('flask.app')


class Recipes(db.Model):
    __tablename__ = "Recipes"
    id = db.Column(db.Integer, name="ID", primary_key=True)
    recipe_name = db.Column(db.String(32), name="RecipeName", nullable=False, unique=True)
    default_weight = db.Column(db.Integer, name="DefaultWeight", nullable=False)
    bagging = db.Column(db.Boolean, name="Bagging")
    washing = db.Column(db.Boolean, name="Washing")

    lines = db.relationship('ProductionLines', backref="current_recipe")


class ProductionLines(db.Model):
    __tablename__ = "ProductionLines"
    id = db.Column(db.Integer, name="ID", primary_key=True)
    line_name = db.Column(db.String(32), name="LineName", unique=True, nullable=False)
    bagging = db.Column(db.Boolean, name="Bagging")
    washing = db.Column(db.Boolean, name="Washing")
    current_device_ip = db.Column(db.String(32), unique=True, name="CurrentDeviceIP")
    current_recipe_name = db.Column(db.String(32), db.ForeignKey("Recipes.RecipeName"), name="CurrentRecipe", nullable=False)
    last_recipe_change = db.Column(db.DateTime, name="LastRecipeChange")
    trays_since_change = db.Column(db.Integer, name="TraysSinceChange", default=0, nullable=False)

    antenna = db.relationship("Antennas", backref="production_line")


class TransactionsLog(db.Model):
    __tablename__ = "TransactionsLog"
    id = db.Column(db.Integer, name="ID", primary_key=True)
    transaction_datetime = db.Column(db.DateTime, name="TransactionDateTime")
    last_updated = db.Column(db.DateTime, name="LastUpdated")
    rfid = db.Column(db.String(32), name="RFID")
    read_point = db.Column(db.String(32), name="ReadPoint")
    line_name = db.Column(db.String(32), name="LineName")
    current_tray_recipe = db.Column(db.String(32), db.ForeignKey("Recipes.RecipeName"), name="CurrentTrayRecipe")
    current_tray_status = db.Column(db.String(32), name="CurrentTrayStatus")
    current_tray_weight = db.Column(db.Integer, name="CurrentTrayWeight")
    transaction_tray_recipe = db.Column(db.String(32), db.ForeignKey("Recipes.RecipeName"), name="TransactionTrayRecipe")
    transaction_tray_status = db.Column(db.String(32), name="TransactionTrayStatus")
    transaction_tray_weight = db.Column(db.Integer, name="TransactionTrayWeight")


class Trays(db.Model):
    __tablename__ = "ItemLog"
    id = db.Column(db.Integer, name="ID", primary_key=True)
    rfid = db.Column(db.String(32), name="RFID")
    current_tray_status = db.Column(db.String(32), name="CurrentTrayStatus")
    current_recipe_name = db.Column(db.String(32), db.ForeignKey("Recipes.RecipeName"), name="CurrentRecipe")
    current_weight = db.Column(db.Integer, name="CurrentWeight")
    last_line_name = db.Column(db.String(32), name="LastLineName")
    last_updated = db.Column(db.DateTime, name="LastUpdated")
    created_date = db.Column(db.Date, name="CreatedDate")
    destroyed_date = db.Column(db.Date, name="DestroyedDate")


class Antennas(db.Model):
    __tablename__ = "Antennas"
    id = db.Column(db.Integer, name="ID", primary_key=True)
    reader_name = db.Column(db.String(32), name="ReaderName", nullable=False)
    antenna_port = db.Column(db.Integer, name="AntennaPort", nullable=False)
    position_name = db.Column(db.String(32), name="PositionName", unique=True, nullable=False)
    production_line_name = db.Column(db.String(32), db.ForeignKey("ProductionLines.LineName"), name="ProductionLine", nullable=False)
    start = db.Column(db.Boolean, nullable=False)
    end = db.Column(db.Boolean, nullable=False)
