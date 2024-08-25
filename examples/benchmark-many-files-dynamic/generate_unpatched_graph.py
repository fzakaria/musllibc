#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3Packages.plotnine

import pandas as pd
from plotnine import ggplot, aes, geom_line, labs, theme_minimal, scale_x_log10, scale_y_log10
import plotnine as p9

# Define the data as a list of tuples
data = [
    (1_000_000, 10000, 184.764727182),
    (1_000_000, 1000, 25.641176059),
    (1_000_000, 100, 3.629669525),
    (1_000_000, 10, 0.680910907),
    (1_000_000, 1, 0.486876925),
    (100_000, 10000, 34.015519607),
    (100_000, 100, 0.086994629),
    (100_000, 1000, 1.590814645),
    (100_000, 10, 0.027827711),
    (100_000, 1, 0.021915959000000002),
    (10_000, 100, 0.010736151000000001),
    (10_000, 10000, 23.486871932),
    (10_000, 1000, 0.278427266),
    (10_000, 10, 0.003563282),
    (10_000, 1, 0.002400858),
    (1_000, 100, 0.0059618990000000005),
    (1_000, 10, 0.001176441),
    (1_000, 1000, 0.148139437),
    (1_000, 1, 0.0007510030000000001),
    (100, 100, 0.005365309),
    (100, 10, 0.001058018),
    (100, 1, 0.000649839),
    (10, 10, 0.000968269),
    (10, 1, 0.0007475810000000001),
    (1, 1, 0.0006174920000000001)
]

# Convert the data to a DataFrame
df = pd.DataFrame(data, columns=['total_functions', 'num_shared_objects', 'time'])

# Create the plot
plot = (
    ggplot(df, aes(x='total_functions', y='time', color='factor(num_shared_objects)'))
    + geom_line()
    + scale_y_log10()
    + scale_x_log10(
        breaks=[1, 10, 100, 1000, 10000, 100000, 1000000],  # Logarithmic scale breaks
        labels=['1', '10', '100', '1,000', '10,000', '100,000', '1,000,000']  # Formatted labels
    )
    + labs(
        title="",
        x="Total Functions",
        y="Time (s)",
        color="Shared Objects"
    )
    + p9.theme_light()
)

# Display the plot
plot.save("unpatched_histogram.png", width=8, height=8, dpi=300)