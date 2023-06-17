"""

Knowledge representations

"""
from __future__ import annotations


### Local
from wonka.utils import *
from wonka.query import Query


class KnowledgeGraph(nx.MultiDiGraph):
    def __init__(
        self,
        load: str | Ontology = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **{**{"directed": True}, **kwargs})
        if load is not None:
            self.load(load)

    def load(self, load_from: str | Ontology) -> KnowledgeGraph:
        """Load knowledge either from an OWL file (.owl) or an Ontology (owlready2)

        Parameters
        ----------
        load_from : str | Ontology
            OWL file path (.owl) or ontology (`Ontology`) to load knowledge from

        Returns
        -------
        KnowledgeGraph
            self
        """
        if isinstance(load_from, str) and load_from.endswith(".owl"):
            onto = default_world.get_ontology(load_from).load()
        elif isinstance(load_from, Ontology):
            onto = load_from
        else:
            log.warning(f"Could not import\n{load_from}")
        self._load_from_ontology(onto)
        return self

    def _load_from_ontology(
        self, onto: Ontology, exclude_relationships: Sequence = []
    ) -> KnowledgeGraph:
        for individual in onto.individuals():
            name_indiv = format_iri(individual)
            ### Add individual node
            if not self.has_node(name_indiv):
                self.add_node(
                    name_indiv,
                    **{"nodeType": "instance", "class": str(individual.__class__)},
                )
            for relation in individual.get_properties():
                for neighbour in relation[individual]:
                    name_relation = format_iri(relation)
                    name_neighbour = format_iri(neighbour)
                    if relation in onto.data_properties():
                        ### Data property as an individual's attribute/node data (instead of creating a neighbour node)
                        self.nodes[name_indiv][name_relation] = neighbour
                    else:
                        if name_relation not in exclude_relationships:
                            ### Add neighbour node
                            if not self.has_node(name_neighbour):
                                self.add_node(
                                    name_neighbour,
                                    **{
                                        "nodeType": "instance",
                                        "class": str(neighbour.__class__),
                                    },
                                )
                            ### Add edges between individual and neighbour nodes
                            #   explicitly indicate relationship existence (altered in query graphs)
                            if not (
                                name_indiv,
                                name_neighbour,
                                name_relation,
                            ) in self.edges(keys=True):
                                self.add_edge(
                                    name_indiv,
                                    name_neighbour,
                                    key=name_relation,
                                    **{"exists": True},
                                )

    def divide(
        self, border_cls: Sequence[str], key_cls: Sequence[str] = None
    ) -> dict[str | int, KnowledgeGraph]:
        """Divide knowledge graph in subgraphs,
        cutting off branches where classes in `border_cls` are found

        Parameters
        ----------
        border_cls : Sequence[str]
            classes that make the interfaces between targeted subgraphs
        key_cls : Sequence[str], optional
            classes to use as primary key to identify the subgraphs, by default None

        Returns
        -------
        dict[str | int, KnowledgeGraph]
            dict enumerating the knowledge subgraphs
        """
        graph = copy.deepcopy(self)
        subgraphs, trimmed = {}, set()
        ### remove nodes at the border (interfaces between subgraphs)
        for node in copy.deepcopy(graph.nodes()):
            if graph.nodes[node]["class"] in border_cls:
                graph.remove_node(node)
                trimmed |= {node}

        ### generate subgraphs from connected components (in the undirected sense)
        for k, connected in enumerate(
            nx.connected_components(graph.to_undirected(as_view=True))
        ):
            if key_cls is not None:
                key = [n for n in connected if graph.nodes[n]["class"] in key_cls].pop()
            else:
                key = k
            subgraphs[key] = graph.subgraph(connected)
            subgraphs[key]._trimmed = trimmed
        return subgraphs

    def project_query_graph(
        self,
        uninstantiated_query_graph: QueryGraph,
        query_result: pd.DataFrame = pd.DataFrame(),
        inplace=False,
    ) -> KnowledgeGraph:
        """Project the results of a query onto a knowledge graph

        Parameters
        ----------
        uninstantiated_query_graph : QueryGraph
            Uninstantiated query graph
        query_result : pd.DataFrame, optional
            DataFrame containing the results of a SPARQL query, by default pd.DataFrame()
        inplace : bool, optional
            If False, return a copy, otherwise, do operation inplace and return self. by default False

        Returns
        -------
        KnowledgeGraph
            query elements projected onto the knowledge graph
        """

        if len(query_result) == 0:
            log.info("No query result...")
            return self

        projKG = self if inplace else copy.deepcopy(self)

        for _, res in query_result.iterrows():

            instance = {var: str(indiv) for var, indiv in zip(res.index, res.values)}

            for _s, _o, _k in uninstantiated_query_graph.edges(keys=True):
                s, o, p = (
                    str(instance[_s]),
                    str(instance[_o]),
                    format_predicate(_k),
                )

                if (s, o, p) in projKG.edges(keys=True):
                    projKG[s][o][p]["color"] = RED
                    projKG[s][o][p]["width"] = 5
        return projKG


