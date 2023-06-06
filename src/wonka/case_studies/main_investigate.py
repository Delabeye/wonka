"""

Development of the WONKA pipeline

[pre-requisite]
    a. design and instantiate ontology, save post-reasoning (.owl)
    b. design sparql queries, save (.rq)

[STEP 1] --- OWL to Knowledge Graph ---
    a. compute knowledge graph
    b. divide knowledge graph into  knowledge subgraphs (systems/use cases)
    c. evaluate semantic similarity between knowledge subgraphs (systems/use cases)

[STEP 2] --- SPARQL to Query Graph ---
    a. compute query graph
    b. run query
    c. instantiate query graph

[STEP 3] --- Helper Graph ---
    a. run ok/nok queries; compute & instantiate query graphs
    b. solve helper (missing & erroneous nodes or links)
    c. project query results (qres_nok) onto the knowledge graph (KG)

[STEP 4] --- Validation and Scalability metrics ---
    a. run degrees of validation and scalability


NOTE
- OWL file name must match the ontology's name (e.g. http://localhost/wonka iri -> wonka.owl)
- same goes for sparql queries' shorthand notations (e.g., `wonka:http://localhost/wonka` must be used for concepts/properties related to `wonka`)

"""


### Local
from wonka.utils import *
from wonka.visualisation import viz_nx_graph
from wonka.query import Query, sparql

path_to_owl = Path(__file__).parent.parent / "data/SAM2022/ontology/labsys_selection/wonka.owl"
path_to_queries = Path(__file__).parent.parent / "data/SAM2022/query/requirements_BSSapproach"

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
    print(str(KG))
    viz_nx_graph(KG, save_as="KG")


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
        print(skg_id, str(SKG))
        viz_nx_graph(SKG, save_as=skg_id)

exit()

####################################################
###
###     STEP 1c: semantic similarity
###

from wonka.metrics import HeterogeneousLinSimilarity


sim = HeterogeneousLinSimilarity(onto)

if study_wonka_intrinsic_similarity := False:
    lab_systems_labels = [
        "wonka.LABORATORY_CoffeeMachine",
        "wonka.LABORATORY_3Dprinter",
        "wonka.LABORATORY_6axisRobot",
    ]
    lab_systems = [subkgs[s] for s in lab_systems_labels]

    ind_systems_labels = ["wonka.CHOCOLATE_FACTORY", "wonka.VEHICLE_TESTBED"]
    ind_systems = [subkgs[s] for s in ind_systems_labels]

    # ### indsys vs labsys
    # indlabsys_matrix = np.matrix(
    #     [[sim.sim_subkgs([sys1, sys2]) for sys2 in lab_systems] for sys1 in ind_systems]
    # )
    # df_indlabsys = pd.DataFrame(
    #     indlabsys_matrix, columns=lab_systems_labels, index=pd.Index(ind_systems_labels)
    # )
    # ic(df_indlabsys)

    # ### labsys vs labsys
    # labsys_matrix = np.matrix(
    #     [[sim.sim_subkgs([sys1, sys2]) for sys2 in lab_systems] for sys1 in lab_systems]
    # )
    # df_labsys = pd.DataFrame(
    #     labsys_matrix, columns=lab_systems_labels, index=pd.Index(lab_systems_labels)
    # )

    ### indsys vs indsys
    indsys_matrix = np.matrix(
        [[sim.sim_subkgs([sys1, sys2]) for sys2 in ind_systems] for sys1 in ind_systems]
    )
    df_indsys = pd.DataFrame(
        indsys_matrix, columns=ind_systems_labels, index=pd.Index(ind_systems_labels)
    )
    ic(df_indsys)

    # ### --- save ---
    # df_labsys.to_csv("labsys_vs_labsys.csv", sep="\t", mode="w")
    # df_indsys.to_csv("indsys_vs_indsys.csv", sep="\t", mode="w")
    # df_indlabsys.to_csv("indsys_vs_labsys.csv", sep="\t", mode="w")


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

if disp_qKG := False:
    print(qKG)
    viz_nx_graph(qKG.disp_view())
    viz_nx_graph(qKG.fold_class().disp_view())
    # viz_nx_graph(qKG)
    # viz_nx_graph(qKG.fold_class(True).unfold_class(True).disp_view())
    # viz_nx_graph(qKG.fold_class().unfold_class().disp_view())
    # viz_nx_graph(qKG.fold_class(True).disp_view())


####################################################
###
###     STEP 2b: run query
###

qres = sparql(query, world)

# # restrict the query to a specific subgraph
# qres = sparql(query, world, kg=subkgs["wonka.CHOCOLATE_FACTORY"])
# qres = sparql(query, world, kg=subkgs["wonka.VEHICLE_TESTBED"])

if disp_query_results := True:
    ic(qres)


####################################################
###
###     STEP 2c: instantiate qKG with query results
###

qKG_inst = qKG.instantiate(qres, KG)
qKG_inst_without_KG = qKG.instantiate(qres)

if disp_qKG := False:
    print(qKG_inst)
    viz_nx_graph(qKG_inst.disp_view())
    viz_nx_graph(qKG_inst_without_KG.disp_view())

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

if disp_qKGok_qKGnok := False:
    viz_nx_graph(qKGok.disp_view())
    viz_nx_graph(qKGnok.disp_view())


####################################################
###
###     STEP 3b: compute qKGhelper
###

qres_nok = sparql(query_NOK, world)
qres_nok.to_csv("query_result.csv", sep="\t", mode="w")

qKGhelper = qKGok.solve(qres_nok, KG, onto)

if disp_qKGhelper := False:
    print(qKGhelper)
    viz_nx_graph(qKGhelper)

####################################################
###
###     STEP 3c: project query results onto KG
###

qKGok = QueryGraph(query_OK).fold_class()
projKG = KG.project_query_graph(qKGok, qres_nok, inplace=False)

if disp_projKG := False:
    print(projKG)
    viz_nx_graph(projKG)
    # viz_nx_graph(KG)

""" ------------------------------------------------ """
""" ------------------   STEP 4   ------------------ """
""" ------------------------------------------------ """

####################################################
###
###     STEP 4a: compute degrees of validation and scalability
###


from wonka.metrics import ValidationMetric

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
    ic(df_validation)
    ic(df_scalability)

####################################################
print("Done.")
