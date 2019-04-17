#!/usr/bin/env python3
#<-------------------------------------------- 100 characters ------------------------------------>|

# Web Sites:
#     US Gov Food Search Site:  https://ndb.nal.usda.gov/ndb/search/list
#     UPC Database Lookup Site: https://www.upcitemdb.com

import os
import pickle
import usda
from usda.client import UsdaClient

# Conversion coefficients to ml:
VOLUME_CONVERSIONS = {
  "cup":    236.58824,
  "floz":    29.57353,
  "oza":     29.57353,
  "litre": 1000.000,
  "ml":       1.00000,
  "pint":   473.17647,
  "quart":  946.35295,
  "tbsp":    14.786765,
  "tsp":      4.9289216,
}

# Conversion coefficients to grams:
MASS_CONVERSIONS = {
  "g":   1.00000,
  "gm":  1.00000,
  "oz": 28.349523,
}

class Day:
    def __init__(self, name):
        # Verify argument types:
        assert isinstance(name, str)

        day = self
        day.recipe_scale_pairs = list()

    def meal(self, recipe, scale=1.0):
        # Verify argument types:
        assert isinstance(recipe, Recipe)
        assert isinstance(scale, float)

        day = self
        day.recipe_scale_pairs.append( (recipe, scale) )

    def process(self, client):
        # Verify argument types:
        assert isinstance(client, usda.client.UsdaClient)

        day = self
        recipe_scale_pairs = day.recipe_scale_pairs
        day_total = Food.empty()
        for recipe, scale in recipe_scale_pairs:
            recipe_total = recipe.process(client, scale)
            day_total += recipe_total * scale
        return day_total

