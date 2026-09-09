import pandas as pd
import plotly.express as px


def group_by_col_ref(df_input: pd.DataFrame, col_name: str, min_count_to_keep: int = 1):
    df_gb_top = (
        df_input.groupby([col_name])
        .size()
        .sort_values(ascending=False)
        .rename("count")
        .reset_index()
    )

    df_gb_top = df_gb_top[(df_gb_top["count"] >= min_count_to_keep)]

    df_ret = (
        df_input.groupby([col_name, "is_reference"])
        .size()
        .sort_values(ascending=False)
        .rename("count")
        .reset_index()
    )
    df_ret = df_ret[df_ret[col_name].isin(df_gb_top[col_name].unique())]
    return df_ret


def filter_on_list(
    df_input: pd.DataFrame,
    list_input: list[str] | set[str],
    col_name: str,
    blacklist=True,
):
    if blacklist:
        return df_input[
            df_input[col_name].isna() | (~df_input[col_name].isin(list_input))
        ]
    else:
        return df_input[
            df_input[col_name].isna() | (df_input[col_name].isin(list_input))
        ]


def explode_and_filter_on_list(
    df_input: pd.DataFrame,
    col_name: str,
    black_list_input: set[str] | list[str],
    seaparator=";",
    black_list=True,
):
    """
    Filter all papers that have at least one keywords inside a blacklist
    """
    df_input = df_input.reset_index(drop=True)
    serie_is_topic_in_list = (
        df_input[col_name]
        .str.split(pat=seaparator)
        .explode()
        .str.strip()
        .isin(black_list_input)
        .groupby(level=0)
        .any()
    )
    if black_list:
        return df_input[(~serie_is_topic_in_list) | df_input[col_name].isna()]
    else:
        return df_input[serie_is_topic_in_list | df_input[col_name].isna()]


def explode_and_groupby_topic(
    df_input: pd.DataFrame,
    name_topic_col: str,
    min_count_to_keep=1,
    separator=";",
):
    df_input = df_input[df_input[name_topic_col].notna()].reset_index(drop=True).copy()
    df_input[name_topic_col] = df_input[name_topic_col].str.split(pat=separator)
    df_input = df_input.explode(name_topic_col)
    df_input[name_topic_col] = df_input[name_topic_col].str.strip()
    return group_by_col_ref(df_input, name_topic_col, min_count_to_keep)


def plot_histogram(
    df_input: pd.DataFrame,
    col_name: str,
    min_count_to_keep=1,
    seperator: str = None,
    height=500,
):
    if seperator is None:
        gb = group_by_col_ref(df_input, col_name, min_count_to_keep)
    else:
        gb = explode_and_groupby_topic(df_input, col_name, min_count_to_keep, seperator)
    return px.bar(gb, y=col_name, color="is_reference", x="count", height=height)
