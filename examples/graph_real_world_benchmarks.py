#!/usr/bin/env python3
import pandas as pd
import plotnine as p9
from scipy import stats
import numpy as np

# Running the benchmarks give benchmark.json
# the values here are copied.
data = {
    'application': ['openoffice', 'openoffice', 'pynamic', 'pynamic', 'clang', 'clang'],
    'optimization': ['baseline', 'optimized', 'baseline', 'optimized', 'baseline', 'optimized'],
    'execution_time': [
        # openoffice baseline
        [
        0.56628955252,
        0.56454342152,
        0.55912842552,
        0.56332005552,
        0.56618201952,
        0.56271890252,
        0.56419655652,
        0.55784262152,
        0.56011941252,
        0.56221837952,
        0.56186524352,
        0.56797146152,
        0.56325925152,
        0.5694211245199999,
        0.5640646485199999,
        0.56176270052,
        0.56274639352,
        0.5602900145199999,
        0.55842066252,
        0.56307827952
        ],
        # openoffice optimized
        [
        0.50257522752,
        0.49928621852000005,
        0.49682438952,
        0.49403097452000005,
        0.49664117452000006,
        0.49999939352000006,
        0.49638255652,
        0.49274222552,
        0.4977706035200001,
        0.49776738652,
        0.49495923452,
        0.49676841352000006,
        0.49141444252000005,
        0.50004245452,
        0.50082965752,
        0.49319236352,
        0.49163282452,
        0.49645225752000005,
        0.49593909152000004,
        0.49622036152000004
        ],
        # pynamic baseline
        [
        30.47457876646,
        30.63062439946,
        31.247814994459997,
        31.30015320946,
        30.93508028446,
        31.331559053459998,
        31.272156097459998,
        31.76399655446,
        31.130623974459997,
        30.74697911746
        ],
        # pynamic optimized
        [
        4.96586811046,
        4.98863165346,
        4.4806663884599995,
        4.65354016446,
        4.52730198246,
        4.4229917594599995,
        4.96731332546,
        4.67309716446,
        4.647938186459999,
        4.29013629546
        ],
        # clang baseline
        [
        5.83528755544,
        5.82718794444,
        5.82229393544,
        5.82951947344,
        5.82042468644,
        5.829264467440001,
        5.8236957274400005,
        5.82995626644,
        5.81862345244,
        5.82802914944
        ],
        # clang optimized
        [
        4.75388777344,
        4.77707340044,
        4.77469795144,
        4.75316796444,
        4.73212530644,
        4.7316263354400006,
        4.71882420144,
        4.71344291744,
        4.711522496440001,
        4.698419657440001
        ]
    ]
}

df = pd.DataFrame(data)

# Calculate mean, standard error, and confidence interval
def calculate_statistics(times):
    mean = np.mean(times)
    std_err = stats.sem(times)  # Standard error of the mean
    conf_interval = stats.t.interval(0.95, len(times)-1, loc=mean, scale=std_err)  # 95% CI
    return mean, std_err, conf_interval

# Initialize lists to store the computed values
speedup_data = {
    'application': [],
    'speedup_mean': [],
    'conf_low': [],
    'conf_high': []
}

# Iterate over the applications to calculate speedup and confidence intervals
applications = df['application'].unique()

for app in applications:
    # Get baseline and optimized times
    baseline_times = df[(df['application'] == app) & (df['optimization'] == 'baseline')]['execution_time'].values[0]
    optimized_times = df[(df['application'] == app) & (df['optimization'] == 'optimized')]['execution_time'].values[0]

    # Calculate statistics for baseline and optimized
    baseline_mean, baseline_std_err, baseline_conf = calculate_statistics(baseline_times)
    optimized_mean, optimized_std_err, optimized_conf = calculate_statistics(optimized_times)

    print("application", app)
    print("baseline_mean", baseline_mean)
    print("optimized_mean", optimized_mean)
    # Calculate speedup
    speedup_mean = baseline_mean / optimized_mean

    # Calculate the confidence interval for the speedup using error propagation
    speedup_std_err = speedup_mean * np.sqrt((baseline_std_err / baseline_mean)**2 + (optimized_std_err / optimized_mean)**2)
    speedup_conf = stats.t.interval(0.95, len(baseline_times)-1, loc=speedup_mean, scale=speedup_std_err)

    # Store results in the data dictionary
    speedup_data['application'].append(app)
    speedup_data['speedup_mean'].append(speedup_mean)
    speedup_data['conf_low'].append(speedup_conf[0])
    speedup_data['conf_high'].append(speedup_conf[1])

# Create a DataFrame for speedup data
df_speedup = pd.DataFrame(speedup_data)

print(df_speedup)

# Create the plot
plot = (
    p9.ggplot(df_speedup, p9.aes(x='application', y='speedup_mean'))
    + p9.geom_bar(
        stat='identity',
        position='dodge',  # Group bars by application, dodge for side-by-side bars
        width=0.75,
        fill='#66B3FF'
    )
    + p9.scale_y_log10(
        breaks=[1, 2, 4, 6, 8],  # Logarithmic scale breaks
    )
    + p9.annotation_logticks(
        sides = 'l',
    )
    + p9.geom_errorbar(
        p9.aes(
            ymin='conf_low',
            ymax='conf_high'
        ),
        width=0.2,
    )
    + p9.labs(
        x='',
        y='Speedup',
    )
    + p9.theme_light()
)

# Save or display the plot
plot.save('execution_time_speedup_plot.png', dpi=600)
plot
