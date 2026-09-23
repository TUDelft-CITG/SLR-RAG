"""Parse a boolean research query, evaluate it on abstracts, and draw a treemap.

The query '("medicine" OR "health") AND ("brain")' is parsed into a tree
(leaf nodes are keywords, inner nodes are AND/OR). Each node becomes a boolean
column of the dataframe, the dataframe is aggregated per node (number of
matching abstracts, parent node), and the result is drawn as a plotly treemap.

Run with: uv run python -m slrrag.toolbox.query_treemap
"""

import re

from nltk.stem import PorterStemmer
import pandas as pd
import plotly.express as px

QUERY = '("medicine" OR "health") AND ("brain")'

_STEMMER = PorterStemmer()


def stem_text(text: str) -> str:
    """Lowercase `text`, split it into words, and stem each word.

    Returns the stems joined by spaces ("" for non-string input).
    """
    if not isinstance(text, str):
        return ""
    return " ".join(_STEMMER.stem(word) for word in re.findall(r"\w+", text.lower()))


def stem_pattern(keyword: str) -> str:
    """Regex matching `keyword` (stemmed) as whole words inside stemmed text."""
    words = re.findall(r"\w+", keyword.lower())
    if not words:
        # Keyword without word characters (e.g. "c++"): match it literally
        return rf"\b{re.escape(keyword.lower())}\b"
    stems = [_STEMMER.stem(word) for word in words]
    return r"\b" + r" ".join(re.escape(stem) for stem in stems) + r"\b"


# ---------------------------------------------------------------------------
# 1. Parser: query string -> tree
# ---------------------------------------------------------------------------
class Leaf:
    def __init__(self, keyword: str):
        self.keyword = keyword
        # Column name: spaces (and any whitespace) inside keywords become "_"
        self.name = re.sub(r"\s+", "_", keyword)


class Inner:
    def __init__(self, op: str, index: int, children: list):
        self.op = op  # "AND" or "OR"
        self.children = children
        # Unique index per operator, e.g. "AND_1", "OR_3"
        self.name = f"{op}_{index}"


def tokenize(query: str) -> list[str]:
    return re.findall(r'\(|\)|"[^"]*"|AND|OR', query)


def parse_query(query: str):
    """Recursive-descent parser. AND binds tighter than OR (parentheses override)."""
    tokens = tokenize(query)
    pos = 0
    op_counts = {"AND": 0, "OR": 0}

    def make_inner(op: str, children: list) -> Inner:
        # Assign a unique index per operator, e.g. "AND_1", "OR_3"
        op_counts[op] += 1
        return Inner(op, op_counts[op], children)

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def parse_or():
        nonlocal pos
        children = [parse_and()]
        while peek() == "OR":
            pos += 1
            children.append(parse_and())
        return children[0] if len(children) == 1 else make_inner("OR", children)

    def parse_and():
        nonlocal pos
        children = [parse_factor()]
        while peek() == "AND":
            pos += 1
            children.append(parse_factor())
        return children[0] if len(children) == 1 else make_inner("AND", children)

    def parse_factor():
        nonlocal pos
        token = peek()
        if token == "(":
            pos += 1
            node = parse_or()
            if peek() != ")":
                raise ValueError(f"Expected ')' at token {pos} in {tokens!r}")
            pos += 1
            return node
        if token and token.startswith('"'):
            pos += 1
            return Leaf(token.strip('"'))
        raise ValueError(f"Unexpected token {token!r} at position {pos} in {tokens!r}")

    tree = parse_or()
    if pos != len(tokens):
        raise ValueError(f"Trailing tokens {tokens[pos:]!r} in query: {query!r}")
    return tree


