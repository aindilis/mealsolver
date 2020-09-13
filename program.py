import pandas as pd
import pulp as pl

def get_missing_nutrients(daily, foods):
  return [
    nutrient
    for nutrient in foods
    if nutrient not in ['food_group','name']
    and (foods[nutrient] == 0).all()
  ]

def get_dfs(csv_daily, csv_foods):
  daily = pd.read_csv(csv_daily)
  foods = pd.read_csv(csv_foods).fillna(0)

  unnecessary = [
        "chromium_mcg",
        "linoleic_acid_g",
        "iodine_mcg",
        "alpha_linolenic_acid_g",
        "chloride_g",
        "vitamin_b12_mcg",
        "vitamin_d_iu"
    ]
    
  nutritions_list = [i for i in sorted(daily.name.to_list()) if i not in unnecessary]
    
  daily = daily[daily["name"].isin(nutritions_list)]
  daily = daily.sort_values(by="name", ignore_index=True)
  
  foods = foods[["food_group", "name"] + nutritions_list]
  foods['max'] = 10000 # for now, let's say max value is 1kg for all foods
  foods['cost'] = 1
  foods['var'] = foods.apply(
    lambda food: pl.LpVariable(food['name'], 0, food['max']),
    axis=1
  )
  
  missing = get_missing_nutrients(daily,foods)
  daily = daily[~daily["name"].isin(missing)].sort_values(by="name",ignore_index=True)
  
  return daily, foods
 
def add_constraints(daily, foods):
    prob = pl.LpProblem("meal_planner", pl.LpMinimize)
   
    nutrients = foods.drop(columns=['food_group','name','max','cost','var'])

    intake = nutrients.T.dot(foods['var'])
    cost = foods['cost'].dot(foods['var'])


    # constraints:
    for nutrient, min_val, max_val in daily.values.tolist():
        prob += intake[nutrient] >= min_val
 
        # if we could do inf for max_val then we wouldn't need the conditional
        if not pd.isna(max_val):
            prob += intake[nutrient] <= max_val

    # objective:
    prob += cost
 
    return prob
    
    
def get_values(foods_df):
  foods_df['amount'] = foods_df.apply(lambda food: pl.value(food['var']), axis = 1)
  included = foods_df[foods_df['amount'] > 0]
  return included[['name','amount']]
    
def example():
  return get_dfs("daily_intake.csv", "foods.csv")
  
def full_example():
  daily, foods = example()
  prob = add_constraints(daily, foods)
  status = prob.solve(pl.PULP_CBC_CMD(msg=0))
  return get_values(foods)

def main():
    daily, foods = example()
    n = len(daily.index)
    for i in range(1,n):
      prob = add_constraints(daily.head(i), foods)
      status = prob.solve(pl.PULP_CBC_CMD(msg = 0))
      print("{0}: {1}: {2}".format(i, daily.loc[i-1]['name'], pl.LpStatus[status]))
      if pl.LpStatus[status] == 'Infeasible':
        break
