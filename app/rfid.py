from datetime import datetime

from flask import abort, Blueprint, jsonify, request, current_app

from app.models import TransactionsLog, Trays, Antennas
from config import Config
from .extensions import db

bp = Blueprint('rfid', __name__)


@bp.route('/rfid', methods=['POST'])
def rfid_route():
    """ The point to be posted to by the RFID reader. This request should contain a list called tag_reads. Each read should contain antennaPort and epc"""
    current_app.logger.debug("Received POST request to /rfid")
    reads = request.json["tag_reads"]
    if not reads:
        current_app.logger.debug("POST request to /rfid does not contain tag_reads")
        return abort(400)
    # The payload contains a list of tag reads, sort through each one separately
    for read in reads:
        antenna_port = read["antennaPort"]
        epc = read["epc"]
        current_app.logger.debug(f"Received tag read: Port={antenna_port}, epc={epc}")
        if antenna_port is not None and epc is not None:
            process_rfid_read(rfid_tag=epc, antenna_port=antenna_port)
        else:
            current_app.logger.debug(f"POST request to /rfid does not contain antenna_port or epc")
    response = jsonify({"message": "success"})
    response.status_code = 200
    return response


def process_rfid_read(antenna_port, rfid_tag):
    """ Process a RFID read once understood by the server"""
    current_app.logger.debug(f"Processing tag {rfid_tag}")

    # Read the antenna, production line and tray from the database
    antenna = Antennas.query.filter_by(antenna_port=antenna_port).first()
    production_line = getattr(antenna, "production_line", None)
    if not production_line:
        current_app.logger.error(f"Could not find production line for Antenna on port {antenna_port}")
        return None
    current_app.logger.debug(f"Tag {rfid_tag} scanned on production line {production_line.line_name}")
    tray = Trays.query.filter_by(rfid=rfid_tag).first()
    if tray is None and Config.ACCEPT_ANY_RFID:
        # Create a new tray with the scanned RFID tag
        current_app.logger.info(f"Creating new tray for tag {rfid_tag}")
        tray = Trays(rfid=rfid_tag, created_date=datetime.utcnow(), current_tray_status="New Tray")
        db.session.add(tray)
        db.session.commit()
    if tray is None:
        current_app.logger.warn("Unknown RFID scanned: " + rfid_tag)
        return None

    # Process the operation depending on the type of production line
    if production_line.bagging:
        # RFID has been scanned on a bagging line
        new_tray_status = "Empty Tray"
        new_recipe_name = production_line.current_recipe_name
        new_weight = 0
    elif production_line.washing and antenna.start:
        # RFID has been scanned at the start of a washing line
        new_tray_status = "Washed Tray"
        new_recipe_name = None
        new_weight = 0
    elif production_line.washing and antenna.end:
        # RFID has been scanned at the end of a washing line
        new_tray_status = "Washed Recipe"
        new_recipe_name = production_line.current_recipe_name
        new_weight = production_line.current_recipe.default_weight
    else:
        current_app.logger.error(f"Antenna {antenna_port} was not assigned to start or end, or production line was not set to washing or bagging")
        return None

    # Ignore if the tray is already in this position (i.e. a re-read)
    if tray.current_tray_status == new_tray_status:
        current_app.logger.debug(f"Re-read - Tray {tray.rfid} on {production_line.line_name}")
        return None

    current_app.logger.info(f"Tray {tray.rfid} on {production_line.line_name}. Current recipe: {production_line.current_recipe_name}")

    # Add to the total trays if applicable
    if antenna.end or production_line.bagging:
        production_line.trays_since_change += 1

    # Create a new transaction
    transaction = TransactionsLog(transaction_datetime=datetime.utcnow(),
                                  rfid=tray.rfid,
                                  read_point=antenna.position_name,
                                  line_name=production_line.line_name,
                                  current_tray_recipe=tray.current_recipe_name,
                                  current_tray_status=tray.current_tray_status,
                                  current_tray_weight=tray.current_weight,
                                  transaction_tray_recipe=new_recipe_name,
                                  transaction_tray_status=new_tray_status,
                                  transaction_tray_weight=new_weight)
    db.session.add(transaction)

    tray.current_tray_status = new_tray_status
    tray.current_recipe_name = new_recipe_name
    tray.current_weight = new_weight
    tray.last_line_name = production_line.line_name
    tray.last_updated = datetime.now()
    db.session.commit()

