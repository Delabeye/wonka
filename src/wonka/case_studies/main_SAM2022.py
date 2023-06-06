"""
NOTE
- query "SELECT * ..." will not work if type not declared (and not within a NOT EXISTS graph)

TODO
- represent data properties (str(data) for a node's name leads to overwritings)
- restructure a tat' analyzer -> KG & onto aspects should be distinct from querying mechanism
    - owl2graph ; query_analyser ; querying_mechanism
    -   add LCS & cie into owl2graph
- define LCS(c1, c2, KG) -> KG=[kg1, kg2] or [kg]
- define sim_lin


"""

### Local
from wonka.utils import *
from wonka.visualisation import viz_nx_graph
from wonka.query import query_to_df, vars_from_query

### ______________________________________
###
###                 Interface
### ______________________________________

base_iri = "wonka"

path_to_owl = Path(__file__).parent / "data/SAM2022/ontology/labsys_selection"
path_to_queries = Path(__file__).parent / "data/SAM2022/query/requirements_BSSapproach"

filename_owl = "wonka.owl"  # "onto_ATV_CoffeeMachine_HVAC_ChocolateFactory-postExp_INF.owl" # "onto_ATV_CoffeeMachine_HVAC_ChocolateFactory_INF.owl"


ID_query = 41
query_OK = "".join(open(path_to_queries / f"req_{ID_query}_ok.rq")).replace(
    "onto:", f"{base_iri}:"
)
query_NOK = "".join(open(path_to_queries / f"req_{ID_query}_nok.rq")).replace(
    "onto:", f"{base_iri}:"
)

use_query = query_NOK


### ______________________________________
###
###                 RUN
### ______________________________________

####################################################
### STEP 1: compute KG

from wonka.representation import KnowledgeRepresentation

knowledge = KnowledgeRepresentation()
knowledge.import_ontology(filename=filename_owl, dir=path_to_owl, base_iri=base_iri)
knowledge.kg

if disp := True:
    print(str(knowledge.kg))
    viz_nx_graph(knowledge.kg, buttons=True, toggle_physics=True)

exit()


####################################################
### STEP 2:
subkgs = knowledge.divide_kg(
    key_cls=["wonka.Laboratory", "saref4inma.Factory"],
    border_cls=[
        "wonka.Approach_to_Validate",
        "wonka.Accuracy",
        "wonka.Requirement",
    ],
)
### TESTS
# viz_nx_graph(subkgs, buttons=True, toggle_physics=True)

# ic(knowledge.LCS("core.LightSwitch", "core.Sensor"))
# ic(knowledge.LCS("core.Sensor", "core.LightSwitch"))

# ic(knowledge.IC("core.Sensor", subkg_id="wonka.LABORATORY"))
# ic(knowledge.IC("core.Sensor", subkg_id="wonka.ChocolateFactory"))
# ic(knowledge.IC("core.Sensor", subkg_id="wonka.VEHICLE_TESTBED"))

# ic(
#     knowledge.sim_lin(
#         ["core.Sensor", "core.FeatureOfInterest"],
#         ["wonka.LABORATORY", "wonka.VEHICLE_TESTBED"],
#     )
# )

# ic(knowledge.maxSim("wonka.Current", "wonka.LABORATORY", "wonka.VEHICLE_TESTBED"))

# ic(knowledge.sim_subkgs(["wonka.LABORATORY_CoffeeMachine", "wonka.VEHICLE_TESTBED"]))
# ic(knowledge.sim_subkgs(["wonka.LABORATORY_CoffeeMachine", "wonka.CHOCOLATE_FACTORY"]))
# ic(knowledge.sim_subkgs(["wonka.VEHICLE_TESTBED", "wonka.CHOCOLATE_FACTORY"]))

if False:
    labsys = [
        "wonka.LABORATORY_CoffeeMachine",
        "wonka.LABORATORY_3Dprinter",
        "wonka.LABORATORY_6axisRobot",
    ]
    indsys = ["wonka.VEHICLE_TESTBED", "wonka.CHOCOLATE_FACTORY"]
    for lsys in labsys:
        for isys in indsys:
            score = knowledge.sim_subkgs([lsys, isys])
            n_instances_lab = len(knowledge.subkg[lsys])
            n_instances_ind = len(knowledge.subkg[isys])
            print(
                f"\n{lsys} : {score*100:.1f}% similar : {isys}\nratio = 1:{n_instances_ind/n_instances_lab} (lab {n_instances_lab} vs ind {n_instances_ind} instances)\n"
            )

# exit()


####################################################
### STEP 1: compute KG

from analyser import SPARQL_Requirement_Analyser

if True:
    ra = SPARQL_Requirement_Analyser()

    ra.import_ontology(filename=filename_owl, dir=path_to_owl, base_iri=base_iri)

    KG = ra.compute_KG()

    if disp := True:
        ic(str(KG))
        kg_disp = copy.deepcopy(KG)
        viz_nx_graph(KG, buttons=True, toggle_physics=True)


####################################################
### STEP 2: compute qKG

from analyser import QueryAnalyser

if True:
    qa = QueryAnalyser(query=use_query, base_iri=base_iri, world=default_world)

    qKG = qa.compute_qKG()

    if disp := True:
        viz_nx_graph(
            qa.compute_qKG(fold_class=False), buttons=True, toggle_physics=True
        )
        viz_nx_graph(qKG, buttons=True, toggle_physics=True)

    qa_ok = QueryAnalyser(query=query_OK, base_iri=base_iri, world=default_world)
    qa_nok = QueryAnalyser(query=query_NOK, base_iri=base_iri, world=default_world)
    qKGok = qa_ok.compute_qKG()
    qKGnok = qa_nok.compute_qKG()

