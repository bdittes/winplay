""" Run with `.\run dcf` through PowerShell. """

import pandas as pd

diskontsatz = 0.025
cf = pd.DataFrame(dict(year=range(2020, 2120), cf=[5] * 100))
print(sum(cf["cf"] * 1 / (pow(1 + diskontsatz, cf["year"] - 2020))))