# ---------------------------------------------------------------------------
# 2. and 3. One boolean column per node (leaves first, then inner nodes)
# ---------------------------------------------------------------------------
def add_node_columns(
    df: pd.DataFrame,
    node,
    columns: str | list[str] = "abstract",
    binary_columns: str | list[str] | None = None,
    stemming: bool = True,
    stemmed: dict[str, pd.Series] | None = None,
    parent_name: str = "",
) -> list[dict]:
    """Add a boolean column for `node` (and its subtree) to `df`.

    `columns` is one or more dataframe columns searched for leaf keywords
    (a leaf matches if the keyword appears in any of them). With
    `stemming=True` (default), keywords are matched on stemmed text with
    word boundaries, so "medicine" matches "medicines" but not
    "biomedicine"; with `stemming=False`, keywords are matched as plain
    lowercase substrings.

    `binary_columns` is one or more boolean dataframe columns; for each of
    them, the returned records carry the number of rows where the node
    matches and the binary column is True.

    `stemmed` maps a column name to its stemmed text (see `stem_text`); it
    is computed once per top-level call and threaded through the recursion.

    Returns the list of node records (name, parent, count) for the subtree.
    """
    columns = [columns] if isinstance(columns, str) else columns
    binary_columns = (
        []
        if binary_columns is None
        else [binary_columns]
        if isinstance(binary_columns, str)
        else list(binary_columns)
    )
    if stemming and stemmed is None:
        # Precompute the stemmed text once per call, not once per keyword
        stemmed = {col: df[col].map(stem_text) for col in columns}
    records = []
    if isinstance(node, Leaf):
        if stemming:
            pattern = stem_pattern(node.keyword)
            matches = stemmed[columns[0]].str.contains(pattern, regex=True, na=False)
            for col in columns[1:]:
                matches |= stemmed[col].str.contains(pattern, regex=True, na=False)
        else:
            keyword = node.keyword.lower()
            matches = (
                df[columns[0]].str.lower().str.contains(keyword, regex=False, na=False)
            )
            for col in columns[1:]:
                matches |= (
                    df[col].str.lower().str.contains(keyword, regex=False, na=False)
                )
        df[node.name] = matches
    else:
        # Children first: an inner node combines the boolean columns of its children
        for child in node.children:
            records.extend(
                add_node_columns(
                    df,
                    child,
                    columns=columns,
                    binary_columns=binary_columns,
                    stemming=stemming,
                    stemmed=stemmed,
                    parent_name=node.name,
                )
            )
        if node.op == "AND":
            df[node.name] = df[[c.name for c in node.children]].all(axis=1)
        else:  # OR
            df[node.name] = df[[c.name for c in node.children]].any(axis=1)

    record = {
        "node": node.name,
        "parent": parent_name,  # "" for the root node
        "count": int(df[node.name].sum()),
    }
    # For each binary column: number of rows matching this node AND the binary column
    for col in binary_columns:
        record[col] = int((df[node.name] & df[col].fillna(False).astype(bool)).sum())
    records.append(record)
    return records


# ---------------------------------------------------------------------------
# 4. Aggregate by node
# ---------------------------------------------------------------------------
def aggregate_by_node(
    df: pd.DataFrame,
    tree,
    columns: str | list[str] = "abstract",
    binary_columns: str | list[str] | None = None,
    stemming: bool = True,
) -> pd.DataFrame:
    records = add_node_columns(
        df.copy(),
        tree,
        columns=columns,
        binary_columns=binary_columns,
        stemming=stemming,
        parent_name="",
    )
    return pd.DataFrame.from_records(
        sorted(records, key=lambda r: (r["parent"] == "", r["parent"], r["node"]))
    )


# ---------------------------------------------------------------------------
# 5. Treemap
# ---------------------------------------------------------------------------
def treemap(
    agg: pd.DataFrame,
    title: str | None = None,
    width: int | None = None,
    height: int | None = None,
):
    # Columns besides node/parent/count are binary-column counts -> show on hover
    binary_cols = [c for c in agg.columns if c not in ("node", "parent", "count")]
    fig = px.treemap(
        agg,
        names="node",
        parents="parent",
        values="count",
        color="count",
        color_continuous_scale="Blues",
        custom_data=binary_cols,
        title=title if title is not None else "Matching abstract/title per query node",
        width=width,
        height=height,
    )
    hovertemplate = "%{label}<br>matching: %{value}"
    hovertemplate += "".join(
        f"<br>{col}: %{{customdata[{i}]}}" for i, col in enumerate(binary_cols)
    )
    fig.update_traces(
        texttemplate="%{label}<br>%{value} matches",
        hovertemplate=hovertemplate + "<extra></extra>",
    )
    return fig


def main():
    # Sample data: in real use, replace with your own dataframe of titles/abstracts
    df = pd.DataFrame(
        {
            "title": [
                "Advances in brain medicine",
                "Medicine in general practice",
                "Exercise and the brain",
                "Health economics",
                "Code generation with LLMs",
                "Preventive medicine and brain health",
                "Gut microbiome and nutrition",
                "Digital brain monitoring",
            ],
            "abstract": [
                "New advances in brain medicine and public health policy.",
                "This article studies medicine in general practice.",
                "The brain responds to physical exercise.",
                "Health economics and insurance systems.",
                "Machine learning for code generation.",
                "Brain health: a review of preventive medicine.",
                "A study of nutrition and the gut microbiome.",
                "Digital health tools for monitoring the brain.",
            ],
            "is_reference": [True, False, True, True, False, True, False, True],
        }
    )

    tree = parse_query(QUERY)

    # Search the keywords in one or more columns: "title", ["title", "abstract"], ...
    # binary_columns adds, per node, the number of matching rows where each
    # binary column is True (here: rows that are references).
    agg = aggregate_by_node(
        df,
        tree,
        columns=["title", "abstract"],
        binary_columns=["is_reference"],
    )
    print("Per-node boolean columns added to the dataframe:")
    print(df.to_string(index=False))
    print()
    print("Aggregation by node (parent='' for the root, is_reference =")
    print("number of matching rows where is_reference is True):")
    print(agg.to_string(index=False))

    fig = treemap(
        agg,
        title=f"Query tree: {QUERY}",
        width=900,
        height=600,
    )
    fig.write_html("query_treemap.html")
    print("\nTreemap written to query_treemap.html")


if __name__ == "__main__":
    main()
