import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.stats.api as sms
from math import ceil
import descriptive.pyeda as eda
from statsmodels.stats.proportion import proportions_ztest, proportion_confint


ab_testing = pd.read_csv("ab_data.csv")
# print(ab_testing.head())

effect_size = sms.proportion_effectsize(0.13, 0.15)
required_n = sms.NormalIndPower().solve_power(effect_size, power=.8, alpha=.05, ratio=1)
required_n = ceil(required_n)
# print(required_n)
# print(ab_testing.info())

# to make sure all the control group are seeing the old page and vice versa
# crosstab_data = pd.crosstab(ab_testing["group"], ab_testing["landing_page"])
# print(crosstab_data)

session_count = ab_testing["user_id"].value_counts(ascending=False)
# print(session_count)
multi_users = session_count[session_count > 1].count()
# print(f"There are {multi_users} users that appear multiple times in the dataset")

users_to_drop = session_count[session_count > 1].index

ab_testing = ab_testing[~ab_testing["user_id"].isin(users_to_drop)]
# print(f"The update dataset now has {ab_testing.shape[0]} entries.")

control_sample = ab_testing[ab_testing["group"] == "control"].sample(n=required_n, random_state=22)
treatment_sample = ab_testing[ab_testing["group"] == "treatment"].sample(n=required_n, random_state=22)

ab_test = pd.concat([control_sample, treatment_sample], axis=0)
ab_test.reset_index(drop=True, inplace=True)
# print(ab_test)
# print(ab_test["group"].value_counts())

conversion_rates = ab_test.groupby("group")["converted"]

std_p = lambda x: np.std(x, ddof=0)  # std of the proportion
se_p = lambda x: stats.sem(x, ddof=0)  # (std / sqrt(n))

conversion_rates = conversion_rates.agg([np.mean, std_p, se_p])
conversion_rates.columns = ["conversion_rate", "std_deviation", "std_error"]

# print(conversion_rates.round(3))
# title = "Conversion rate by group"
# eda.visualize_basic_bar_plot(ab_test, "converted", "group", title, subtitle="")


control_results = ab_test[ab_test["group"] == "control"]["converted"]
treatment_results = ab_test[ab_test["group"] == "treatment"]["converted"]

n_con = control_results.count()
n_treat = treatment_results.count()

success = [control_results.sum(), treatment_results.sum()]

nobs = [n_con, n_treat]

z_stat, pval = proportions_ztest(success, nobs=nobs)

(lower_con, lower_treat), (upper_con, upper_treat) = proportion_confint(success, nobs, alpha=0.05)

print(f"z statistic : {z_stat:.2f}")
print(f"p-value: {pval:.3f}")
print(f"ci 95% for control group: [{lower_con:.3f}, {upper_con:.3f}]")
print(f"ci 95% for treatment group: [{lower_treat:.3f}, {upper_treat:.3f}]")
