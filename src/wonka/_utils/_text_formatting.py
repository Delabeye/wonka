"""

Text formatting

"""

from rdflib.plugins.sparql import parser, algebra
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.algebra import translateQuery
from rdflib.plugins.sparql.processor import prepareQuery
from rdflib import Namespace, XSD, RDF, RDFS, OWL
from rdflib.term import Variable, URIRef, BNode, Literal
from rdflib.plugins.sparql.parserutils import *


def format_iri(obj, base_iri=None, refactor=False):
    """remove base_iri from obj's label (or change it to refactor.) and cast to str (instead of owlready2 classes)"""
    # if base_iri is None or refactor is False:
    #     return str(obj)
    # elif refactor is True:
    #     return str(obj).replace(f"{base_iri}.", "")
    # elif isinstance(refactor, str):
    #     return str(obj).replace(f"{base_iri}.", f"{refactor}.")
    return str(obj)


def format_predicate(p, base_iri=None, refactor=False):
    mapping = {"saref:": "core.", "saref4inma:": "saref4inma."}
    # if base_iri is not None and refactor is False:
    #     mapping[f"{base_iri}:"] = f"{base_iri}."
    #     mapping[f"onto:"] = f"{base_iri}."
    # if base_iri is not None and refactor is True:
    #     mapping[f"{base_iri}:"] = ""
    #     mapping[f"onto:"] = ""
    # elif base_iri is not None and isinstance(refactor, str):
    #     mapping[f"{base_iri}:"] = f"{refactor}."
    #     mapping[f"onto:"] = f"{refactor}."
    for k, v in mapping.items():
        p = str(p).replace(k, v)
    p = p.replace(":", ".")
    return p


def token2name(token):
    tname = token
    if getattr(token, "name", None) == "PathAlternative":
        tname = token["part"][0]["part"][0]["part"]
    if isinstance(tname, Variable):
        return f"?{str(tname)}"
    elif isinstance(tname, URIRef):
        if str(tname) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
            return "rdf:type"
        return f"<{str(tname)}>"
    else:
        prefix, lname = "" or tname["prefix"], tname["localname"]
        return f"{prefix}:{lname}"


def owl2_to_prefixed(name: str):
    mapping = {"core.": "saref:", "saref4inma.": "saref4inma:"}
    for k, v in mapping.items():
        name = name.replace(k, v).replace(".", ":")
    return name
