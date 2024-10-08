#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages(ps: with ps; [scipy numpy pandas])"

import json
import pandas as pd
import numpy as np
from scipy import stats
import sys
import os

# Load JSON data from the file specified in argv
with open(sys.argv[1], 'r') as file:
    json_data = file.read()

data = json.loads(json_data)

# Create a DataFrame from the results
df = pd.DataFrame(data['results'])

# Strip common prefix from command paths
df['command'] = df['command'].apply(lambda x: os.path.basename(x))

# Calculate speedup using the mean of the first command as baseline
baseline_mean = df['mean'].iloc[0]
df['speedup'] = baseline_mean / df['mean']

# Calculate 95% confidence interval for each command using Student's t-test
def student_t_confidence_interval(data, confidence=0.95):
    n = len(data)
    mean = np.mean(data)
    stderr = stats.sem(data)
    t_value = stats.t.ppf((1 + confidence) / 2., n - 1)
    margin_of_error = t_value * stderr
    return margin_of_error

df['95%_ci'] = df['times'].apply(lambda x: student_t_confidence_interval(x))

df['mean_with_ci'] = df.apply(lambda row: f"{row['mean']} ± {row['95%_ci']}", axis=1)

# Display results
print(df[['command', 'mean', 'speedup', 'mean_with_ci']])