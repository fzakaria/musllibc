#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p "python3.withPackages(ps: with ps; [plotnine scipy numpy pandas])"

import pandas as pd
from plotnine import *
import numpy as np
from statistics import geometric_mean
from scipy.stats import t, gmean

# Load the CSV file for Ruby
data_ruby = pd.read_csv('benchmark.csv', header=None, names=['Benchmark', 'Type', 'Time'])

# Separate data into two groups: 'withplt' and 'noplt'
data_withplt_ruby = data_ruby[data_ruby['Type'] == 'withplt']
data_noplt_ruby = data_ruby[data_ruby['Type'] == 'noplt']

# Calculate mean and standard deviation for each benchmark for Ruby
data_withplt_ruby_agg = data_withplt_ruby.groupby('Benchmark').agg(mean=('Time', 'mean'), stdev=('Time', 'std')).reset_index()
data_noplt_ruby_agg = data_noplt_ruby.groupby('Benchmark').agg(mean=('Time', 'mean'), stdev=('Time', 'std')).reset_index()

# Calculate speedup (withplt / noplt) for each benchmark for Ruby
data_withplt_ruby_agg['speedup'] = data_withplt_ruby_agg['mean'] / data_noplt_ruby_agg['mean']

# Compute 95% confidence intervals for speedup for Ruby
z_score = 1.96  # For 95% confidence
data_withplt_ruby_agg['speedup_se'] = np.sqrt((data_noplt_ruby_agg['stdev'] / data_noplt_ruby_agg['mean'])**2 + (data_withplt_ruby_agg['stdev'] / data_withplt_ruby_agg['mean'])**2) * data_withplt_ruby_agg['speedup']
data_withplt_ruby_agg['CI_Lower'] = data_withplt_ruby_agg['speedup'] - z_score * data_withplt_ruby_agg['speedup_se']
data_withplt_ruby_agg['CI_Upper'] = data_withplt_ruby_agg['speedup'] + z_score * data_withplt_ruby_agg['speedup_se']

# Filter out non-significant speedups and slowdowns for Ruby
data_withplt_ruby_agg['significance'] = data_withplt_ruby_agg.apply(lambda row: 'Significant' if row['CI_Lower'] > 1 or row['CI_Upper'] < 1 else 'Not Significant', axis=1)
significant_data_ruby = data_withplt_ruby_agg[data_withplt_ruby_agg['significance'] == 'Significant']

# Load the CSV files for Python
python_withplt = pd.read_csv('../python-plt/withplt.csv')
python_noplt = pd.read_csv('../python-plt/noplt.csv')

# Calculate mean and standard deviation for each benchmark for Python
python_withplt_agg = python_withplt.groupby('Benchmark').agg(mean=('mean', 'mean'), stdev=('stdev', 'mean')).reset_index()
python_noplt_agg = python_noplt.groupby('Benchmark').agg(mean=('mean', 'mean'), stdev=('stdev', 'mean')).reset_index()

# Calculate speedup (withplt / noplt) for each benchmark for Python
python_withplt_agg['speedup'] = python_withplt_agg['mean'] / python_noplt_agg['mean']

# Compute 95% confidence intervals for speedup for Python
python_withplt_agg['speedup_se'] = np.sqrt((python_noplt_agg['stdev'] / python_noplt_agg['mean'])**2 + (python_withplt_agg['stdev'] / python_withplt_agg['mean'])**2) * python_withplt_agg['speedup']
python_withplt_agg['CI_Lower'] = python_withplt_agg['speedup'] - z_score * python_withplt_agg['speedup_se']
python_withplt_agg['CI_Upper'] = python_withplt_agg['speedup'] + z_score * python_withplt_agg['speedup_se']

# Filter out non-significant speedups and slowdowns for Python
python_withplt_agg['significance'] = python_withplt_agg.apply(lambda row: 'Significant' if row['CI_Lower'] > 1 or row['CI_Upper'] < 1 else 'Not Significant', axis=1)
significant_data_python = python_withplt_agg[python_withplt_agg['significance'] == 'Significant']

# Prepare DataFrame for plotting
# Concatenate all significant speedup data points for Ruby and Python
significant_data_ruby['Language'] = 'Ruby'
significant_data_python['Language'] = 'Python'

speedup_data = pd.concat([
    pd.DataFrame({'Benchmark': ['All'] * len(significant_data_ruby), 'Speedup': significant_data_ruby['speedup'], 'Language': 'Ruby'}),
    pd.DataFrame({'Benchmark': ['All'] * len(significant_data_python), 'Speedup': significant_data_python['speedup'], 'Language': 'Python'})
])

# Calculate geometric mean for significant speedups
geometric_mean_ruby = gmean(significant_data_ruby['speedup'])
geometric_mean_python = gmean(significant_data_python['speedup'])

# Print the geometric means
print(f'Geometric Mean Speedup for Ruby: {geometric_mean_ruby}')
print(f'Geometric Mean Speedup for Python: {geometric_mean_python}')

# Plot using plotnine
p = (
    ggplot(speedup_data, aes(x='Language', y='Speedup', fill='Language')) +
    geom_violin(trim=True, scale='width') +
    # stat_summary(fun_y=geometric_mean, geom='point', shape='o', size=3, color='black') +
    # stat_summary(fun_data='mean_cl_boot', geom='errorbar', width=0.2) +
    theme_light() +
    theme(
        axis_text_x=element_text(size=10),
        legend_position='none'
        ) +
    labs(title='', x='', y='Speedup')
)

# Display the plot
p.save("violin_graph.pdf", width=3.33, height=2.22, dpi=600),
