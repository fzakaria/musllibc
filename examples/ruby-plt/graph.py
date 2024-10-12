#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages(ps: with ps; [plotnine scipy numpy pandas])"

import pandas as pd
import numpy as np
from plotnine import *
from scipy.stats import t, gmean

# Read the CSV file
df = pd.read_csv('benchmark.csv', header=None, names=['Benchmark', 'Version', 'Time'])

# Convert Time to float
df['Time'] = df['Time'].astype(float)

# Group by 'Benchmark' and 'Version', compute mean, standard deviation, and sample size
df_grouped = df.groupby(['Benchmark', 'Version']).agg(
    mean_time=('Time', 'mean'),
    stdev_time=('Time', 'std'),
    n=('Time', 'count')
).reset_index()

# Pivot the data to have versions as columns
df_pivot = df_grouped.pivot(index='Benchmark', columns='Version', values=['mean_time', 'stdev_time', 'n'])

# Flatten the MultiIndex columns
df_pivot.columns = ['_'.join(col).strip() for col in df_pivot.columns.values]

# Assign df_pivot to df for consistency
df = df_pivot.reset_index()

# Ensure all necessary columns are present
required_columns = ['mean_time_withplt', 'mean_time_noplt',
                    'stdev_time_withplt', 'stdev_time_noplt',
                    'n_withplt', 'n_noplt']

for col in required_columns:
    if col not in df.columns:
        df[col] = np.nan  # Assign NaN if column is missing

# Calculate speedup (Without PLT / With PLT)
df['Speedup'] = df['mean_time_withplt'] / df['mean_time_noplt']

# Convert times to milliseconds
df['Base_ms'] = df['mean_time_withplt'] * 1000
df['Changed_ms'] = df['mean_time_noplt'] * 1000

# Filter benchmarks with execution times > 5 ms (optional)
# df = df[(df['Base_ms'] > 5) | (df['Changed_ms'] > 5)].copy()

# Convert standard deviations to milliseconds
df['Base_SD_ms'] = df['stdev_time_withplt'] * 1000
df['Changed_SD_ms'] = df['stdev_time_noplt'] * 1000

# Compute standard errors
df['Base_SE_ms'] = df['Base_SD_ms'] / np.sqrt(df['n_withplt'])
df['Changed_SE_ms'] = df['Changed_SD_ms'] / np.sqrt(df['n_noplt'])

# Compute standard error of the speedup using the delta method
df['Speedup_SE'] = np.sqrt(
    (df['Changed_SE_ms'] / df['Base_ms']) ** 2 +
    (df['Changed_ms'] * df['Base_SE_ms'] / df['Base_ms'] ** 2) ** 2
)

# Calculate Normalized Speedup as percentage change
df['Normalized_Speedup'] = (df['Speedup'] - 1) * 100  # In percentage

# Compute standard error of Normalized Speedup
df['Normalized_Speedup_SE'] = df['Speedup_SE'] * 100  # Since we multiplied by 100

# Compute 95% confidence intervals for Normalized Speedup
z_score = 1.96  # For 95% confidence

df['NS_CI_Lower'] = df['Normalized_Speedup'] - z_score * df['Normalized_Speedup_SE']
df['NS_CI_Upper'] = df['Normalized_Speedup'] + z_score * df['Normalized_Speedup_SE']

# Determine significance based on confidence intervals
def significance(row):
    if row['NS_CI_Lower'] > 0:
        return 'Significant Speedup'
    elif row['NS_CI_Upper'] < 0:
        return 'Significant Slowdown'
    else:
        return 'Not Significant'

df['Significance'] = df.apply(significance, axis=1)

# Filter significant benchmarks
df_significant = df[df['Significance'] != 'Not Significant']

# Extract speedup values
speedups = df_significant['Speedup'].values

print(len(speedups))

# Calculate the geometric mean of the speedups
geometric_mean_speedup = gmean(speedups)

# Convert to normalized speedup percentage
normalized_geometric_mean_speedup = (geometric_mean_speedup - 1) * 100  # In percentage

print(f"Geometric Mean Speedup: {geometric_mean_speedup:.4f}")
print(f"Normalized Geometric Mean Speedup: {normalized_geometric_mean_speedup:.2f}%")

# Prepare data for plotting
df_plot = df[['Benchmark', 'Normalized_Speedup', 'NS_CI_Lower', 'NS_CI_Upper', 'Significance']].copy()

df_plot = df_plot[df_plot['Significance'] != 'Not Significant']

# Ensure the order of benchmarks is consistent
df_plot['Benchmark'] = pd.Categorical(df_plot['Benchmark'], categories=df_plot['Benchmark'], ordered=True)

# Map colors based on Significance
color_mapping = {
    'Significant Speedup': 'green',
    'Significant Slowdown': 'red',
    'Not Significant': 'grey'
}

# Calculate the minimum y-axis value to include at least -5%
min_value = df_plot['NS_CI_Lower'].min()
y_axis_min = min(-5, np.floor(min_value / 5) * 5)  # Round down to the nearest multiple of 5%

# Create the plot
p = (
    ggplot(df_plot, aes(x='Benchmark', y='Normalized_Speedup', fill='Significance')) +
    geom_bar(stat='identity', show_legend=False) +
    geom_errorbar(
        aes(ymin='NS_CI_Lower', ymax='NS_CI_Upper'),
        width=0.2
    ) +
    geom_hline(yintercept=0, linetype='dashed', color='black') +
    # Add horizontal line at the geometric mean speedup
    geom_hline(yintercept=normalized_geometric_mean_speedup, linetype='dotted', color='blue') +
    scale_fill_manual(values=color_mapping) +
    scale_y_continuous(
        limits=(y_axis_min, None),  # Set the lower y-axis limit
        breaks=np.unique(np.concatenate([np.arange(y_axis_min, df_plot['NS_CI_Upper'].max() + 1, 5)])),
        labels=lambda l: ["{0:.0f}%".format(v) for v in l]
    ) +
    theme_bw() +
    theme(
        axis_text_x=element_text(rotation=90, hjust=1, size=10),
        figure_size=(16, 10),
        axis_text_y=element_text(size=12),
        axis_title_x=element_text(size=14),
        axis_title_y=element_text(size=14),
        legend_title=element_text(size=12),
        legend_text=element_text(size=10),
        plot_title=element_text(size=16)
    ) +
    labs(
        x='Benchmark',
        y='Normalized Speedup (%)',
        fill='Significance'
    )
)

# Save the plot
p.save("normalized_speedup_bar_chart.png", width=24, height=10, dpi=300)