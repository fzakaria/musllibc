import pandas as pd
import numpy as np
from plotnine import *
from scipy.stats import t, gmean

# Read the CSV files
df_withplt = pd.read_csv("withplt.csv")
df_noplt = pd.read_csv("noplt.csv")

# Merge dataframes on 'Benchmark'
df = pd.merge(df_withplt, df_noplt, on='Benchmark', suffixes=('_withplt', '_noplt'))

# Calculate speedup (Without PLT / With PLT)
df['Speedup'] = df['mean_withplt'] / df['mean_noplt']

# Convert times to milliseconds
df['Base_ms'] = df['mean_withplt'] * 1000
df['Changed_ms'] = df['mean_noplt'] * 1000

# Filter benchmarks with execution times > 5 ms (optional)
df = df[(df['Base_ms'] > 5) | (df['Changed_ms'] > 5)].copy()

# Convert standard deviations to milliseconds
df['Base_SD_ms'] = df['stdev_withplt'] * 1000
df['Changed_SD_ms'] = df['stdev_noplt'] * 1000

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

print(speedups)

# Calculate the geometric mean of the speedups
geometric_mean_speedup = gmean(speedups)

# Convert to normalized speedup percentage
normalized_geometric_mean_speedup = (geometric_mean_speedup - 1) * 100  # In percentage

# Prepare data for plotting
df_plot = df[['Benchmark', 'Normalized_Speedup', 'NS_CI_Lower', 'NS_CI_Upper', 'Significance']].copy()

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
        breaks=np.unique(np.concatenate([np.arange(-6, 6, 1), np.arange(y_axis_min, df_plot['NS_CI_Upper'].max() + 1, 5)])),
        labels=lambda l: ["{0:.0f}%".format(v) for v in l]
    ) +
    scale_fill_manual(values=color_mapping) +
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
        # title='Normalized Speedup of Benchmarks (With 95% Confidence Intervals)',
        x='Benchmark',
        y='Normalized Speedup (%)',
        fill='Significance'
    )
)

# Save the plot
p.save("normalized_speedup_bar_chart.png", width=16, height=10, dpi=300)