class Food:
    def __init__(self, description, serving_volume, serving_units, serving_mass, calories,
      total_fat, saturated_fat, trans_fat, cholesterol, sodium,
      carbohydrates, dietary_fiber, sugars, protein,
      calcium=None, potassium=None, upc=None, food_id=None):
        # Verify argument types:
        assert isinstance(description, str)
        assert isinstance(serving_volume, float) or isinstance(serving_volume, int)
        assert isinstance(serving_units, str)
        assert isinstance(serving_mass, float)   or isinstance(serving_mass, int)
        assert isinstance(calories, float)       or isinstance(calories, int)
        assert isinstance(total_fat, float)      or isinstance(total_fat, int)
        assert isinstance(saturated_fat, float)  or isinstance(saturated_fat, int)
        assert isinstance(trans_fat, float)      or isinstance(trans_fat, int)
        assert isinstance(cholesterol, float)    or isinstance(cholesterol, int)
        assert isinstance(sodium, float)         or isinstance(sodium, int)
        assert isinstance(carbohydrates, float)  or isinstance(carbohydrates, int)
        assert isinstance(dietary_fiber, float)  or isinstance(dietary_fiber, int)
        assert isinstance(sugars, float)         or isinstance(sugars, int)
        assert isinstance(protein, float)        or isinstance(protein, int)
        assert isinstance(calcium, float)        or isinstance(calcium, int) or calcium is None
        assert isinstance(potassium, float)      or isinstance(potassium, int) or potassium is None
        assert isinstance(upc, str)              or upc is None
        assert isinstance(food_id, int)          or food_id is None

        #print("=>Food.__init__(*, '{0}', ..., food_id={1}, upc={2})".
        #  format( description, food_id, (None if upc is None else "'{0}'".format(upc)) ))

        #serving_units = serving_units.lower()
        serving_units = serving_units.lower()
        scale = 1.0
        density = -1
        if not isinstance(food_id, int):
            scale = 100.0 / serving_mass
        if serving_units in VOLUME_CONVERSIONS:
            milliliters = serving_volume * VOLUME_CONVERSIONS[serving_units]
            density = serving_mass / milliliters
            #print("amount={0} units='{1}' mass={2} ml={3} density={4}".
            #  format(serving_volume, serving_units, serving_mass, milliliters, density))
        #print("Food.__init__():'{0}'\n     sv={1} su='{2}', sm={3}, fi={4} upc={5} scale={6}".
        #  format(description, serving_volume, serving_units, serving_mass, food_id,
        #    (None if upc is None else '{0}'.format(upc)), scale))
        #print("density={0}".format(density))

        if calcium is None:
            calcium = 0.0
        if potassium is None:
            potassium = 0.0

        # Stuff arugments in to *food* (i.e. *self*):
        food = self
        food.description    = description            # Text
        food.serving_volume = serving_volume         # The number of *serving_units* in a serving
        food.serving_units  = serving_units          # The units (e.g. "cup", "tsp", "oz".)
        food.serving_mass   = serving_mass           # The number of grams per serving.
        food.density        = density                # The density of the food (g/ml^3)
        food.calories       = scale * calories       # The energy per 100 grams (kcal)
        food.total_fat      = scale * total_fat      # The total fat per 100 grams (g)
        food.saturated_fat  = scale * saturated_fat  # The staturated fat per 100 grams (g)
        food.trans_fat      = scale * trans_fat      # The tran fat per 100 grams (g)
        food.cholesterol    = scale * cholesterol    # The cholesterol per 100 grams (mg)
        food.sodium         = scale * sodium         # The sodium per 100 grams (mg)
        food.carbohydrates  = scale * carbohydrates  # The total carbohydrates per 100 grams (g)
        food.dietary_fiber  = scale * dietary_fiber  # The dietary fiber per 100 grams (g)
        food.sugars         = scale * sugars         # The surgars per 100 grams (g)
        food.protein        = scale * protein        # The protein per 100 grams (g)
        food.calcium        = scale * calcium        # The calcium per 100 grams (mg)
        food.potassium      = scale * potassium      # The potassium per 100 grams (g)
        food.upc            = upc                    # The UPC code as *str* or *None*
        food.food_id        = food_id                # The USDA food id as *int* or *None*

        #print("<=Food.__init__(*, '{0}', ..., food_id={1}, upc={2})".
        #  format( description, food_id, (None if upc is None else "'{0}'".format(upc)) ))

    def __add__(self, food2):
        # Verify argument types:
        assert isinstance(food2, Food)

        food1 = self
        sum = Food("Total",
          0.0,
          "",
          food1.serving_mass        + food2.serving_mass,
          food1.calories            + food2.calories,
          food1.total_fat           + food2.total_fat,
          food1.saturated_fat       + food2.saturated_fat,
          food1.trans_fat           + food2.trans_fat,
          food1.cholesterol         + food2.cholesterol,
          food1.sodium              + food2.sodium,
          food1.carbohydrates       + food2.carbohydrates,
          food1.dietary_fiber       + food2.dietary_fiber,
          food1.sugars              + food2.sugars,
          food1.protein             + food2.protein,
          calcium=food1.calcium     + food2.calcium,
          potassium=food1.potassium + food2.potassium,
          food_id=-1)
        return sum

    def __mul__(self, scale):
        # Verify argument types:
        assert isinstance(scale, float)

        food = self
        scaled = Food("Scaled",
          0.0,
          "",
          food.serving_mass         * scale,
          food.calories             * scale,
          food.total_fat            * scale,
          food.saturated_fat        * scale,
          food.trans_fat            * scale,
          food.cholesterol          * scale,
          food.sodium               * scale,
          food.carbohydrates        * scale,
          food.dietary_fiber        * scale,
          food.sugars               * scale,
          food.protein              * scale,
          calcium=(food.calcium     * scale),
          potassium=(food.potassium * scale),
          food_id=-1)
        return scaled

    @staticmethod
    def empty():
        return Food("Total", 0, "", 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, upc="", food_id=-1)

    def caloric_fractions_get(self):
        food = self
        total_fat     = food.total_fat
        carbohydrates = food.carbohydrates
        protein       = food.protein
        caloric_grams = total_fat + carbohydrates + protein
        #print("total_fat={0}g carbohydrates={1}g protein={2}g caloric_grams={3}g".
        #  format(total_fat, carbohydrates, protein, caloric_grams))
        fat_fraction           = total_fat     / caloric_grams
        carbohydrates_fraction = carbohydrates / caloric_grams
        protein_fraction       = protein       / caloric_grams
        #print("sum(fractions)={0}".
        #  format(fat_fraction + carbohydrates_fraction + protein_fraction))
        return (fat_fraction, carbohydrates_fraction, protein_fraction)

    def summary_string(self, scale=1.0):
        food = self
        calories              = scale * food.calories
        total_fat             = scale * food.total_fat
        carbohydrates         = scale * food.carbohydrates
        protein               = scale * food.protein
        caloric_grams         = total_fat + carbohydrates + protein
        total_fat_percent     = int(100.0 * total_fat / caloric_grams)
        carbohydrates_percent = int(100.0 * carbohydrates / caloric_grams)
        protein_percent       = int(100.0 * protein / caloric_grams)
        summary ="{0}cal {1}g~={2}(Fat)+{3}(Carb)+{4}g(Prot) (100%~={5}%+{6}%+{7}%)".format(
          int(calories),
          int(caloric_grams),
          int(total_fat),
          int(carbohydrates),
          int(protein),
          total_fat_percent,
          carbohydrates_percent,
          protein_percent,
          scale)
        return summary

    def to_string(self, heading=None, indent=0):
        # Verify argument types:
        assert isinstance(heading, str) or heading is None
        assert isinstance(indent, int) and indent >= 0

        food = self
        lines = list()
        indent *= ' '
        if not heading is None:
            lines.append(heading)
        lines.append("{0}{1}".format(indent,                         food.description))
        lines.append("{0} Calories: {1}".format(indent,              int(food.calories)))
        lines.append("{0}  Total Fat: {1}g".format(indent,           int(food.total_fat)))
        lines.append("{0}   Saturated Fat: {1}g".format(indent,      int(food.saturated_fat)))
        lines.append("{0}   Trans Fat: {1}g".format(indent,          int(food.trans_fat)))
        lines.append("{0}  Cholesterol: {1}mg".format(indent,        int(food.cholesterol)))
        lines.append("{0}  Sodium: {1}mg".format(indent,             int(food.sodium)))
        lines.append("{0}  Total Carbohydrates: {1}g".format(indent, int(food.carbohydrates)))
        lines.append("{0}   Dietary Fiber: {1}g".format(indent,      int(food.dietary_fiber)))
        lines.append("{0}   Total Sugars: {1}g".format(indent,       int(food.sugars)))
        lines.append("{0}  Protein: {1}g".format(indent,             int(food.protein)))
        lines.append("{0}  Calcium: {1}mg".format(indent,            int(food.calcium)))
        lines.append("{0}  Potassium: {1}mg".format(indent,          int(food.potassium)))
        lines.append("{0} {1}".format(indent,                        food.summary_string()))
        lines.append("")
        text = '\n'.join(lines)
        return text

