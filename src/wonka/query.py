"""

Querying engine

"""
from __future__ import annotations

### Local
from wonka.utils import *


@dataclass
class Query:
    def __init__(self, path_to_query_file: str | Path) -> None:
        self._query = self._load_query(path_to_query_file)

    def _load_query(self, path_to_query: str | Path) -> Query:
        """load a query file (.rq)"""
        return "".join(open(str(path_to_query)))

    def __repr__(self) -> str:
        return str(self._query)


# def load_query(path_to_query: str | Path) -> Query:
#     """load a query file (.rq)"""
#     return "".join(open(str(path_to_query)))


def vars_from_query(query: Query | str):
    """TODO /!\ if "SELECT *" : order does not match the one used in owlready2"""
    return list(dict.fromkeys(re.findall(r"\?\b\w+\b", str(query))))


def sparql(
    query: Query | str,
    world: World = default_world,
    kg=None,
) -> pd.DataFrame:
    """Evaluate a SPARQL query on a world (containing an ontology)

    Parameters
    ----------
    query : Query | str
        query to run
    world : World, optional
        world containing the ontology, by default default_world
    kg : KnowledgeGraph | QueryGraph, optional
        restrict to a specific knowledge graph (or instantiated query graph)
        (subgraph of the ontology-inferred knowledge graph), by default None

    Returns
    -------
    pd.DataFrame
        query results as a DataFrame (each column corresponds to a variable)
    """

    ### Run SPARQL query
    query_results = [
        [format_iri(indiv) for indiv in row] for row in list(world.sparql(str(query)))
    ]
    query_vars = vars_from_query(str(query))
    ### Turn query results into DataFrame
    fetchvar = lambda i: f"x{i}" if query_vars is None else query_vars[i]
    # add missing values as the variable's name
    if query_results:
        for icol, var in enumerate(query_vars):
            if icol >= np.array(query_results).shape[1]:
                for irow in range(len(query_results)):
                    query_results[irow].append(var)
    # convert to DataFrame
    if query_results:
        df_query_results = pd.DataFrame(
            {
                fetchvar(i): row
                for i, row in enumerate(np.array(query_results).T.tolist())
            }
        )
        ### Drop rows with instances which do not belong to the knowledge or query graph
        if kg is not None:
            kg_instances = set(map(str, kg.nodes())) | getattr(kg, "_trimmed", set())
            _in_kg = lambda instance: str(instance) in kg_instances | {"nan"}
            rows_to_del = []
            for i_row, row in df_query_results.iterrows():
                if np.any([not _in_kg(instance) for instance in row]):
                    rows_to_del.append(i_row)
            df_query_results = df_query_results.drop(rows_to_del)
        return df_query_results
    return pd.DataFrame(columns=query_vars)
