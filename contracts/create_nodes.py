from domain.node import Node

def create_nodes(node_ids: list[str]) -> set[Node]:
    nodes: set[Node] = set()

    for node_id in node_ids:
        node = Node(name=node_id)
        nodes.add(node)

    return nodes