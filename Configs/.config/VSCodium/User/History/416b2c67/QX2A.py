import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

output_folder = "out"
os.makedirs(output_folder, exist_ok=True)


def plot_generation_regplot(
    df: pd.DataFrame, x_variable: str, safe_name: str, folder: str = output_folder
) -> None:
    """
    Plots Generation (Y) against a specific Variable (X) and saves the figure.
    Includes a regression line to show the strength of the relationship.
    """

    safe_name = safe_name.replace(" ", "_").replace("/", "_").lower()
    filename = f"generation_vs_{safe_name}.png"
    save_path = os.path.join(folder, filename)

    plt.figure(figsize=(10, 6))

    sns.regplot(
        data=df,
        x=x_variable,
        y="Generation",
        scatter_kws={"s": 60, "alpha": 0.6, "edgecolor": "w"},
        line_kws={"color": "red", "alpha": 0.5, "linewidth": 2},
    )

    plt.title(f"Generation vs {x_variable}")
    plt.ylabel("Generation (Total)")
    plt.xlabel(x_variable)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    plt.savefig(save_path)
    plt.close()
    print(f"Saved plot: {save_path}")


def plot_dual_axis_ts(
    df: pd.DataFrame, variable_name: str, safe_name: str, folder: str = output_folder, filter: str = None
) -> None:
    """
    Plots Generation on Left Axis and Variable on Right Axis over time.
    """
    safe_name = safe_name.replace(" ", "_").replace("/", "_").lower()
    filename = f"ts_generation_vs_{safe_name}.png"
    save_path = os.path.join(folder, filename)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Axis 1: Generation (Green)
    color1 = "tab:green"
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Generation", color=color1, fontweight="bold")
    ax1.plot(
        df["Date"], df["Generation"], color=color1, linewidth=2, label="Generation"
    )
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.grid(True, alpha=0.3)

    # Axis 2: The Comparison Variable (Blue)
    ax2 = ax1.twinx()
    color2 = "tab:blue"
    ax2.set_ylabel(variable_name, color=color2, fontweight="bold")
    ax2.plot(
        df["Date"],
        df[variable_name],
        color=color2,
        linewidth=2,
        linestyle="--",
        label=variable_name,
    )
    ax2.tick_params(axis="y", labelcolor=color2)

    plt.title(f"Time Series: Generation vs {variable_name}")
    plt.tight_layout()

    plt.savefig(save_path)
    plt.close()
    print(f"Saved time series: {filename}")


def generate_pair_report(
    df: pd.DataFrame, variable_name: str, safe_name: str, index: str = "Date", folder: str = output_folder
) -> None:
    """
    Generates statistics (Yearly/Monthly) for Generation vs Variable
    using the main dataframe directly.
    """
    df["Year"] = df[index].dt.year
    df["Month"] = df[index].dt.month

    safe_name = variable_name.replace(" ", "_").replace("/", "_").lower()

    yearly_sum = df.groupby("Year")[["Generation", variable_name]].sum()
    yearly_sum = yearly_sum.round(3)
    yearly_sum.to_csv(os.path.join(folder, f"report_yearly_sum_{safe_name}.csv"))

    yearly_mean = df.groupby("Year")[["Generation", variable_name]].mean()
    yearly_mean = yearly_mean.round(3)
    yearly_mean.to_csv(os.path.join(folder, f"report_yearly_mean_{safe_name}.csv"))

    monthly_mean = df.groupby("Month")[["Generation", variable_name]].mean()
    monthly_mean = monthly_mean.round(3)
    monthly_mean.to_csv(
        os.path.join(folder, f"report_monthly_seasonality_{safe_name}.csv")
    )

    print(f"Generated reports for: Generation vs {variable_name}")
