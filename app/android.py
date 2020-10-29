from flask import Blueprint, jsonify, request, abort, current_app

from app import db
from app.models import ProductionLines, Recipes
from datetime import datetime

bp = Blueprint('android', __name__)


@bp.route('/get_status', methods=['GET'])
def get_status():
    db.create_all()
    """ Returns a JSON object containing the current recipe and amount of trays passed a production line.
     The production line is found according to the IP of the requesting client"""

    # Get the line corresponding to the device sending the request
    device_ip = request.remote_addr
    prod_line = ProductionLines.query.filter_by(current_device_ip=device_ip).first()
    if not prod_line:
        abort(403)

    # Get the relevent data
    current_recipe_name = prod_line.current_recipe_name or "No Recipe"
    trays_since_change = prod_line.trays_since_change or 0

    # Send the response with the data
    response = jsonify({"trays": trays_since_change, "recipe": current_recipe_name, "line": prod_line.line_name})
    response.status_code = 200
    return response


@bp.route('/recipe_options')
def recipe_options_api():
    """ Returns a list of recipe options as a list of names e.g. ["recipe1", "recipe2"].
    The list is modified according to the IP of the requesting client"""
    all_recipes = Recipes.query.all()
    # Get the production line this device is assigned to
    device_prod_line = ProductionLines.query.filter_by(current_device_ip=request.remote_addr).first()
    if not device_prod_line:
        response = {"recipe_options": ["This device is not assigned to a line"]}
        current_app.logger.warn(f"Recipe options requested by {request.remote_addr} which is not assigned to a line")
        return response
    # Get the correct recipe list from the recipes table
    if device_prod_line.washing:
        recipe_names = [recipe.recipe_name for recipe in all_recipes if recipe.washing]
        current_app.logger.debug(f"Recipe options requested by {request.remote_addr} which is assigned to {device_prod_line.line_name} (washing)")
    elif device_prod_line.bagging:
        recipe_names = [recipe.recipe_name for recipe in all_recipes if recipe.bagging]
        current_app.logger.debug(f"Recipe options requested by {request.remote_addr} which is assigned to {device_prod_line.line_name} (bagging)")
    else:
        recipe_names = []

    # Send the response
    recipe_options = {"recipe_options": recipe_names}
    return jsonify(recipe_options)


@bp.route('/change_recipe', methods=['POST'])
def change_recipe():
    """ Accepts POST requests containing a JSON object in the format {recipe: RECIPE_NAME} and changes the active
    recipe for a production line according to the IP of the client"""

    device_ip = request.remote_addr
    # Get the line corresponding to the device sending the request
    prod_line = ProductionLines.query.filter_by(current_device_ip=device_ip).first()

    # Get the new recipe db entry
    requested_recipe_name = request.json["recipe"]
    new_recipe = Recipes.query.filter_by(recipe_name=requested_recipe_name).first()
    if not new_recipe:
        current_app.logger.error(f"Invalid recipe received by {device_ip}")
        return abort(400, {'message': 'invalid recipe'})

    # Add the changes and commit to the database
    prod_line.last_recipe_change = datetime.utcnow()
    prod_line.trays_since_change = 0
    prod_line.current_recipe_name = new_recipe.recipe_name
    db.session.commit()

    current_app.logger.info(f"Setting recipe to {new_recipe.recipe_name} on line {prod_line.line_name}")

    # Send a success response
    response = jsonify({"message": "recipe changed"})
    response.status_code = 200
    return response
