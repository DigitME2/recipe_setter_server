from app import create_app
from app.extensions import db
from app.models import ProductionLines, Antennas, Recipes


def create_test_db_entries():
    db.create_all()
    recipe1 = Recipes(recipe_name="Recipe 1", default_weight=10, bagging=True, washing=False)
    recipe2 = Recipes(recipe_name="Recipe 2", default_weight=5, bagging=True, washing=False)
    recipe3 = Recipes(recipe_name="Recipe 3", default_weight=15, bagging=False, washing=True)
    recipe4 = Recipes(recipe_name="Recipe 4", default_weight=20, bagging=False, washing=True)

    db.session.add(recipe1)
    db.session.add(recipe2)
    db.session.add(recipe3)
    db.session.add(recipe4)
    db.session.commit()

    prod_line1 = ProductionLines(line_name="Washing 1", bagging=False, washing=True)
    prod_line2 = ProductionLines(line_name="Washing 2", bagging=False, washing=True)
    prod_line3 = ProductionLines(line_name="Bagging 1", bagging=True, washing=False)
    prod_line4 = ProductionLines(line_name="Bagging 2", bagging=True, washing=False)
    db.session.add(prod_line1)
    db.session.add(prod_line2)
    db.session.add(prod_line3)
    db.session.add(prod_line4)
    db.session.commit()

    antenna1 = Antennas(antenna_port=1, production_line_name="Washing 1", position_name="Washing 1 Start", start=True, end=False)
    antenna2 = Antennas(antenna_port=2, production_line_name="Washing 1", position_name="Washing 1 End", start=False, end=True)
    db.session.add(antenna1)
    db.session.add(antenna2)
    db.session.commit()


app = create_app()
with app.app_context():
    create_test_db_entries()
