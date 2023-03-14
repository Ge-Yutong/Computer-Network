import numpy as np
import pandas as pd

data = {'Subscriber Number':['408-554-6805', '408-666-8821', '408-680-8821'], 
        'Technology':['04', '03', '02'],
        'Paid':[1, 0, 1]}

df = pd.DataFrame(data)
df.to_csv('Verification_Database.csv', index=False)
