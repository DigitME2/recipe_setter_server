import logging
from datetime import datetime

from flask import abort, Blueprint, jsonify, request, current_app

from app.models import TransactionsLog, Trays, Antennas
from .extensions import db

bp = Blueprint('rfid', __name__)


@bp.route('/rfid', methods=['POST'])
def rfid_route():
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
    current_app.logger.debug(f"Processing tag {rfid_tag}")
    antenna = Antennas.query.filter_by(antenna_port=antenna_port).first()
    if hasattr(antenna, 'production_line'):
        production_line = antenna.production_line
        current_app.logger.debug(f"Tray {rfid_tag} scanned on production line {production_line.line_name}")
    else:
        current_app.logger.error(f"Could not find production line for Antenna on port {antenna_port}")
        return

    # Gather the valid data to save to database
    tray = Trays.query.filter_by(rfid=rfid_tag).first()
    if not tray:
        current_app.logger.warn("Unknown RFID scanned: " + rfid_tag)
        return
    if antenna.start:
        new_tray_status = f"empty on {production_line.line_name}"
        new_tray_weight = 0
        new_recipe_name = None
    elif antenna.end:
        new_tray_status = "full tray"
        new_tray_weight = production_line.current_recipe.default_weight
        new_recipe_name = production_line.current_recipe_name
    else:
        current_app.logger.error(f"Antenna {antenna_port} was not assigned to start or end")
        return abort(500)

    if tray.current_tray_status == new_tray_status:
        current_app.logger.debug(f"Tray {rfid_tag} is already in this position (ie this is a re-read)")
        # Do nothing if the tray is already in this position (i.e. a re-read)
        return

        # Print some logging info
    if antenna.start:
        current_app.logger.info(f"Tray {rfid_tag} at start of {production_line.line_name}")
    elif antenna.end:
        current_app.logger.info(f"Tray {rfid_tag} at end of {production_line.line_name}")
    else:
        current_app.logger.warn(f"Antenna not assigned to start or end")
    prior_tray_state = tray.current_tray_status
    prior_recipe_name = tray.current_recipe_name

    # Create a new transaction
    transaction = TransactionsLog(transaction_datetime=datetime.utcnow(),
                                  rfid=rfid_tag,
                                  read_point=antenna.position_name,
                                  tray_status=prior_tray_state,
                                  tray_recipe_name=prior_recipe_name,
                                  selected_recipe_name=production_line.current_recipe_name,
                                  weight=new_tray_weight)
    db.session.add(transaction)
    db.session.commit()

    # Edit production line
    if antenna.end:
        production_line.trays_since_change += 1

    # Edit tray
    tray.current_tray_status = new_tray_status
    tray.current_recipe_name = new_recipe_name
    tray.current_weight = new_tray_weight
    db.session.commit()