####################################################
### STEP 3: query qKG
if True:

    df_query_result = qa.sparql()

    df_query_result.to_csv(r"query_result.csv", sep="\t", mode="w")

    if disp := True:
        ic(df_query_result)
        ic(vars_from_query(use_query))

    all_qres_ok = qa_ok.sparql()
    all_qres_nok = qa_nok.sparql()
    qres_ok = all_qres_ok.iloc[[0]]
    qres_nok = all_qres_nok.iloc[[0]]


####################################################
### STEP 4: instantiate qKGok with qres_nok
if True:

    qKGhelper = ra.solve_within_qKG(
        qKG=qKGok, qres=qres_nok, KG=KG, order_new=1, order_existing=0
    )
    # qKGhelper = ra.solve_within_qKG(qKG=qKGnok, qres=qres_ok, KG=KG, order_new=1, order_existing= 0 )

    if disp := True:
        viz_nx_graph(qKGhelper, buttons=True, toggle_physics=True)


# ####################################################
# ### OLD (former step 4) - STEP 5: inject qKG and query results into KG
# if options['step 5: proj']['run']:
#     KGhelper = ra.project_qKG_on_KG(KG=KG, qKG=qKG, query_result=df_query_result, color=RED)

#     if options['step 4: proj']['disp']:
#         viz_nx_graph(KGhelper, buttons=True, toggle_physics=True)


####################################################
### Evaluate scalability


def process_query(query):
    qa = QueryAnalyser(query=query, base_iri=base_iri, world=default_world)
    qKG = qa.compute_qKG()
    df_query_result = qa.sparql(query)
    return qKG, df_query_result


def compute_scalability_metrics(
    all_queries_oknok: list[tuple[str, str]], labsys, indsys
):
    n_req, n_inst = len(all_queries_oknok), 0
    labsys_val, indsys_val = [
        {s: {"req": 0, "inst": 0, "inst_total": 0} for s in syst}
        for syst in [labsys, indsys]
    ]
    for query_OK, query_NOK in all_queries_oknok:
        _, df_qok = process_query(query_OK)
        _, df_qnok = process_query(query_NOK)

        df_qok["?platform"] = df_qok["?platform"].astype(str)
        df_qnok["?platform"] = df_qnok["?platform"].astype(str)

        n_inst += len(df_qok) + len(df_qnok)

        for sys_val in [labsys_val, indsys_val]:
            for s in sys_val:
                # total number of instances concerned by the requirement
                sys_val[s]["inst_total"] += len(
                    df_qok.loc[df_qok["?platform"] == s]
                ) + len(df_qnok.loc[df_qnok["?platform"] == s])
                # number of instances that validate the requirement
                sys_val[s]["inst"] += len(df_qok.loc[df_qok["?platform"] == s])
                # whether requirement is validated
                sys_val[s]["req"] += len(df_qnok.loc[df_qnok["?platform"] == s]) == 0

    # wrapping up
    n_req_labsys_val, n_inst_labsys_val = sum(
        [syst["req"] for syst in labsys_val.values()]
    ), sum([syst["inst"] for syst in labsys_val.values()])
    degree_of_validation = {
        s: {
            "req": sys_val[s]["req"] / n_req,
            "inst": sys_val[s]["inst"] / sys_val[s]["inst_total"],
        }
        for sys_val in [labsys_val, indsys_val]
        for s in sys_val
    }

    degree_of_scalability = {
        s: {
            "req": 1 - (n_req_labsys_val - sys_val[s]["req"]) / n_req,
            # 'inst': 1 - sys_val[s]['inst']/sys_val[s]['inst_total']
        }
        for sys_val in [indsys_val]
        for s in sys_val
    }
    metrics_per_sys = {
        "degree_of_validation": degree_of_validation,
        "degree_of_scalability": degree_of_scalability,
    }
    # metrics_per_sys['degree_of_validation']['system_name']['req']
    return metrics_per_sys


if run_scalability := True:
    LabSys, IndSys = [f"{base_iri}.LABORATORY"], [
        f"{base_iri}.VEHICLE_TESTBED",
        f"{base_iri}.ChocolateFactory",
    ]
    static_qid, dynamic_qid = [11, 31, 32, 41], [21]

    all_static_queries = [
        (
            "".join(open(os.path.join(path_to_queries, f"req_{ID_query}_ok.rq"))),
            "".join(open(os.path.join(path_to_queries, f"req_{ID_query}_nok.rq"))),
        )
        for ID_query in static_qid
    ]
    all_dynamic_queries = [
        (
            "".join(open(os.path.join(path_to_queries, f"req_{ID_query}_ok.rq"))),
            "".join(open(os.path.join(path_to_queries, f"req_{ID_query}_nok.rq"))),
        )
        for ID_query in dynamic_qid
    ]

    static_validation = compute_scalability_metrics(
        all_static_queries, labsys=LabSys, indsys=IndSys
    )
    dynamic_validation = compute_scalability_metrics(
        all_dynamic_queries, labsys=LabSys, indsys=IndSys
    )
    overall_validation = compute_scalability_metrics(
        all_static_queries + all_dynamic_queries, labsys=LabSys, indsys=IndSys
    )

    ic(static_validation, dynamic_validation, overall_validation)


####################################################
### Wrap up

if True:

    qKG, df_query_result = process_query(query_NOK)
    KGhelper = ra.project_qKG_on_KG(
        KG=KG, qKG=qKG, query_result=df_query_result, color=RED
    )

    qKG, df_query_result = process_query(query_OK)
    KGhelper = ra.project_qKG_on_KG(
        KG=KGhelper, qKG=qKG, query_result=df_query_result, color=GREEN
    )

    if disp := True:
        viz_nx_graph(KGhelper, buttons=True, toggle_physics=True)
