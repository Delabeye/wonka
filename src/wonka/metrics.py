### Local
from wonka.utils import *
from wonka.representation import KnowledgeGraph
from wonka.query import Query, sparql

###
###     Semantic Similarity (intrinsic)
###


@dataclass
class SemanticSimilarity:
    onto: Ontology

    def _fetch_conceptlist_from_onto(
        self, concept: str, concept_method: str, as_str=True
    ):
        """TODO result is assumed to be in the right order (owlready2 returns a set -> check ancestor order is always kept)"""
        for cls in self._onto_classes():
            if str(cls) == concept:
                conceptlist = list(getattr(cls, concept_method)())
                if as_str:
                    conceptlist = [str(c) for c in conceptlist]
                return conceptlist
        return ValueError

    def _sort_classes(self, conceptlist: Sequence[Any], as_str=True):
        """NOTE conceptlist must be a sequence of concepts (owlready2-generated class, not str)"""
        conceptlist = sorted(conceptlist, key=lambda c: len(c.ancestors()))
        if as_str:
            conceptlist = [str(c) for c in conceptlist]
        return conceptlist

    def _descendants_of(self, concept, as_str=True):
        """List all descendants (subclasses) of a class (result includes the concept itself)
        NOTE subclasses of owl:Thing must be made explicitly so"""
        ### list descendants
        desc = self._fetch_conceptlist_from_onto(
            concept=concept, concept_method="descendants", as_str=False
        )
        subcls = self._fetch_conceptlist_from_onto(
            concept=concept, concept_method="subclasses", as_str=False
        )
        subclasses = list(set(desc + subcls))
        ### sort descendants
        return self._sort_classes(subclasses, as_str=as_str)

    def _ancestors_of(self, concept, as_str=True):
        """List all ancestors of a class (result includes the concept itself)"""
        ### list ancestors
        ancestors = self._fetch_conceptlist_from_onto(
            concept=concept, concept_method="ancestors", as_str=False
        )
        ### sort ancestors
        return self._sort_classes(ancestors, as_str=as_str)

    def _onto_classes(self):
        return [Thing] + list(self.onto.classes())
        # return [self.onto["owl.Thing"]] + list(self.onto.classes())

    def _all_classes_in(self, kg: KnowledgeGraph, as_str=True):
        cls = np.unique([data["class"] for _, data in kg.nodes(data=True)]).tolist()
        if as_str:
            return cls
        else:
            return [c for c in self._onto_classes() if str(c) in cls]

    def _count_instances(self, concept, kg: KnowledgeGraph):
        return len([n for n, data in kg.nodes(data=True) if data["class"] in [concept]])

    def _str2class(self, concept: str):
        for cls in self._onto_classes():
            if str(cls) == concept:
                return cls


