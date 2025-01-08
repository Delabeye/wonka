"""

Development of the WONKA pipeline

[pre-requisite]
    a. Identify target applications (relevant laboratory systems and industrial systems)
    b. Ellicite requirements (e.g., using MBSE analysis)
    c. Design and instantiate an ontology (e.g., using Protégé), save post-reasoning (.owl)
    d. Translate requirements into sparql queries, save (.rq)

[STEP 1] --- OWL to Knowledge Graph ---
    a. Compute the knowledge graph
    b. Divide the knowledge graph into knowledge subgraphs (systems/use cases)
    c. Evaluate semantic similarity between knowledge subgraphs (systems/use cases)

[STEP 2] --- SPARQL to Query Graph ---
    a. Compute query graph from a sparql query
    b. Query
    c. Instantiate query graph with the results of the query

[STEP 3] --- Helper Graph ---
    a. Run ok/nok queries; compute & instantiate query graphs
    b. Solve (find missing & erroneous nodes or links)
    c. Project query results `qres_nok` onto the knowledge graph `KG`

[STEP 4] --- Validation and Scalability metrics ---
    a. Run degrees of validation and scalability


NOTE
- OWL file name must match the ontology's name (e.g. `http://localhost/wonka` iri -> wonka.owl)
- Same goes for sparql queries' shorthand notations (e.g., `wonka:http://localhost/wonka` must be used for concepts/properties related to `wonka`)

"""

### Local
from wonka.utils import *
from wonka.visualisation import viz_nx_graph
from wonka.query import Query, sparql

path_to_owl = Path(__file__).parent / "data/wonka_case_study/ontology/wonka.owl"
path_to_queries = Path(__file__).parent / "data/wonka_case_study/query"
path_to_results = Path(__file__).parent / "data/wonka_case_study/results"

world = default_world
onto = world.get_ontology(str(path_to_owl)).load()


""" ------------------------------------------------ """
""" ------------------   STEP 1   ------------------ """
""" ------------------------------------------------ """

####################################################
###
###     STEP 1a: compute KG
###

from wonka.representation import KnowledgeGraph

KG = KnowledgeGraph(onto)

if disp_KG := True:
    print(f"Knowledge Graph: {str(KG)}")
    viz_nx_graph(KG, save_as=path_to_results / "KG")


####################################################
###
###     STEP 1b: divide KG
###

subkgs = KG.divide(
    border_cls=[
        "wonka.Approach_to_Validate",
        "wonka.Accuracy",
        "wonka.Requirement",
    ],
    key_cls=["wonka.Laboratory", "saref4inma.Factory"],
)

lab_systems = {
    s: subkgs[s]
    for s in [
        "wonka.LABORATORY_CoffeeMachine",
        "wonka.LABORATORY_3Dprinter",
        "wonka.LABORATORY_6axisRobot",
    ]
}

ind_systems = {
    s: subkgs[s] for s in ["wonka.CHOCOLATE_FACTORY", "wonka.VEHICLE_TESTBED"]
}


if disp_subkgs := True:
    for skg_id, SKG in subkgs.items():
        print(f"Subgraph {skg_id}: {str(SKG)}")
        viz_nx_graph(SKG, save_as=path_to_results / skg_id)

####################################################
###
###     STEP 1c: semantic similarity
###

from wonka.metrics import HeterogeneousLinSimilarity


sim = HeterogeneousLinSimilarity(onto)

if study_wonka_intrinsic_similarity := True:
    print("\n\nSemantic similarity:\n")

    lab_systems_labels = [
        "wonka.LABORATORY_CoffeeMachine",
        "wonka.LABORATORY_3Dprinter",
        "wonka.LABORATORY_6axisRobot",
    ]
    # lab_systems = [subkgs[s] for s in lab_systems_labels]
    lab_systems = {s: subkgs[s] for s in lab_systems_labels}

    ind_systems_labels = ["wonka.CHOCOLATE_FACTORY", "wonka.VEHICLE_TESTBED"]
    # ind_systems = [subkgs[s] for s in ind_systems_labels]
    ind_systems = {s: subkgs[s] for s in ind_systems_labels}

    ### indsys vs labsys
    indlabsys_matrix = np.matrix(
        [
            [sim.sim_subkgs([sys1, sys2]) for sys2 in lab_systems.values()]
            for sys1 in ind_systems.values()
        ]
    )
    df_indlabsys = pd.DataFrame(
        indlabsys_matrix, columns=lab_systems_labels, index=pd.Index(ind_systems_labels)
    )
    print(tabulate(df_indlabsys, headers="keys", tablefmt="psql"))

    ### labsys vs labsys
    labsys_matrix = np.matrix(
        [
            [sim.sim_subkgs([sys1, sys2]) for sys2 in lab_systems.values()]
            for sys1 in lab_systems.values()
        ]
    )
    df_labsys = pd.DataFrame(
        labsys_matrix, columns=lab_systems_labels, index=pd.Index(lab_systems_labels)
    )
    print(tabulate(df_labsys, headers="keys", tablefmt="psql"))

    ### indsys vs indsys
    indsys_matrix = np.matrix(
        [
            [sim.sim_subkgs([sys1, sys2]) for sys2 in ind_systems.values()]
            for sys1 in ind_systems.values()
        ]
    )
    df_indsys = pd.DataFrame(
        indsys_matrix, columns=ind_systems_labels, index=pd.Index(ind_systems_labels)
    )
    print(tabulate(df_indlabsys, headers="keys", tablefmt="psql"))

    ### --- save ---
    df_labsys.to_csv(path_to_results / "labsys_vs_labsys.csv", sep="\t", mode="w")
    df_indsys.to_csv(path_to_results / "indsys_vs_indsys.csv", sep="\t", mode="w")
    df_indlabsys.to_csv(path_to_results / "indsys_vs_labsys.csv", sep="\t", mode="w")


