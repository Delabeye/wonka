### Local
from wonka.utils import *
from wonka.visualisation import viz_nx_graph
from wonka.query import load_query, sparql

iri_format_options = {"base_iri": "onto", "refactor": False}

path_to_owl = Path(__file__).parent / "data/dummy/onto.owl"

world = default_world  # pb with Thing (used in SemanticSimilarity) if not default_world
onto = world.get_ontology(str(path_to_owl)).load()

""" ------------------------------------------------ """
""" ------------------   STEP 1   ------------------ """
""" ------------------------------------------------ """

####################################################
###
###     STEP 1a: compute KG
###

from wonka.representation import KnowledgeGraph

KG = KnowledgeGraph(onto, iri_format_options)

if disp_KG := True:
    print(str(KG))
    viz_nx_graph(KG)


####################################################
###
###     STEP 1c: semantic similarity
###

from wonka.metrics import SemanticSimilarity


sim = SemanticSimilarity(onto, KG, subkgs)

ic(sim.LCS("core.LightSwitch", "core.Sensor"))
ic(sim.LCS("core.Sensor", "core.LightSwitch"))

ic(sim.IC("core.Sensor", subkg_id="wonka.LABORATORY_CoffeeMachine"))
ic(sim.IC("core.Sensor", subkg_id="wonka.CHOCOLATE_FACTORY"))
ic(sim.IC("core.Sensor", subkg_id="wonka.VEHICLE_TESTBED"))

ic(
    sim.sim_lin(
        ["core.Sensor", "core.FeatureOfInterest"],
        ["wonka.LABORATORY_CoffeeMachine", "wonka.VEHICLE_TESTBED"],
    )
)

ic(
    sim.sim_lin(
        ["core.Sensor", "core.Sensor"],
        ["wonka.LABORATORY_CoffeeMachine", "wonka.VEHICLE_TESTBED"],
    )
)

ic(sim.sim_subkgs(["wonka.LABORATORY_CoffeeMachine", "wonka.VEHICLE_TESTBED"]))

""" ------------------------------------------------ """
""" ------------------   STEP 2   ------------------ """
""" ------------------------------------------------ """


####################################################
###
###     STEP 2a: compute qKG
###

from wonka.representation import QueryGraph

ID_query = 41
query = load_query(path_to_queries / f"req_{ID_query}_ok.rq", iri_format_options)

qKG = QueryGraph(query, iri_format_options)

if disp_qKG := False:
    print(qKG)
    viz_nx_graph(qKG)
    viz_nx_graph(qKG.disp_view())
    viz_nx_graph(qKG.fold_class().unfold_class().disp_view())
    viz_nx_graph(qKG.fold_class().disp_view())


####################################################
###
###     STEP 2b: run query
###


qres = sparql(query, world, iri_format_options)

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

query_OK = load_query(path_to_queries / f"req_{ID_query}_ok.rq", iri_format_options)
query_NOK = load_query(path_to_queries / f"req_{ID_query}_nok.rq", iri_format_options)

qKGok = QueryGraph(query_OK, iri_format_options).fold_class()
qKGnok = QueryGraph(query_NOK, iri_format_options).fold_class()

####################################################
###
###     STEP 3b: compute qKGhelper
###

qres_nok = sparql(query_NOK, world, iri_format_options)
qres_nok.to_csv("query_result.csv", sep="\t", mode="w")

qKGok.solve(qres_nok, KG, onto, order_new=1, order_existing=0)

if disp_qKGhelper := False:
    print(qKGok)
    viz_nx_graph(qKGok.disp_helper_view())