class Ingredient:
    # Conversion coefficients to milliLiters:
    def __init__(self, amount, units, description, food_id=None, upc=None, food=None):
        # Verifya argument types:
        assert isinstance(amount, float)
        assert isinstance(units, str)
        assert isinstance(description, str)
        assert isinstance(food_id, str) or isinstance(food_id, int) or food_id is None
        assert isinstance(upc, str) or upc is None
        assert isinstance(food, Food) or food is None
        count = 0
        count += isinstance(food_id, str) or isinstance(food_id, int)
        count += isinstance(upc, str)
        count += isinstance(food, Food)
        assert count == 1

        # Load arguments into *ingredient* (i.e. *self*):
        ingredient = self
        ingredient.amount      = float(amount)
        ingredient.units       = units.lower()
        ingredient.description = description
        ingredient.food_id     = food_id
        ingredient.upc         = upc
        ingredient.food        = food
        
    def food_lookup(self, client):
        #print("=>Ingredient.food_lookup(*)")

        # Verify argument types:
        assert isinstance(client, UsdaClient)

        # Grap the *food_id* from *ingredient* (i.e. *self*):
        ingredient = self

        food = ingredient.food

        description = ingredient.description
        file_name = "/tmp/" + description.replace(" ", "_") + ".pkl"
        if food is None:
            if os.path.isfile(file_name):
                with open(file_name, "rb") as pickle_file:
                    food= pickle.load(pickle_file)
        if food is None:
            # Initialize all of the *Food* object fields to *None* except *food_id*:
            description    = None
            serving_volume = None
            serving_units  = None
            serving_mass   = None
            calories       = None
            total_fat      = None
            saturated_fat  = None
            trans_fat      = None
            cholesterol    = None
            sodium         = None
            carbohydrates  = None
            dietary_fiber  = None
            sugars         = None
            protein        = None
            calcium        = None
            potassium      = None
            upc            = None
    
            #print("food_id={0} upc={1}".
            #  format(food_id, (None if upc is None else "'{1}'".format(upc)) ))
            food_id = ingredient.food_id
            assert not food_id is None
            search = client.search_foods(food_id, 1)
            food_item = next(search)
            assert isinstance(food_item, usda.domain.Food)
            food_name = food_item.name
            #print("food_name='{0}'".format(food_name))
            #assert(food_id == food_item.id)
            #food_upc_index = food_name.find("UPC: ")
            #food_upc = food_name[food_upc_index + 5:] if food_upc_index >= 0 else None
    
            #print("food_id={0} upc={1}".
            #  format(food_id, (None if upc is None else "'{0}'".format(upc))))
    
            # Get the nutrient report:
            #report_dict = client.get_food_report_raw(ndbno=food_id)
            #assert isinstance(report_dict, dict)
            #pprint.pprint(report_dict)
            #print(raw_report)
    
            report = client.get_food_report(food_id)
            nutrients = list(report.nutrients)
            for nutrient_index, nutrient in enumerate(nutrients):
                # Extract the *nutrient* values:
                nutrient_name = nutrient.name
                nutrient_unit = nutrient.unit
                nutrient_value = nutrient.value
    
                # We only need to grab the *serving_volume*, *serving_units*, and *serving_mass*
                # once:
                if nutrient_index == 0:
                    measures = nutrient.measures
                    #print("measures_type=", type(measures))
                    for measure_index, measure in enumerate(measures):
                        # Get the *serving_volume*, *serving_mass*, and *serving_units*
                        # from *measure*:
                        serving_volume = measure.quantity
                        serving_mass   = float(measure.gram_equivalent)
                        serving_units  = measure.label.lower()
    
                        # Sometimes *serving_units* is has some extra information... Trim it off:
                        space_index = serving_units.find(' ')
                        if space_index >=0:
                            serving_units = serving_units[:space_index]
    
                        # Print out the serving size information:
                        #print("Measure[{3}]  {0}{1} => {2}gm".
                        #  format(serving_volume, serving_units, serving_mass, measure_index))
    
                #print("  {0}: {1}{2}".format(nutrient_name, nutrient_value, nutrient_unit))
                if nutrient_name == "Energy":
                    assert nutrient_unit == "kcal"
                    calories = nutrient_value
                elif nutrient_name == "Total lipid (fat)":
                    assert nutrient_unit == "g"
                    total_fat = nutrient_value
                elif nutrient_name == "Fatty acids, total saturated":
                    assert nutrient_unit == "g"
                    saturated_fat = nutrient_value
                elif nutrient_name == "Fatty acids, total trans":
                    assert nutrient_unit == "g"
                    trans_fat = nutrient_value
                elif nutrient_name == "Cholesterol":
                    assert nutrient_unit == "mg"
                    cholesterol = nutrient_value
                elif nutrient_name == "Sodium, Na":
                    assert nutrient_unit == "mg"
                    sodium = nutrient_value
                elif nutrient_name == "Carbohydrate, by difference":
                    assert nutrient_unit == "g"
                    carbohydrates = nutrient_value
                elif nutrient_name == "Fiber, total dietary":
                    assert nutrient_unit == "g"
                    dietary_fiber = nutrient_value
                elif nutrient_name ==  "Sugars, total":
                    assert nutrient_unit == "g"
                    sugars = nutrient_value
                elif nutrient_name == "Protein":
                    assert nutrient_unit == "g"
                    protein = nutrient_value
                elif nutrient_name == "Potassium, K":
                    assert nutrient_unit == "mg"
                    potassium = nutrient_value
                elif nutrient_name == "Calcium, Ca":
                    assert nutrient_unit == "mg"
                    calcium = nutrient_value
                #else:
                #    print("  -->{0}: {1}{2}".format(nutrient_name, nutrient_value, nutrient_unit))
                    
            food = Food(food_name, serving_volume, serving_units, serving_mass, calories,
              total_fat, saturated_fat, trans_fat, cholesterol, sodium,
              carbohydrates, dietary_fiber, sugars, protein,
              calcium=calcium, potassium=potassium, upc=upc, food_id=food_id)

        with open(file_name, "wb") as pickle_file:
            pickle.dump(food, pickle_file)
        #print("<=Ingredient.food_lookup(*)")
        return food

