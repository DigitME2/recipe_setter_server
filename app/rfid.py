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
    antenna = Antennas.query.filter_by(antenna_port=antenna_port).first()
    if hasattr(antenna, 'production_line'):
        production_line = antenna.production_line
        current_app.logger.debug(f"Tag {rfid_tag} scanned on production line {production_line.line_name}")
    else:
        current_app.logger.error(f"Could not find production line for Antenna on port {antenna_port}")
        return

    tray = Trays.query.filter_by(rfid=rfid_tag).first()
    if tray:
        # Get these values now for the transaction log
        prior_tray_state = tray.current_tray_status
        prior_recipe_name = tray.current_recipe_name
    else:
        if Config.ACCEPT_ANY_RFID:
            # Create a new tray with the scanned RFID tag
            current_app.logger.info(f"Creating new tray for tag {rfid_tag}")
            tray = Trays(rfid=rfid_tag, created_date=datetime.utcnow())
            prior_tray_state = "New Tray"
            prior_recipe_name = None
            db.session.add(tray)
            db.session.commit()
        else:
            # Do not process RFID tags that are not in the system
            current_app.logger.warn("Unknown RFID scanned: " + rfid_tag)
            return

    if production_line.bagging:
        # RFID has been scanned on a bagging line
        tray = process_tray_at_bagging(tray, production_line)
        production_line.trays_since_change += 1
    elif production_line.washing and antenna.start:
        # RFID has been scanned at the start of a washing line
        tray = process_tray_at_washing_start(tray, production_line)
    elif production_line.washing and antenna.end:
        # RFID has been scanned at the end of a washing line
        tray = process_tray_at_washing_end(tray, production_line)
        production_line.trays_since_change += 1
    else:
        current_app.logger.error(f"Antenna {antenna_port} was not assigned to start or end, or production line was not set to washing or bagging")
        return abort(500)

    if not tray:
        # Functions return None if this is a re-read
        current_app.logger.debug(f"Tray with tag {rfid_tag} is already in this position (ie this is a re-read)")
        return

    # Create a new transaction
    transaction = TransactionsLog(transaction_datetime=datetime.utcnow(),
                                  rfid=rfid_tag,
                                  read_point=antenna.position_name,
                                  tray_status=prior_tray_state,
                                  tray_recipe_name=prior_recipe_name,
                                  selected_recipe_name=production_line.current_recipe_name,
                                  weight=tray.current_weight)
    db.session.add(transaction)
    db.session.commit()  # This will also save the Tray status, as returned by the processing functions


def process_tray_at_washing_start(tray, production_line):
    new_tray_status = f"empty on {production_line.line_name}"
    if tray.current_tray_status == new_tray_status:
        # Return nothing if the tray is already in this position (i.e. a re-read)
        return None
    tray.current_tray_status = new_tray_status
    tray.current_recipe_name = None
    tray.current_weight = 0
    current_app.logger.info(f"Tray {tray.rfid} at start of {production_line.line_name}. Current recipe: {production_line.current_recipe_name}")
    return tray


def process_tray_at_washing_end(tray, production_line):
    new_tray_status = "full tray (washed)"
    if tray.current_tray_status == new_tray_status:
        # Return nothing if the tray is already in this position (i.e. a re-read)
        return None
    tray.current_tray_status = new_tray_status
    tray.current_recipe_name = production_line.current_recipe_name
    tray.current_weight = production_line.current_recipe.default_weight
    current_app.logger.info(f"Tray {tray.rfid} at end of {production_line.line_name}. Current recipe: {production_line.current_recipe_name}")
    return tray


def process_tray_at_bagging(tray, production_line):
    new_tray_status = "full tray (bagged)"
    if tray.current_tray_status == new_tray_status:
        # Return nothing if the tray is already in this position (i.e. a re-read)
        return None
    tray.current_tray_status = new_tray_status
    tray.current_recipe_name = production_line.current_recipe_name
    tray.current_weight = production_line.current_recipe.default_weight
    current_app.logger.info(f"Tray {tray.rfid} at {production_line.line_name}. Current recipe: {production_line.current_recipe_name}")
    return tray