@dataclass
class HeterogeneousLinSimilarity(SemanticSimilarity):
    def IC(self, concept: str, kg: KnowledgeGraph) -> np.float64:
        """Information Content of a concept within a knowledge graph

        Parameters
        ----------
        concept : str
            Concept
        kg : KnowledgeGraph
            Knowledge graph

        Returns
        -------
        np.float64
            Information content of the concept within the knowledge graph (negative log likelihood of this concept)
        """
        subcls = self._descendants_of(concept)
        subsumers = [n for n, data in kg.nodes(data=True) if data["class"] in subcls]
        n_instances = len(subsumers)
        p_c = n_instances / len(kg.nodes())
        negloglik_p_c = -np.log(p_c)
        return negloglik_p_c

    def LCS(self, concept1: str, concept2: str, as_str=True) -> Any:
        anc1 = self._ancestors_of(concept1, as_str=as_str)
        anc2 = self._ancestors_of(concept2, as_str=as_str)
        for c1, c2 in zip(*make_same_size(anc1, anc2)):
            if str(c1) == str(c2):
                lcs = c1
        return lcs
        """lin similarity between two concepts lying in two different knowledge graphs stemming from the same ontology."""

    def sim_lin(
        self, concepts: tuple[str, str], kg: tuple[KnowledgeGraph, KnowledgeGraph]
    ) -> np.float64:
        """Lin similarity between two concepts lying in two knowledge graphs stemming from the same ontology.

        Parameters
        ----------
        concepts : tuple[str, str]
            Concepts (lying in at least one of the two graphs)
        kg : tuple[KnowledgeGraph, KnowledgeGraph]
            Knowledge graphs with respect to which similarity will be computed

        Returns
        -------
        np.float64
            Lin similarity between the two concepts, takes values in [0, 1]
        """
        subkg1, subkg2 = kg[0], kg[1]
        c1, c2 = concepts[0], concepts[1]
        lcs = self.LCS(c1, c2)
        ic_lcs1 = self.IC(lcs, subkg1)
        ic_lcs2 = self.IC(lcs, subkg2)
        ic1 = self.IC(c1, subkg1)
        ic2 = self.IC(c2, subkg2)
        sim = (ic_lcs1 + ic_lcs2) / (ic1 + ic2)
        return sim

    def sim_subkgs(self, kg: tuple[KnowledgeGraph, KnowledgeGraph]) -> np.float64:
        """Similarity between two knowledge graphs

        Parameters
        ----------
        kg : tuple[KnowledgeGraph, KnowledgeGraph]
            Two knowledge graphs

        Returns
        -------
        np.float64
            Similarity between two knowledge graphs
        """
        maxsims_1 = np.array(
            [self.maxSim(data["class"], *kg) for _, data in kg[0].nodes(data=True)]
        )
        maxsims_2 = np.array(
            [
                self.maxSim(data["class"], *kg[::-1])
                for _, data in kg[1].nodes(data=True)
            ]
        )
        scores = 0.5 * np.append(maxsims_1 / maxsims_1.size, maxsims_2 / maxsims_2.size)
        return scores.sum()

    def maxSim(
        self, concept: str, in_kg: KnowledgeGraph, wrt_kg_ref: KnowledgeGraph
    ) -> np.float64:
        """Highest similarity index of a concept lying in a knowledge graph `in_kg`,
        with respect to all concepts in a reference knowledge graph `wrt_kg_ref`

        Parameters
        ----------
        concept : str
            Concept belonging at least to `in_kg`
        in_kg : KnowledgeGraph
            Knowledge graph containing the specific `concept`
        wrt_kg_ref : KnowledgeGraph
            Knowledge graph with respect to which similarity should be measured

        Returns
        -------
        np.float64
            Maximum similarity between `concept` and `wrt_kg_ref` (each concept thereof)
        """
        sim = 0.0
        for cls in self._all_classes_in(wrt_kg_ref):
            sim = np.nanmax([sim, self.sim_lin([concept, cls], [in_kg, wrt_kg_ref])])
        return sim


###
###     Scalability Metrics (taking requirements into consideration)
###


@dataclass
class ValidationMetric:

    world: World = default_world

    def degree_of_validation(
        self,
        queries: Sequence[tuple[Query | str, Query | str]],
        kg: KnowledgeGraph,
    ) -> dict:
        """Compute degrees of requirements validation

        Parameters
        ----------
        queries : Sequence[tuple[Query  |  str, Query  |  str]]
            Couples of queries (validating & non-validating)
        kg : KnowledgeGraph
            Query only within this knowledge graph

        Returns
        -------
        dict
            `valid_req`: number of validated requirements over the total number of requirements;
            `valid_rows`: total number of validating query results (rows)
                          over the total number of query results.
        """

        counts = {"valid_req": 0, "valid_rows": 0, "total_rows": 0}

        for query_ok, query_nok in queries:
            df_qok = sparql(query_ok, self.world, kg)
            df_qnok = sparql(query_nok, self.world, kg)

            # total number of instances the requirement is affected by
            counts["total_rows"] += len(df_qok) + len(df_qnok)
            # number of instances that validate the requirement
            counts["valid_rows"] += len(df_qok)
            # whether requirement is validated
            counts["valid_req"] += len(df_qnok) == 0

        metrics = {
            "valid_req": counts["valid_req"] / len(queries),
            "valid_rows": counts["valid_rows"] / counts["total_rows"],
        }
        return metrics

    def degree_of_scalability(
        self,
        queries: Sequence[tuple[Query | str, Query | str]],
        kg: tuple[KnowledgeGraph, KnowledgeGraph],
    ) -> dict:
        metrics = {
            "valid_req": 1
            - (
                self.degree_of_validation(queries, kg[0])["valid_req"]
                - self.degree_of_validation(queries, kg[1])["valid_req"]
            ),
            "valid_rows": 1
            - (
                self.degree_of_validation(queries, kg[0])["valid_rows"]
                - self.degree_of_validation(queries, kg[1])["valid_rows"]
            ),
        }
        return metrics