class Recipe:
    def __init__(self, name):
        # Verify argument types:
        assert isinstance(name, str)

        # Load up *recipe* (i.e. *self*):
        recipe = self
        recipe.name = name
        recipe.ingredients = list()
        
    def ingredient(self, amount, units, description, food_id=None, upc=None, food=None):
        # Verify argument types:
        assert isinstance(amount, float) or isinstance(amount, int)
        assert isinstance(units, str)
        assert isinstance(description, str)
        assert isinstance(food_id, str) or isinstance(food_id, int) or food_id is None
        assert isinstance(upc, str) or upc is None
        assert isinstance(food, Food) or food is None
        count = 0
        count += isinstance(food_id, str) or isinstance(food_id, int)
        count += isinstance(upc, str)
        count += isinstance(food, Food)
        assert count == 1

        # Create *ingredient*:
        ingredient = Ingredient(float(amount), units, description,
          food_id=food_id, upc=upc, food=food)

        # Append *ingredient* to *recipe* (i.e. *self*):
        recipe = self
        recipe.ingredients.append(ingredient)

    def process(self, client, scale=1.0):
        # Verify argument types:
        assert isinstance(client, UsdaClient)
        assert isinstance(scale, float) or isinstance(scale, int)

        #print("=>Recipe.process(*, *, scale={0})".format(scale))

        # Process the *ingredients* in *recipe* (i.e. *self*):
        recipe = self
        print("Recipe: {0}{1}".format(recipe.name,
          ("" if scale == 1.0 else " x {0:.2}".format(scale)) ))
        foods = list()
        total = Food.empty()
        ingredients = recipe.ingredients
        
        total_calories = 0.0
        total_grams = 0.0
        for ingredient_index, ingredient in enumerate(ingredients):
            amount      = ingredient.amount
            units       = ingredient.units
            description = ingredient.description

            #print("Ingredient[{0}] {1}{2} {3} {4}:".
            #  format(ingredient_index, amount, units,
            #   (code if isinstance(code, int) else "'{0}'".format(code)), description))

            food = ingredient.food_lookup(client)
            assert isinstance(food, Food)

            grams = None
            density = None
            if units in VOLUME_CONVERSIONS:
                #print("volume converstion")
                density = food.density
                assert density > 0.0
                milliliters = amount * VOLUME_CONVERSIONS[units]
                grams = density * milliliters
                #print("amount={0} units='{1}' ml={2}, density={3} gm={4}".
                #  format(amount, units, milliliters, density, grams))
            elif units in MASS_CONVERSIONS:
                #print("mass converstion")
                grams = amount * MASS_CONVERSIONS[units]
            else:
                assert False, "No valid conversion for '{0}'".format(units)
            food_scale = grams / 100.0
            #print("grams={0} scale={1}".format(grams, scale))
            scaled_food = food * food_scale
            foods.append(food)

            total_grams += grams
            calories = scaled_food.calories
            total_calories += calories
            print("[{0:>2}] {1:>5}g{2:>5}g{3:>5}cal  {4:.2f} {5} {6}".
              format(ingredient_index, int(grams), int(total_grams), int(calories),
	      amount * scale, units, description))
            #print(scaled_food.to_string())

            total += scaled_food

        print(total.summary_string(scale=scale))
        print("")

        #print("<=Recipe.process(*, *, scale={0})".format(scale))
        return total

