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

# Calculate 95% confidence interval for each command using Student's t-test
def student_t_confidence_interval(data, confidence=0.95):
    n = len(data)  # Number of data points
    mean = np.mean(data)  # Mean of the data
    stderr = stats.sem(data)  # Standard error of the mean (SEM)
    t_value = stats.t.ppf((1 + confidence) / 2., n - 1)  # t-value for the given confidence level and degrees of freedom (n-1)
    margin_of_error = t_value * stderr  # Margin of error
    return margin_of_error  # Return the margin of error as the confidence interval

# Calculate mean, confidence interval, and speedup
baseline_mean = df['mean'].iloc[1]  # Use the mean of the second command as the baseline for speedup calculation
df['stdev'] = df['times'].apply(lambda x: np.std(x, ddof=1))  # Calculate standard deviation for each command
df['95%_ci'] = df['times'].apply(lambda x: student_t_confidence_interval(x))  # Calculate 95% confidence interval for each command
df['speedup'] = baseline_mean / df['mean']  # Calculate speedup by dividing baseline mean by each command's mean

# Function to calculate the confidence interval for the speedup
def speedup_confidence_interval(baseline, baseline_ci, mean, mean_ci):
    # Using error propagation formula for division:
    # If Z = A / B, then the relative error of Z is given by:
    # (dZ / Z) = sqrt((dA / A)^2 + (dB / B)^2)
    # Where dA and dB are the absolute errors (confidence intervals) of A and B, respectively.
    relative_error = np.sqrt((baseline_ci / baseline) ** 2 + (mean_ci / mean) ** 2)  # Calculate relative error using error propagation formula
    speedup_ci = relative_error * (baseline / mean)  # Calculate absolute confidence interval for speedup
    return speedup_ci

# Apply the speedup confidence interval calculation to each row
df['speedup_95%_ci'] = df.apply(lambda row: speedup_confidence_interval(baseline_mean, df['95%_ci'].iloc[0], row['mean'], row['95%_ci']), axis=1)

# Display results
df['mean_with_ci'] = df.apply(lambda row: f"{row['mean']:.2f} ± {row['95%_ci']:.2f}", axis=1)  # Format mean with confidence interval
df['speedup_with_ci'] = df.apply(lambda row: f"{row['speedup']:.2f} ± {row['speedup_95%_ci']:.2f}", axis=1)  # Format speedup with confidence interval

# Print the final DataFrame with command, mean, speedup, and their respective confidence intervals
print(df[['command', 'stdev', 'mean_with_ci', 'speedup_with_ci']])