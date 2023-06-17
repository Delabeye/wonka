from wonka.utils import *


def viz_nx_graph(
    nx_graph,
    toggle_physics=True,
    buttons=False,
    height="900px",
    width="1800px",
    relabel=True,
    save_as: Path | str = None,
):
    if relabel:
        for n, data in nx_graph.nodes(data=True):
            data["label"] = owl2_to_prefixed(str(n))
        for _, _, k, data in nx_graph.edges(keys=True, data=True):
            data["weight"] = owl2_to_prefixed(k)
    nt = Network(height, width, directed=True)
    nt.toggle_physics(toggle_physics)
    nt.from_nx(nx_graph)
    nt.set_edge_smooth("dynamic")
    if buttons:
        nt.show_buttons()
    if isinstance(save_as, Path | str):
        save_as = str(save_as)
        save_as = save_as if save_as.endswith(".html") else save_as + ".html"
    else:
        save_as = "viz_nx_graph.html"
    filename = Path(save_as).name
    nt.show(filename) # TODO save to location directly; do not open
    time.sleep(.01) # wait for the file to be created
    shutil.move(Path("./")/filename, save_as)
    # webbrowser.open(save_as)
