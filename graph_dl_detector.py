import networkx as nx
import matplotlib.pyplot as plt

def parse_graph_state(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    graph_edges = []
    deadlock_cycle = []

    # Parse the graph state
    graph_state_section = True
    for line in lines:
        line = line.strip()
        if line.startswith("==="):
            if "Deadlock Cycle" in line:
                graph_state_section = False
            continue

        if graph_state_section:
            if "->" in line:
                node, neighbors_str = line.split("->")
                node = node.strip()
                neighbors = neighbors_str.strip("{} ").split(", ")
                for neighbor in neighbors:
                    graph_edges.append((node, neighbor))
        else:
            # Parse the deadlock cycle
            if "->" in line:
                deadlock_cycle = line.split(" -> ")

    return graph_edges, deadlock_cycle

def plot_graph(graph_edges, deadlock_cycle):
    G = nx.DiGraph()
    G.add_edges_from(graph_edges)

    # Define edge colors
    edge_colors = ['red' if (u, v) in zip(deadlock_cycle, deadlock_cycle[1:] + [deadlock_cycle[0]]) else 'black' for u, v in G.edges()]

    # Draw the graph
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=5000, font_size=10, edge_color=edge_colors, arrows=True, arrowsize=20)

    # Set the title
    plt.suptitle("Graph Representation with Deadlock Cycle Highlighted", fontsize=16)

    plt.show()

if __name__ == "__main__":
    graph_edges, deadlock_cycle = parse_graph_state('./dl_detector_logs/graph_state.txt')
    plot_graph(graph_edges, deadlock_cycle)
