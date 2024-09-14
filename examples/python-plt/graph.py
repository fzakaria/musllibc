import pandas as pd
from plotnine import *
import numpy as np
from io import StringIO
import matplotlib.pyplot as plt

df = pd.read_csv("./benhmark.csv")

# Calculate speedup
df['Speedup'] = df['Base'] / df['Changed']

# Convert times to milliseconds
df['Base_ms'] = df['Base'] * 1000
df['Changed_ms'] = df['Changed'] * 1000

# Filter benchmarks with execution times > 10ms
df = df[(df['Base_ms'] > 5) | (df['Changed_ms'] > 5)].copy()

# Define significance thresholds
significant_speedup_threshold = 1.02  # Adjust as needed
significant_slowdown_threshold = 0.98  # Adjust as needed

# Determine significance
def significance_category(row):
    if row['Speedup'] >= significant_speedup_threshold:
        return 'Significant Speedup'
    elif row['Speedup'] <= significant_slowdown_threshold:
        return 'Significant Slowdown'
    else:
        return 'Not Significant'

df['Significance'] = df.apply(significance_category, axis=1)

# Filter out non-significant data
df_significant = df[df['Significance'] != 'Not Significant'].copy()

# Reshape data for plotting
df_long = pd.melt(df_significant, id_vars=['Benchmark', 'Speedup', 'Significance'], value_vars=['Base_ms', 'Changed_ms'],
                  var_name='Version', value_name='Time_ms')

# Clean up 'Version' column
df_long['Version'] = df_long['Version'].str.replace('_ms', '')

# Ensure the order of benchmarks is consistent
df_significant['Benchmark'] = pd.Categorical(df_significant['Benchmark'], categories=df_significant['Benchmark'], ordered=True)
df_long['Benchmark'] = pd.Categorical(df_long['Benchmark'], categories=df_significant['Benchmark'], ordered=True)

# Create the plot
p = (
    ggplot(df_long, aes(x='Benchmark', y='Time_ms', fill='Version')) +
    geom_bar(stat='identity', position=position_dodge(width=0.8)) +
    geom_text(
        df_long[df_long['Version'] == 'Base'],
        aes(x='Benchmark', y='Time_ms + 5', label='round(Speedup, 2)', color='Significance'),
        position=position_dodge(width=0.8),
        ha='center',
        va='bottom',
        size=14,
        format_string='{:.2f}'
    ) +
    scale_y_log10() +
    scale_fill_manual(labels = ['With PLT', 'Without PLT'], values=['#1f77b4', '#ff7f0e']) +
    scale_color_manual(values={'Significant Speedup': 'green', 'Significant Slowdown': 'red'}) +
    theme_bw() +
    theme(
        axis_text_x=element_text(rotation=90, hjust=1, size=14),
        figure_size=(16, 10),
        axis_text_y=element_text(size=14),  # Increased y-axis text size
        axis_title_x=element_text(size=16),  # Increased x-axis title size
        axis_title_y=element_text(size=16),  # Increased y-axis title size
        legend_title=element_text(size=16),  # Increased legend title size
        legend_text=element_text(size=14),  # Increased legend text size
        plot_title=element_text(size=18),   # Increased plot title size
        legend_position='top'
    ) +
    labs(
        #title='Benchmark Execution Time Comparison (Significant Changes Only)',
        x='Benchmark',
        y='Execution Time (ms)',
        fill='Version',
        color='Significance'
    )
)

# Display the plot
p.save("python-plt.png", width=16, height=16, dpi=300)