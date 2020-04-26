import numpy as np
import networkx as nx
from karateclub.karateclub.estimator import Estimator
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from karateclub.karateclub.utils.treefeatures import WeisfeilerLehmanHashing

class GL2Vec(Estimator):
    r"""An implementation of `"GL2Vec" <https://link.springer.com/chapter/10.1007/978-3-030-36718-3_1>`_
    from the ICONIP '19 paper "GL2vec: Graph Embedding Enriched by Line Graphs with Edge Features".
    First, the algorithm creates the line graph of each graph in the graph dataset.
    The procedure creates Weisfeiler-Lehman tree features for nodes in graphs. Using
    these features a document (graph) - feature co-occurence matrix is decomposed in order
    to generate representations for the graphs.

    The procedure assumes that nodes have no string feature present and the WL-hashing
    defaults to the degree centrality. However, if a node feature with the key "feature"
    is supported for the nodes the feature extraction happens based on the values of this key.

    Args:
        wl_iterations (int): Number of Weisfeiler-Lehman iterations. Default is 2.
        dimensions (int): Dimensionality of embedding. Default is 128.
        workers (int): Number of cores. Default is 4.
        down_sampling (float): Down sampling frequency. Default is 0.0001.
        epochs (int): Number of epochs. Default is 10.
        learning_rate (float): HogWild! learning rate. Default is 0.025.
        min_count (int): Minimal count of graph feature occurences. Default is 5.
        seed (int): Random seed for the model. Default is 42.
    """
    def __init__(self, wl_iterations=2, dimensions=128, workers=4, down_sampling=0.0001,
                 epochs=10, learning_rate=0.025, min_count=5, seed=42):

        self.wl_iterations = wl_iterations
        self.dimensions = dimensions
        self.workers = workers
        self.down_sampling = down_sampling
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.min_count = min_count
        self.seed = seed

    def _create_line_graph(self, graph):
        r"""Getting the embedding of graphs.

        Arg types:
            * **graph** *(NetworkX graph)* - The graph transformed to be a line graph.

        Return types:
            * **line_graph** *(NetworkX graph)* - The line graph of the source graph.
        """
        graph = nx.line_graph(graph)
        node_mapper = {node: i for i, node in enumerate(graph.nodes())}
        edges = [[node_mapper[edge[0]], node_mapper[edge[1]]] for edge in graph.edges()]
        line_graph = nx.from_edgelist(edges)
        return line_graph

    def fit(self, graphs):
        """
        Fitting a GL2Vec model.

        Arg types:
            * **graphs** *(List of NetworkX graphs)* - The graphs to be embedded.
        """
        self._check_graphs(graphs)
        graphs = [self._create_line_graph(graph) for graph in graphs]
        documents = [WeisfeilerLehmanHashing(graph, self.wl_iterations, False) for graph in graphs]
        documents = [TaggedDocument(words=doc.get_graph_features(), tags=[str(i)]) for i, doc in enumerate(documents)]

        model = Doc2Vec(documents,
                        vector_size=self.dimensions,
                        window=0,
                        min_count=self.min_count,
                        dm=0,
                        sample=self.down_sampling,
                        workers=self.workers,
                        epochs=self.epochs,
                        alpha=self.learning_rate,
                        seed=self.seed)

        self._embedding = [model.docvecs[str(i)] for i, _ in enumerate(documents)]

    def get_embedding(self):
        r"""Getting the embedding of graphs.

        Return types:
            * **embedding** *(Numpy array)* - The embedding of graphs.
        """
        return np.array(self._embedding)
