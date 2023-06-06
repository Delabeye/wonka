"""
Graph formatting for visualisation using pyvis.network
"""

defaultColors = [
    "#1f77b3",
    "#ff7e0e",
    "#2ba02b",
    "#d62628",
    "#9367bc",
    "#8c564b",
    "#e277c1",
    "#7e7e7e",
    "#bcbc21",
    "#16bdcf",
    "#3a0182",
    "#004201",
    "#0fffa8",
    "#5d003f",
    "#bcbcff",
    "#d8afa1",
]
(
    BLUE,
    ORANGE,
    GREEN,
    RED,
    PURPLE,
    BROWN,
    PINK,
    GRAY,
    YELLOW,
    CYAN,
    DARKPURPLE,
    DARKGREEN,
    LIGHTGREEN,
    DARKRED,
    LAVENDER,
    LIGHTBROWN,
    BLACK,
    WHITE,
    GRAY2,
) = (*defaultColors, "#000000", "#ffffff", "#808080")

###################################################################################
###                                  Nodes                                      ###
###################################################################################

#  {'shape':'ellipse', 'color':{'border': BLACK, 'background': 'white'}}

gformat_node = {
    # nodeType
    "variable": dict(
        shape="box",
        color={"border": BLACK, "background": WHITE},
        style="dashed",
        shapeProperties={"borderDashes": [5, 5]},
    ),
    # "variable": dict(
    #     shape="dot",
    #     style=None,
    #     shapeProperties=None,
    # ),
    "class": dict(
        shape="box",
        color={"border": BLACK, "background": BLACK},
        font={"color": WHITE},
    ),
    "instance": dict(
        shape="box",
        color={"border": BLACK, "background": WHITE},
        style="dashed",
        shapeProperties={"borderDashes": [5, 5]},
    ),
    # "instance": dict(
    #     shape="box",
    #     style=None,
    #     shapeProperties=None,
    # ),
    "data": dict(),
    # status
    "ok": dict(
        color=GREEN,
    ),
    "new": dict(
        color=RED,
    ),
    "existing": dict(
        color=BLUE,
    ),
    "unsued": dict(),  # gray out -> not used
    # default : do nothing
    None: {},
}

###################################################################################
###                                  Edges                                      ###
###################################################################################

# {'dashes':True, 'color':RED, 'arrows':{'to': {'enabled': True}}}

gformat_edge = {
    # option
    "var2var": dict(
        dashes=True,
        arrows={"to": {"enabled": True}},
    ),
    "var2class": dict(
        dashes=False,
        arrows={"to": {"enabled": True}},
    ),
    #
    "must_exist": dict(
        color=BLACK,
    ),
    "must_not_exist": dict(
        color=RED,
    ),
    #
    #
    "exists": dict(
        color=BLUE,
    ),
    "not_exists": dict(
        color=BLACK,
    ),
    #
    # Status (helper)
    "ok": dict(
        color=GREEN,
        dashes=False,
    ),
    "ok_existing": {},
    "del_existing": {},
    "del": dict(
        color=RED,
        dashes=False,
    ),
    "add2ok": dict(
        color=RED,
        dashes=True,
    ),
    "add2new": dict(
        color=RED,
        dashes=True,
    ),
    "add2new_existing": {},
    "add2existing": dict(
        color=YELLOW,
        dashes=True,
    ),
    "warn": {},
    # default : do nothing
    None: {},
}

###################################################################################
###                               all formats                                   ###
###################################################################################

gformat = {
    "node": gformat_node,
    "edge": gformat_edge,
}


def fetch_gformat(gtype="node", format: str | tuple | list = None):
    """concatenate formats"""
    desired_format, format = {}, format if isinstance(format, (tuple, list)) else [
        format
    ]
    for f in format:
        desired_format.update(gformat[gtype][f])
    return desired_format
