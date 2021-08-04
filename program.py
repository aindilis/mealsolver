import pandas as pd
import pulp as pl

class NutrientRequirements:
    def __init__(self, csv, unnecessary = []):
        self.df = pd.read_csv(csv)          \
                    .sort_values(by='name') \
                    .set_index('name')

        self.unnecessary = unnecessary

    def parse_units(self):
        pass

class FoodNutrients:
    def __init__(self,csv):
        self.df = pd.read_csv(csv)          \
                    .sort_values(by='name') \
                    .set_index('name')      \
                    .fillna(0)
        self.df['max'] = 10000 # for now, let's say max value is 1kg for all foods
        self.df['cost'] = 1
        self.df['amount_var'] = self.df.apply(
            lambda food: pl.LpVariable(food.name, 0, food['max']),
            axis=1
        )

    def missing_nutrients(self):
        non_nutrient_columns = ['name', 'food_group']
        return {
            nutrient
            for nutrient in self.df
            if nutrient not in non_nutrient_columns
            and (self.df[nutrient] == 0).all()
        }

class Log:
    def __init__(self,csv):
        self.df = pd.read_csv(csv)

class Problem:
    def __init__(self, nutrient_table, food_table):
        self.excluded = nutrient_table.unnecessary | food_table.missing_nutrients()
        self.included = set(nutrient_table.df.index) - self.excluded
        self.nutrient_table = nutrient_table.df[nutrient_table.df.index.isin(self.included)].copy()
        self.food_table = food_table
        self.nutrient_matrix = self.food_table.df[self.included].T
        self.add_constraints()

    def add_constraints(self):
        self.prob = pl.LpProblem("meal_planner", pl.LpMinimize)

        N = self.nutrient_matrix
        f = self.food_table.df['amount_var']
        c = self.food_table.df['cost']

        # @ is Pandas operator for matrix multiplication / dot product
        self.nutrient_table['intake']   = N @ f
        self.cost                       = c @ f

        # constraints:
        # should be basically just:
        #   daily['intake'] >= daily['min']
        #   daily['intake'] <= daily['max']

        # or:
        # daily['min'] <= N @ f <= daily['max']
        # minimize(c @ f)
        for min_val, max_val, intake in self.nutrient_table.values.tolist():
            self.prob += intake >= min_val

            # if we could do inf for max_val then we wouldn't need the conditional
            if not pd.isna(max_val):
                self.prob += intake <= max_val

        # objective:
        self.prob += self.cost

    def solve(self):
        status = self.prob.solve(pl.PULP_CBC_CMD(msg=0))
        foods_df = self.food_table.df
        foods_df['amount'] = foods_df.apply(
              lambda food: pl.value(food['amount_var']),
              axis = 1
        )
        included = foods_df[foods_df['amount'] > 0]
        self.recipe = included[['amount']].copy()


def test():
    nutrient_table = NutrientRequirements(
        'daily_intake.csv',
        {
            "chromium_mcg",
            "linoleic_acid_g",
            "iodine_mcg",
            "alpha_linolenic_acid_g",
            "chloride_g",
            "vitamin_b12_mcg",
            "vitamin_d_iu"
        }
    )
    food_table = FoodNutrients('foods.csv')
    return Problem(nutrient_table, food_table)

def test2():
    return Log('test_log.csv').df


def test3():
    return pd.read_csv("test_nutrient_profiles.csv")
