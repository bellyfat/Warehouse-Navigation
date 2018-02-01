import typing
import networkx as nx
from tsp import tsp_circuit
from utils import manhattan_distance


PositionType = typing.Tuple[int, int]


class GridWarehouse(object):
    dimensions = None  # type: PositionType
    grid = None  # type: [[GridWarehouseCell]]
    graph = None  # type: nx.Graph

    def __init__(self, dimensions, grid):  # type: (PositionType, [[GridWarehouseCell]]) -> None
        self.dimensions = dimensions
        self.grid = grid
        self.graph = self._construct_graph()
    
    def find_path(self, from_node, to_node):  # type: (PositionType, PositionType) -> [PositionType]
        return nx.shortest_path(self.graph, from_node, to_node)

    def find_pick_path(self, from_node, intermediate_nodes):  # type: (PositionType, PositionType, [PositionType]) -> [PositionType]

        # Create a graph on the nodes in this order (removes all nodes from graph not in this path)
        nodes = [from_node] + intermediate_nodes
        G_tsp = nx.Graph()
        for node in nodes:
            G_tsp.add_node(node)
        # Add edges into the graph corresponding to the manhattan distance between two points
        for idx_i, i in enumerate(nodes):
            for idx_j, j in enumerate(nodes):
                if i is not j:
                    G_tsp.add_edge(i, j, weight=manhattan_distance(i, j))

        # Compute the TSP
        tsp_tour = tsp_circuit(G_tsp, from_node)
        if tsp_tour is None:
            raise ValueError()

        # Now, re-introduce the intermediate nodes
        final_path = [tsp_tour[0]]
        for next_node in tsp_tour[1:]:
            current_node = final_path[-1]
            path_to_next_node = nx.shortest_path(self.graph, current_node, next_node)[1:]
            final_path += path_to_next_node

        return final_path

    def __str__(self):
        row_strings = []
        for column in self.grid:
            column_strings = []
            for cell in column:
                if isinstance(cell, NavigableTileCell):
                    column_strings.append("+")
                elif isinstance(cell, ShelvingCell):
                    column_strings.append("x")
                else:
                    raise TypeError("Unknown cell type: %s" % type(cell))
            row_strings.append("\t".join(column_strings) + "\n")
        return \
            "Grid Warehouse (%d height x %d width)\n" % self.dimensions + \
            "".join(row_strings)

    def _construct_graph(self):  # type: () -> nx.Graph
        graph = nx.Graph()

        # Add all navigable tiles as nodes
        for i, row in enumerate(self.grid):
            for j, cell in enumerate(row):
                if not isinstance(cell, NavigableTileCell):
                    continue
                graph.add_node((i, j))

        # Add all edges
        for i, row in enumerate(self.grid):
            for j, cell in enumerate(row):
                if not isinstance(cell, NavigableTileCell):
                    continue

                cell_coordinates = (i, j)

                neighbor_coordinates = self._get_neighboring_navigation_cells(cell_coordinates)

                for neighbor_cell_coordinate in neighbor_coordinates:  # type: typing.Tuple(int, int)
                    graph.add_edge(cell_coordinates, neighbor_cell_coordinate, weight=1)

        return graph

    def _get_neighboring_navigation_cells(self, origin_cell_coordinates):  # type: () -> [typing.Tuple(int, int)]
        offsets = [
            (-1, 0),
            (0, +1),
            (+1, 0),
            (0, -1),
        ]

        neighbors = []

        for offset_x, offset_y in offsets:
            neighbor_coordinate_to_examine = (origin_cell_coordinates[0] + offset_x, origin_cell_coordinates[1] + offset_y)

            if neighbor_coordinate_to_examine[0] < 0 or neighbor_coordinate_to_examine[0] >= self.dimensions[0]:
                continue

            if neighbor_coordinate_to_examine[1] < 0 or neighbor_coordinate_to_examine[1] >= self.dimensions[1]:
                continue

            neighbor_cell = self.grid[neighbor_coordinate_to_examine[0]][neighbor_coordinate_to_examine[1]]

            if not isinstance(neighbor_cell, NavigableTileCell):
                continue

            neighbors.append(neighbor_coordinate_to_examine)

        return neighbors


class GridWarehouseCell(object):
    pass


class Direction(object):
    NORTH = 1
    EAST = 2
    SOUTH = 3
    WEST = 4


class ShelvingCell(GridWarehouseCell):
    item = None  # type: Item
    direction = None  # type: Direction

    def __init__(self, direction):
        self.direction = direction


class NavigableTileCell(GridWarehouseCell):
    pass


class Item(object):
    name = None  # type: str
    rfid = None  # type: str