def main():
    # Create *chili_recipe*:
    ground_beef = Food("Lean Ground Beef (7% Fat) Crumbles",
      -1, "", 100, 209, 9.48, .241, 3.897, 0, 86, 0, 0, 0, 28.88, calcium=12, potassium=449)
    yellow_onion = Food("Yellow Onion (?)",
      1, "cup", 160, 64, .16, .067, 0, 0, 6, 14.94, 2.7, 6.78, 1.76, calcium=37, potassium=234)
    green_pepper = Food("Green Pepper (11333)",
      1, "cup", 149, 30, 0.25, .086, 0, 0, 3, 6.91, 2.5, 3.58, 0, calcium=15, potassium=261)
    garlic_clove = Food("Raw Garlic Clove (11215)",
      -1, "", 3, 4, 0.1, .003, 0, 0, 1, .99, .1, .03, 0, calcium=5, potassium=12)
    crushed_tomatoes = Food("Sprouts Crushed Roma Tomatoes (646670314612)",
      .25, "cup", 61, 20, 0, 0, 0, 0, 15, 4, 1, 3, 1, calcium=0, potassium=186)
    chicken_stock = Food("Chicken Broth (021130370023)",
      1, "cup", 1360./6., 10, 0, 0, 0, 0, 860, 0, 0, 0, 1, calcium=0, potassium=40)
    tomato_paste = Food("Tomato Paste (096619937295)",
      2, "tbsp", 33, 30, 0, 0, 0, 0, 20, 6, 2, 4, 1, calcium=0, potassium=0)
    red_kidney_beans = Food("Red Kidney Beans (874875007309) Sprouts",
      .5, "cup", 130, 110, 0, 0, 0, 0, 140, 20, 8, 1, 8, calcium=59, potassium=466)
    white_navy_beans = Food("White Navey Beans (072273453821) S&W",
      .5, "cup", 130, 110, 0, 0, 0, 0, 140, 20, 6, 1, 7, calcium=64, potassium=350)
    pinto_beans = Food("Pinto Beans (87487500725) Sprouts",
     .5, "cup", 126, 110, 0, 0, 0, 0, 10, 20, 7, 1, 6, calcium=0, potassium=0)
    black_beans = Food("Black Beans (072273387737) S&W",
      .5, "cup", 130, 110, 0, 0, 0, 0, 140, 21, 10, 1, 7, calcium=44, potassium=410)
    garbonzo_beans = Food("Garbonzo Beans (072273393134) S&W",
     .5, "cup", 130, 120, 2, 0, 0, 0, 140, 20, 6, 1, 20, calcium=25, potassium=240)

    # Spices
    chili_powder = Food("Chili Powder (02009)",
      1, "tsp", 2.7, 8, .39, .066, 0, 0, 77, 1.34, .9, .18, .36,  calcium=9, potassium=53)
    ground_cumin = Food("Ground Cumin (02014)",
      1, "tsp", 2.1, 8, .47, .032, 0, 0, 4, .93, .2, .05, .37, calcium=20, potassium=38)
    crushed_red_pepper = Food("Crushed Red Pepper (02031)",
      1, "tbsp", 5.3,17, .92, .173, 0, 0, 2, 3, 1.4, .55, .64, calcium=3, potassium=107)
    oregano_spice = Food("Oregano Spice (02027)",
     1, "tsp", 1.8, 5, .08, .028, 0, 0, 0, 1.24, .8, .07, .16, calcium=29, potassium=23)
    basil_spice = Food("Basil Spice (02003)",
     1, "tbsp", 4.5, 10, .18, .097, 0, 0, 3, 2.15, 1.7, .08, 1.03, calcium=101, potassium=37)
    coriander_spice = Food("Coriander Space (02013)",
     1, "tbsp", 5, 15, .89, .050, 0, 0, 35, 2.75, 2.1, 0, .62, calcium=13, potassium=63)
    bay_leaf_spice = Food("Bay Leaf Spice (02004)",
     1, "tbsp", 1.8, 6, .15, .041, 0, 0, 0, 1.35, .5, 0, .14, calcium=15, potassium=10)
    black_peper = Food("Black Peper (02030)",
     1, "tbsp", 6.9, 17, .22, .096, 0, 0, 1, 4.41, 1.7, .04, .72, calcium=31, potassium=92)
    
    # "desc", sv_vol, "sv_un", sv_mass,
    # cal, totfat, satf, tranf, chol, sodium, carb, df, sug, prot, calcium=, potassium=)
    # "desc", sv_vol, "sv_un", sv_mass,
    # cal, totfat, satf, tranf, chol, sodium, carb, df, sug, prot, calcium=, potassium=)
 
    chili_recipe = Recipe("Low Carb Chili")
    chili_recipe.ingredient(16, "oz", "7% Lean Ground Beef Crumbles", food=ground_beef)
    chili_recipe.ingredient(1,  "cup",  "Yellow Onion",               food=yellow_onion)
    chili_recipe.ingredient(1,  "cup",  "Green Pepper",               food=green_pepper)
    chili_recipe.ingredient(14, "oz",   "Crushed Tomatoes",           food=crushed_tomatoes)
    chili_recipe.ingredient(1,  "cup",  "Red Kidney Beans",           food=red_kidney_beans)
    chili_recipe.ingredient(1,  "cup",  "Chicken Stock",              food=chicken_stock)
    chili_recipe.ingredient(1,  "tbsp", "Tomato Paste",               food=tomato_paste)
    chili_recipe.ingredient(6,  "g",    "Garlic Cloves (3g ea.)",     food=garlic_clove)
    # Spices:
    chili_recipe.ingredient(1,  "tbsp", "Chili Powder",               food=chili_powder)
    chili_recipe.ingredient(1,  "tbsp", "Ground Cumin",               food=ground_cumin)
    chili_recipe.ingredient(1,  "tbsp", "Red Pepper Flakes",          food=crushed_red_pepper)
    chili_recipe.ingredient(1,  "tsp",  "Ground Coriander",           food=coriander_spice)
    chili_recipe.ingredient(1,  "tsp",  "Oregano Leafs",              food=oregano_spice)
    chili_recipe.ingredient(1,  "tsp",  "Basil Leafs",                food=basil_spice)
    chili_recipe.ingredient(1,  "tsp",  "Bay Leaf (1.8g ea.)",        food=basil_spice)

    omlette_recipe = Recipe("Low Carb Omlette")
    omlette_recipe.ingredient(50,  "g", "Whole Raw Egg",          food_id=45273699)
    omlette_recipe.ingredient(75,  "g", "100% Liquid Egg Whites", food_id=45229243)
    omlette_recipe.ingredient(105, "g", "Sliced White Mushrooms", food_id=45339962)

    shrimp_cocktail_recipe = Recipe("Shrimp Cocktail")
    shrimp_cocktail_recipe.ingredient(30, "g", "Popcorn Shrimp",  food_id=45338991)
    shrimp_cocktail_recipe.ingredient(50, "g", "Stringless Sugar Snap Peas", food_id=45094241)

    dinner_recipe = Recipe("Random Stuff")
    dinner_recipe.ingredient(175, "g", "1% Milk Fat Low Fat Cottage Cheese", food_id=45034735)
    dinner_recipe.ingredient(220, "g", "Oven Roasted Chicken Breast",        food_id=45139627)
    dinner_recipe.ingredient(60,  "g", "Stringless Sugar Snap Peas",         food_id=45094241)
    dinner_recipe.ingredient(230, "g", "Honey Crisp Apples",                 food_id=45351125)

    peanut_bar = Food("Peanut Bar",
      -1, "", 45, 160, 5, 2, 0, 0, 270, 18, 5, 7, 15, potassium=105, upc="646049002812")
    peanut_bar_recipe = Recipe("Peanut Bar")
    peanut_bar_recipe.ingredient(45, "g", "Peanut Bar", food=peanut_bar)

    peanut_bar = Food("Peanut Cocoa Crunch Bar",
      -1, "", 45, 160, 5, 3, 0, 5, 170, 18, 5, 8, 15, upc="646049003406")
    peanut_bar_recipe = Recipe("Peanut Cocoa Crunch Bar")
    peanut_bar_recipe.ingredient(45, "g", "Peanut Cocoa Crunch Bar", food=peanut_bar)

    client = UsdaClient("mQBfPvhuiXk7gZ9gYA8I0gGD3kiKEfQvuDxz04Z8")

    day = Day("Today")
    day.meal(omlette_recipe)
    day.meal(shrimp_cocktail_recipe, 2.0)
    day.meal(chili_recipe, 1./3.)
    day.meal(peanut_bar_recipe)
    day.meal(peanut_bar_recipe)
    day_total = day.process(client)
    print(day_total.to_string())

    #day = Day("Chili Recipe")
    #day.meal(chili_recipe, 2.0)
    #day_total = day.process(client)
    ##print(day_total.to_string())

    #recipe_total = omlette_recipe.process(client)
    #recipe_total = dinner_recipe.process(client)
    return 0

if __name__ == "__main__":
    main()


646049003406