""" ------------------------------------------------ """
""" ------------------   STEP 2   ------------------ """
""" ------------------------------------------------ """


####################################################
###
###     STEP 2a: compute qKG
###

from wonka.representation import QueryGraph

ID_query = 41
query = Query(path_to_queries / f"req_{ID_query}_ok.rq")

qKG = QueryGraph(query)

if disp_qKG := True:
    print("\n\nQuery Knowledge Graph:")
    print(f"req_{ID_query}_ok.rq : {qKG}")
    viz_nx_graph(qKG.disp_view(), save_as=path_to_results / f"qKG_{ID_query}_ok")
    viz_nx_graph(
        qKG.fold_class().disp_view(),
        save_as=path_to_results / f"qKG_{ID_query}_ok_folded",
    )


####################################################
###
###     STEP 2b: run query
###

qres = sparql(query, world)

### Restrict the query to a specific subgraph
# qres = sparql(query, world, kg=subkgs["wonka.CHOCOLATE_FACTORY"])
# qres = sparql(query, world, kg=subkgs["wonka.VEHICLE_TESTBED"])

if disp_query_results := True:
    print(tabulate(qres, headers="keys", tablefmt="psql"))


####################################################
###
###     STEP 2c: instantiate qKG with query results
###

qKG_inst = qKG.instantiate(qres, KG)
qKG_inst_without_KG = qKG.instantiate(qres)

if disp_qKG := True:
    print(f"req_{ID_query}_ok.rq: {qKG_inst}")
    viz_nx_graph(
        qKG_inst.disp_view(), save_as=path_to_results / f"qKG_{ID_query}_instantiated"
    )
    viz_nx_graph(
        qKG_inst_without_KG.disp_view(),
        save_as=path_to_results / f"qKG_{ID_query}_withoutKG",
    )

""" ------------------------------------------------ """
""" ------------------   STEP 3   ------------------ """
""" ------------------------------------------------ """

####################################################
###
###     STEP 3a: compute qKGok, qKGnok; instantiate
###

from wonka.representation import QueryGraph

ID_query = 41

query_OK = Query(path_to_queries / f"req_{ID_query}_ok.rq")
query_NOK = Query(path_to_queries / f"req_{ID_query}_nok.rq")

qKGok = QueryGraph(query_OK).fold_class()
qKGnok = QueryGraph(query_NOK).fold_class()

if disp_qKGok_qKGnok := True:
    viz_nx_graph(qKGok.disp_view(), save_as=path_to_results / f"qKG_{ID_query}_ok")
    viz_nx_graph(qKGnok.disp_view(), save_as=path_to_results / f"qKG_{ID_query}_nok")


####################################################
###
###     STEP 3b: compute qKGhelper
###

qres_nok = sparql(query_NOK, world)
qres_nok.to_csv(path_to_results / "query_result.csv", sep="\t", mode="w")

qKGhelper = qKGok.solve(qres_nok, KG, onto)

if disp_qKGhelper := True:
    print(f"Helper graph for req_{ID_query}: {qKGhelper}")
    viz_nx_graph(qKGhelper, save_as=path_to_results / f"qKG_{ID_query}_helper")

####################################################
###
###     STEP 3c: project query results onto KG
###

qKGok = QueryGraph(query_OK).fold_class()
projKG = KG.project_query_graph(qKGok, qres_nok, inplace=False)

if disp_projKG := True:
    print(f"Projection of req_{ID_query} onto KG: {projKG}")
    viz_nx_graph(projKG, save_as=path_to_results / f"qKG_{ID_query}_projected_on_KG")

""" ------------------------------------------------ """
""" ------------------   STEP 4   ------------------ """
""" ------------------------------------------------ """

####################################################
###
###     STEP 4a: compute degrees of validation and scalability
###


from wonka.metrics import ValidationMetric

print("\n\nValidation metrics:")

val = ValidationMetric(world)

static_queries = [
    (
        Query(path_to_queries / f"req_{q}_ok.rq"),
        Query(path_to_queries / f"req_{q}_nok.rq"),
    )
    for q in [11, 31, 32, 41]
]
dynamic_queries = [
    (
        Query(path_to_queries / f"req_{q}_ok.rq"),
        Query(path_to_queries / f"req_{q}_nok.rq"),
    )
    for q in [21]
]
all_queries = static_queries + dynamic_queries


degree_of_validation = {
    s: val.degree_of_validation(all_queries, skg) for s, skg in subkgs.items()
}
df_validation = pd.DataFrame(degree_of_validation)

degree_of_scalability = {
    lab: {
        ind: val.degree_of_scalability(all_queries, (lab_kg, ind_kg))["valid_rows"]
        for ind, ind_kg in ind_systems.items()
    }
    for lab, lab_kg in lab_systems.items()
}
df_scalability = pd.DataFrame(degree_of_scalability)

if disp_vnv_metrics := True:
    print(
        "\nValidation rates (ratio of valid requirements or elements satisfying these requirements):\n"
    )
    print(tabulate(df_validation, headers="keys", tablefmt="psql"))
    print("\nScalability rate (similarity between validation rates):\n")
    print(tabulate(df_scalability, headers="keys", tablefmt="psql"))

####################################################
print("Done.")
