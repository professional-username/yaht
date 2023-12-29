#!/usr/bin/env python3
import numpy as np
import pandas as pd
import seaborn as sns
import collections.abc
from itertools import product
from matplotlib import pyplot as plt


def plot_results(result_df):
    """Plot results in a figure appropriate for the given dataframe"""
    # First seperate the data by type
    result_df["type"] = result_df["value"].apply(identify_result_type)
    types = set(result_df["type"])
    experiments = set(result_df["experiment"])

    # Then create the plot
    sns.set_theme()
    fig, axes = plt.subplots(len(types), len(experiments))
    axes = np.array(axes)
    axes = np.reshape(axes, [len(types), len(experiments)])
    for e, t in product(enumerate(experiments), enumerate(types)):
        (e, experiment) = e
        (t, data_type) = t
        # Extract the relevant data for the subplot and plot it
        relevant_df = result_df.loc[
            (result_df["experiment"] == experiment) & (result_df["type"] == data_type)
        ]
        # Plot the data on the correct axis
        plot_based_on_type(relevant_df, data_type=data_type, ax=axes[t, e])
        axes[t, e].set_title(experiment)

    return fig


def identify_result_type(result):
    """Identify the category a result falls into to graph it properly"""
    if isinstance(result, (int, float)):
        return "scalar"
    elif isinstance(result, pd.DataFrame):
        return "series"
    elif isinstance(result, (collections.abc.Sequence, np.ndarray)):
        return "distribution"
    else:
        raise ValueError("Unknown result type %s, cannot be graphed" % type(result))


def plot_based_on_type(data_df, data_type, ax):
    """A custom plot that plots a different type of graph depending on the data 'type'"""
    if data_type == "scalar":
        sns.barplot(data=data_df, x="trial", y="value", hue="name", ax=ax)
    elif data_type == "distribution":
        data_df = data_df.explode("value")
        sns.violinplot(data=data_df, x="trial", y="value", hue="name", ax=ax)
    elif data_type == "series":
        # TODO: Rewrite for efficiency
        total_df = pd.DataFrame()
        for i, df in enumerate(data_df["value"]):
            new_df = pd.DataFrame({"x": df.index, "y": df[df.columns[0]]})
            new_df["trial"] = data_df["trial"].iloc[i]
            new_df["name"] = data_df["name"].iloc[i]
            total_df = pd.concat([total_df, new_df])
        sns.lineplot(data=total_df, x="x", y="y", hue="trial", style="name", ax=ax)
