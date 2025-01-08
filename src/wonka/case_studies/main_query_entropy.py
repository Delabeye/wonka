import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from icecream import ic, install

install()


### Local
from wonka.utils import *


def entropy(series: pd.Series):
    normalized_value_counts = series.value_counts(normalize=True)
    individuals = normalized_value_counts.index.values
    p_x = normalized_value_counts.values

    if len(individuals) <= 1:
        return 0

    return -np.sum(p_x * np.log(p_x)) / np.log(len(individuals))


def query_entropy(query_output: pd.DataFrame):
    return np.sum([entropy(query_output[v]) for v in query_output.columns]) / len(
        query_output.columns
    )


if __name__ == "__main__":
    # NOTE for illustration purposes, removed entries associated with fan1/heating_coil1 and temperature1
    # (shows very different entropy values within 1 query)
    path = Path(__file__).parent / "data/coffeemachine_benchmark/req32_nok_output.csv"
    df_query_output = pd.read_csv(path)
    df_query_output.dropna(inplace=True)

    df = df_query_output  # shorthand

    ic(df_query_output)

    H_sys = entropy(df["?sys"])
    H_total = query_entropy(df)

    ic(H_sys, H_total)

    ic([entropy(df.loc[: len(df), c]) for c in df.columns])
    ic([df[c].value_counts(normalize=True).max() for c in df.columns])

    V = len(df.columns)  # number of variables
    R = len(df)  # number of rows

    columns = df.columns
    # columns = ["?actuator"]
    for col in columns:
        fig, ax = plt.subplots(figsize=(8, 12))

        entropy_col = entropy(df[col])
        value_counts = df[col].value_counts(sort=False, normalize=True)
        hist_data = value_counts.to_dict()
        ax.bar(
            hist_data.keys(),
            hist_data.values(),
            width=1.0,
            align="center",
            edgecolor="white",
            linewidth=0.5,
            color="darkblue",
        )

        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        # ax.set_yticklabels(ax.get_yticklabels(), fontsize=18)
        ax.set_yticklabels([])
        ax.set_yticks([])
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, fontsize=20)
        fig.subplots_adjust(bottom=0.35, top=0.99, right=.92, left=0.08)
        fig.suptitle(
            rf"$\bf{{H({col}) = {np.round(entropy_col, 4)}}}$",
            x=0.5,
            y=0.39,
            fontsize=32,
            color="darkorange",
        )

        plt.savefig(f"entropy_{col}.png", dpi=300)

    plt.show()
