import pandas as pd
import pulp as pl

def intersection(l1,l2):
    return list(set(l1) & set(l2))

def difference(l1,l2):
    return list(set(l1) - set(l2))

def get_missing_nutrients(daily, foods):
  return [
    nutrient
    for nutrient in foods
    if nutrient not in ['food_group','name']
    and (foods[nutrient] == 0).all()
  ]

def get_dfs(csv_daily, csv_foods):
    daily = pd.read_csv(csv_daily).sort_values(by='name').set_index('name')
    foods_input = pd.read_csv(csv_foods).sort_values(by='name').set_index('name').fillna(0)

    unnecessary = [
        "chromium_mcg",
        "linoleic_acid_g",
        "iodine_mcg",
        "alpha_linolenic_acid_g",
        "chloride_g",
        "vitamin_b12_mcg",
        "vitamin_d_iu"
    ]
    missing = get_missing_nutrients(daily,foods_input)
    
    excluded = unnecessary + missing

    nutrient_list = difference(daily.index, excluded)

    daily = daily[daily.index.isin(nutrient_list)]
 
    # the `.copy()` is to suppress the pandas `SettingWithCopyWarning`
    foods = foods_input[['food_group']].copy()
    foods['max'] = 10000 # for now, let's say max value is 1kg for all foods
    foods['cost'] = 1
    foods['amount_var'] = foods.apply(
        lambda food: pl.LpVariable(food.name, 0, food['max']),
        axis=1
    )
    
    nutrients_matrix = foods_input[nutrient_list].T
    
    return daily, foods, nutrients_matrix


def add_constraints(daily, foods, nutrients_matrix):
    prob = pl.LpProblem("meal_planner", pl.LpMinimize)
   
    N = nutrients_matrix
    f = foods['amount_var']
    c = foods['cost']
 
    daily['intake'] = N @ f
    cost            = c @ f

    # constraints:
    # should be basically just:
    #   daily['intake'] >= daily['min']
    #   daily['intake'] <= daily['max']
    for min_val, max_val, intake in daily.values.tolist():
        prob += intake >= min_val
 
        # if we could do inf for max_val then we wouldn't need the conditional
        if not pd.isna(max_val):
            prob += intake <= max_val

    # objective:
    prob += cost
 
    return prob
    
    
def get_values(foods_df):
    foods_df['amount'] = foods_df.apply(
          lambda food: pl.value(food['amount_var']),
          axis = 1
    )
    included = foods_df[foods_df['amount'] > 0]
    return included[['amount']]
    
def example():
    return get_dfs("daily_intake.csv", "foods.csv")
  
def full_example():
    daily, foods, nutrients_matrix = example()
    prob = add_constraints(daily, foods, nutrients_matrix)
    status = prob.solve(pl.PULP_CBC_CMD(msg=0))
    return get_values(foods)

def main():
    daily, foods, nutrients_matrix = example()
    n = len(daily.index)
    for i in range(1,n):
        prob = add_constraints(daily.head(i), foods, nutrients_matrix)
        status = prob.solve(pl.PULP_CBC_CMD(msg = 0))
        print("{0}: {1}: {2}".format(i, daily.iloc[i-1]['name'], pl.LpStatus[status]))
        if pl.LpStatus[status] == 'Infeasible':
            break