class QueryGraph(nx.MultiDiGraph):
    def __init__(
        self,
        load_from: str = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **{**{"directed": True}, **kwargs})
        self._instantiated = False
        if load_from is not None:
            self.load(load_from)

    def load(self, load_from: str | Path) -> QueryGraph:
        if isinstance(load_from, str | Path) and str(load_from).endswith(".rq"):
            # query = "".join(open(str(load_from)))
            query = Query(load_from)
        elif isinstance(load_from, Query):
            query = load_from
        else:
            log.warning(f"Could not import\n{load_from}")
        self._load_from_query(query)
        return self

    def _load_from_query(
        self,
        query: Query | str = None,
        _Token: Any = None,
        _meta: dict = {},
    ) -> QueryGraph:
        """Rudimentary parser to convert a SPARQL query into a QueryGraph
        base on rdflib's `parseQuery`

        Parameters
        ----------
        query : str, optional
            SPARQL query, by default None

        Returns
        -------
        QueryGraph
            up-to-date query graph.
        """

        if _Token is None:
            ### Initialise
            pq = parseQuery(str(query))
            _Token = pq
            _meta["mustExist"] = True

        if isinstance(_Token, (ParseResults, list)):
            ### Update from triples
            for tok in _Token:
                if getattr(tok, "name", None) == "TriplesBlock":
                    self._update_from_triples(
                        graph=self,
                        triplesblock=tok,
                        edge_data={"mustExist": _meta["mustExist"]},
                    )
                self._load_from_query(_Token=tok, _meta=_meta)

        elif isinstance(_Token, CompValue):
            ### Other kinds of tokens
            if _Token.name == "Builtin_NOTEXISTS":
                _meta["mustExist"] = not _meta["mustExist"]
            for _, tok in _Token.items():
                self._load_from_query(_Token=tok, _meta=_meta)
        return self

    def _update_from_triples(
        self, graph, triplesblock, edge_data: dict = {}, node_data: dict = {}
    ):
        def _get_node_attr(name: str, node_data: dict = {}):
            node_attr = node_data
            if name.startswith("?"):
                node_attr["nodeType"] = "variable"
            else:
                node_attr["nodeType"] = "class"
            return node_attr

        def _get_edge_attr(sname: str, oname: str, edge_data: dict = {}):
            if edge_data.get("mustExist") is None:
                log.error("mustExist property was not set.")
            edge_attr = edge_data
            if not (sname.startswith("?") and oname.startswith("?")):
                edge_attr["nodeType"] = "var2class"
            else:
                edge_attr["nodeType"] = "var2var"
            return edge_attr

        for ts, to, tp in triplesblock["triples"]:
            sname, pname, oname = (token2name(ts), token2name(to), token2name(tp))
            graph.add_node(sname, **_get_node_attr(sname, node_data))
            graph.add_node(oname, **_get_node_attr(oname, node_data))
            graph.add_edge(
                sname, oname, key=pname, **_get_edge_attr(sname, oname, edge_data)
            )
        return graph

    def fold_class(self, inplace=False) -> QueryGraph:
        """Fold class nodes
        if a subject's type (`subject rdf:type class`) is declared in the query,
        add the type/class to the node's attributes and remove this node.

        Parameters
        ----------
        inplace : bool, optional
            If False, return a copy, otherwise, do operation inplace and return self. by default False

        Returns
        -------
        QueryGraph
            Query graph without class nodes
        """
        graph = self if inplace else copy.deepcopy(self)
        nodes2del, edges2del = [], []
        for s, o, k, data in graph.edges(keys=True, data=True):
            if k in (
                "rdf:type",
                "a",
                "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>",
            ):
                graph.nodes[s]["class"] = o
                nodes2del.append((o, graph.nodes[o]))
                edges2del.append((s, o, k, data))
        for s, o, k, data in edges2del:
            graph.remove_edge(s, o, k)
        for o, data in nodes2del:
            if graph.has_node(o):
                graph.remove_node(str(o))
        graph.deleted_nodes = nodes2del
        graph.deleted_edges = edges2del
        return graph

    def unfold_class(self, inplace=False) -> QueryGraph:
        graph = self if inplace else copy.deepcopy(self)
        graph.add_nodes_from(self.deleted_nodes)
        graph.add_edges_from(self.deleted_edges)
        return graph

    def disp_view(self):
        graph = copy.deepcopy(self)
        for node, node_attr in graph.nodes(data=True):
            node_attr |= fetch_gformat("node", node_attr["nodeType"])
            # node_attr |= fetch_gformat("node", node_attr.get("status"))
        for s, o, k, edge_attr in graph.edges(keys=True, data=True):
            stype, otype = graph.nodes[s]["nodeType"], graph.nodes[o]["nodeType"]
            if stype == "variable" and otype == "variable":
                edge_attr |= fetch_gformat("edge", "var2var")
            else:
                edge_attr |= fetch_gformat("edge", "var2class")
            if edge_attr.get("mustExist"):
                edge_attr |= fetch_gformat("edge", "must_exist")
            else:
                edge_attr |= fetch_gformat("edge", "must_not_exist")
            # edge_attr |= fetch_gformat("edge", edge_attr.get("status"))
        return graph

    def instantiate(
        self, query_results: pd.DataFrame, KG: KnowledgeGraph = None, inplace=False
    ) -> QueryGraph:
        """instantiate query graph with individuals from query result.
        if KG is provided, node and edge data will be imported from KG to the query graph"""

        def swap_keys(nx_graph: nx.MultiDiGraph, mapping: dict):
            """swap keys {(node1, node2, old_key):new_key}"""
            remove, add = [], []
            for s, o, k, data in nx_graph.edges(keys=True, data=True):
                remove.append((s, o, k))
                add.append((s, o, mapping[(s, o, k)], data))
            for s, o, k in remove:
                nx_graph.remove_edge(s, o, k)
            for s, o, k, data in add:
                nx_graph.add_edge(s, o, key=k, **data)
            return nx_graph

        if query_results.empty:
            log.warning("No query result to instantiate the graph (empty DataFrame)")
            return self

        ### Swap variables with individuals in qKG
        qKG_out = self if inplace else copy.deepcopy(self)
        mapping = {}
        for var_node, data in qKG_out.nodes(data=True):
            data["use"] = True
            if data["nodeType"] == "variable":
                inst_node = str(query_results[var_node].iloc[0])
                mapping[var_node] = inst_node
                if KG is None:
                    data["nodeType"] = "instance"
                else:
                    if KG.has_node(inst_node):
                        data |= KG.nodes[inst_node]
                        mapping[var_node] = inst_node
                        data["nodeType"] = "instance"
                        data["status"] = "ok"
                    else:
                        data["status"] = "new"
        nx.relabel_nodes(qKG_out, mapping, copy=False)
        ### Swap query predicates with properties
        swap_keys(
            qKG_out,
            mapping={
                (s, o, k): format_predicate(k) for s, o, k in qKG_out.edges(keys=True)
            },
        )
        for s, o, k, data in qKG_out.edges(keys=True, data=True):
            data["use"] = True
            if KG is None:
                pass
            else:
                if not (s, o, k) in KG.edges(keys=True):
                    data["exists"] = False
                else:
                    data |= KG[s][o][k]
        qKG_out._instantiated = True
        return qKG_out

    def _update_status_nodes(self):
        ### Update node status (ok, new)
        for _, data in self.nodes(data=True):
            if data["nodeType"] == "variable":
                data["status"] = "new"
            elif data["nodeType"] == "instance" and not data.get("status") == "ok":
                data["status"] = "existing"

    def _update_status_edges(self):
        ### Update action (add, del)
        for ns, no, k, data in self.edges(keys=True, data=True):
            s, o = self.nodes[ns], self.nodes[no]
            exists, mustExist = (
                self[ns][no][k].get("exists"),
                self[ns][no][k]["mustExist"],
            )
            # ok with ok
            if s["status"] == "ok" and o["status"] == "ok":
                if exists and mustExist:
                    data["status"] = "ok"
                elif exists and not mustExist:
                    data["status"] = "del"
                elif not exists and mustExist:
                    data["status"] = "add2ok"
                elif not exists and not mustExist:
                    data["status"] = "warn"
            # ok && new OR new && new
            elif (
                (s["status"] == "ok" and o["status"] == "new")
                or (s["status"] == "new" and o["status"] == "ok")
                or (s["status"] == "new" and o["status"] == "new")
            ):
                if mustExist:
                    data["status"] = "add2new"
                else:
                    data["status"] = "warn"
            # ok && existing OR existing && existing
            elif (
                (s["status"] == "ok" and o["status"] == "existing")
                or (s["status"] == "existing" and o["status"] == "ok")
                or (s["status"] == "existing" and o["status"] == "existing")
            ):
                if exists and mustExist:
                    data["status"] = "ok_existing"
                elif exists and not mustExist:
                    data["status"] = "del_existing"
                elif not exists and mustExist:
                    data["status"] = "add2existing"
                elif not exists and not mustExist:
                    data["status"] = "warn"
            # new && existing
            elif (s["status"] == "new" and o["status"] == "existing") or (
                s["status"] == "existing" and o["status"] == "new"
            ):
                if mustExist:
                    data["status"] = "add2new_existing"
                else:
                    data["status"] = "warn"

    def _update_status(self):
        """update node and edge statuses according to (nodeType) and (node['status'], exists, mustExist) respectively"""
        self._update_status_nodes()
        self._update_status_edges()

    # def _onto_getattr(self, obj, attr):
    #     res = getattr(self.onto[obj.replace(f"{self.base_iri}.", "")], attr)
    #     if isinstance(res, (list, tuple)):
    #         return list(map(str, res))
    #     return str(res)

    def solve(
        self,
        query_results: pd.DataFrame,
        KG: nx.MultiDiGraph,
        ontology: Ontology,
        inplace=False,
    ):
        """A visual helper for pinpointing the individuals and object properties preventing the validation of a requirement"""
        # TODO handle order_new=0 ----> remove variables

        order_new = 1  # TODO var orders
        order_existing = 0  # TODO var orders

        graph = self if inplace else copy.deepcopy(self)

        graph.instantiate(query_results, KG, inplace=True)
        graph._update_status()

        # cp_qKGhelper = copy.deepcopy(qKGhelper)
        # # for each problematic object property (requiring add)
        # for s_init, o_init, predicate_add, data_predicate_add in cp_qKGhelper.edges(keys=True, data=True):
        #     if data_predicate_add.get('status','')[:3] == 'add':
        #         p_domain, p_range = [   (list(map(str, obj_prop.domain)), list(map(str, obj_prop.range)))
        #                                 for obj_prop in ontology.object_properties() if str(obj_prop)==predicate_add].pop()
        #         p_domain += self._onto_getattr(s_init, '__class__')
        #         for new_type in p_domain:
        #             # for s_existing in cp_qKGhelper.nodes():
        #             #     if new_type in self._onto_getattr(s_existing, 'range'):
        #             qKGhelper.add_node((new := f'add > {new_type}'), nodeType='variable', **{'class':new_type})
        #             qKGhelper.add_edge(new, o_init, key=predicate_add, **data_predicate_add)

        ### Add neighbours up to order order_existing
        # i_new = i_existing = -1
        i_existing = -1
        while (i_existing := i_existing + 1) < order_existing:
            # for each node/individual in qKGhelper; for each neighbour (in the undirected sense); add neighbour and properties to qKGhelper
            for n_indiv, data in copy.deepcopy(graph.nodes(data=True)):
                if KG.has_node(n_indiv):
                    for n_neighbour, relations_neighbour in KG.to_undirected(
                        as_view=True
                    )[n_indiv].items():
                        if not graph.has_node(n_neighbour):
                            graph.add_node(
                                n_neighbour,
                                **{**{"use": False}, **KG.nodes[n_neighbour]},
                            )
                        for k, data in relations_neighbour.items():
                            if not graph.has_edge(
                                n_indiv, n_neighbour, key=k
                            ) and not graph.has_edge(n_neighbour, n_indiv, key=k):
                                if KG.has_edge(n_indiv, n_neighbour, key=k):
                                    graph.add_edge(
                                        n_indiv,
                                        n_neighbour,
                                        key=k,
                                        **{"use": False},
                                    )
                                else:
                                    graph.add_edge(
                                        n_neighbour,
                                        n_indiv,
                                        key=k,
                                        **{"use": False},
                                    )

        graph._update_status_nodes()

        copy_qKGhelper = copy.deepcopy(graph)
        copy_qKGhelper_edges = copy.deepcopy(graph.edges(keys=True, data=True))
        copy_qKGhelper_nodes = copy.deepcopy(graph.nodes(data=True))

        ### connect
        # for each problematic object property (requiring add)
        for s_init, o_init, predicate_add, data_predicate_add in copy_qKGhelper_edges:
            if data_predicate_add.get("status", "").startswith("add"):
                p_domain, p_range = [
                    (list(map(str, obj_prop.domain)), list(map(str, obj_prop.range)))
                    for obj_prop in ontology.object_properties()
                    if str(obj_prop) == format_predicate(predicate_add)
                ].pop()

                # for each candidate node as last proxy before bridge
                for s_last, data_last in copy_qKGhelper_nodes:
                    if data_last["status"] == "existing" and (
                        (data_last["class"] in p_domain) or (not p_domain)
                    ):
                        for path in nx.all_simple_edge_paths(
                            copy_qKGhelper.to_undirected(as_view=True),
                            source=s_init,
                            target=s_last,
                        ):
                            if not graph.has_edge(s_last, o_init, predicate_add):
                                for ss, oo, kk in path:
                                    if kk in graph[ss][oo].keys():
                                        graph[ss][oo][kk]["use"] = True
                                        graph[ss][oo][kk][
                                            "mustExist"
                                        ] = data_predicate_add["mustExist"]
                                    else:
                                        graph[oo][ss][kk]["use"] = True
                                        graph[oo][ss][kk][
                                            "mustExist"
                                        ] = data_predicate_add["mustExist"]
                                    graph.nodes[ss]["use"] = True
                                    graph.nodes[oo]["use"] = True
        ### clean (delete unused)
        for s, o, k, data in copy.deepcopy(graph.edges(keys=True, data=True)):
            if not data["use"]:
                graph.remove_edge(s, o, k)
        for n, data in copy.deepcopy(graph.nodes(data=True)):
            if not data["use"]:
                graph.remove_node(n)
        ### update status & style
        graph._update_status()
        graph._apply_style()
        return graph

    def _apply_style(self):
        for n, data in self.nodes(data=True):
            data |= fetch_gformat("node", data["nodeType"])
            data |= fetch_gformat("node", data["status"])
        for s, o, k, data in self.edges(keys=True, data=True):
            data |= fetch_gformat("edge", data["status"])
        return self
