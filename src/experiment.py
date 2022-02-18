from anomaly_detector import AnomalyDetector
import argparse
from graph import Graph
from model import Model
from searcher import Searcher
from evaluator import Evaluator
import random

def insert_anomaly(ds_name, q=0.005):
    with open("../data/" + ds_name + ".txt", "r") as f:
        txt = f.read()
        data = txt.strip().split("\n")
        data = [i.split() for i in data]
        nodes = set()
        for d in data:
            nodes.add(d[0])
            nodes.add(d[2])
        edges = set([x[1] for x in data])
        nodes = tuple(nodes)
        edges = tuple(edges)

        selected_nodes = []
        for i in range(int(q*len(nodes))):
            selected_nodes.append(random.choice(nodes))
        anom_edges = []
        for h in selected_nodes:
            x = random.choice((1,2))
            r1 = random.choice(edges)
            t1 = random.choice(nodes)
            # while(t1==h):
            #     t1 = random.choice(nodes)
            anom_edges.append([h, r1, t1])
            txt += (h+" "+r1+" "+t1+"\n")

            if x == 2:
                r2 = random.choice(edges)
                t2 = random.choice(nodes)
                # while (t2 == h):
                #     t2 = random.choice(nodes)
                anom_edges.append([h, r2, t2])
                txt += (h + " " + r2 + " " + t2 + "\n")

        with open("../data/" + ds_name + "_anomaly.txt", "w") as f:
            f.write(txt)
            print(len(anom_edges), ("anomalies inserted in " + ds_name + "_anomaly.txt"))

        true_edges = []
        for i in range(len(anom_edges)):
            true_edges.append(random.choice(data))
        return anom_edges, true_edges

def rank_edges(edges, anomaly_detector):
    scores_edges = [(anomaly_detector.score_edge(e), e) for e in edges]
    return sorted(scores_edges, reverse=True)

def err_at_k(ranks, k, anom_edges):
    while k<len(ranks) and ranks[k][0]==ranks[k-1][0]:
        k+=1
    err = 0
    for i in range(k):
        if ranks[i][1] in anom_edges:
            err+=1
    return err, k


def parse_args():
    def str2bool(v):
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    parser = argparse.ArgumentParser()
    parser.add_argument('--graph',
                        '-g',
                        type=str,
                        required=True,
                        help='The name of graph: nell or dbpedia if using our parsed data.')
    parser.add_argument('--rule_merging',
                        '-Rm',
                        type=str2bool,
                        default=False,
                        required=False,
                        help='If True, then run merging refinement (Section 4.2.2).')
    parser.add_argument('--rule_nesting',
                        '-Rn',
                        type=str2bool,
                        default=False,
                        required=False,
                        help='If True, then run nesting refinement (Section 4.2.2).')
    parser.add_argument('--idify',
                        '-i',
                        type=str2bool,
                        default=True,
                        required=False,
                        help='If True, then convert entities to integer ids for faster processing.')
    parser.add_argument('--verbosity',
                        '-v',
                        type=int,
                        default=1000000,
                        required=False,
                        help='How often to print output. If 0, then silence output.')
    parser.add_argument('--output_path',
                        '-o',
                        type=str,
                        default='../output/',
                        help='path for output and log files')
    return parser.parse_args()


if __name__ == "__main__":
    # print(insert_anomaly("nell"))
    args = parse_args()

    q = 0.005
    anom_edges, true_edges = insert_anomaly(args.graph, q)

    graph = Graph(args.graph+"_anomaly", idify=args.idify, verbose=args.verbosity > 0)
    if args.verbosity > 0:
        print('Graph loaded.')
    searcher = Searcher(graph)
    if args.verbosity > 0:
        print('Creating model.')

    model = searcher.build_model(verbosity=args.verbosity,
                                 passes=2,
                                 label_qualify=True,
                                 order=['mdl_err', 'coverage', 'lex'])
    if args.verbosity > 0:
        print('***** Initial model *****')
        model.print_stats()
        model.save('{}{}_model'.format(args.output_path, args.graph))

    if args.rule_merging:
        model = model.merge_rules(verbosity=args.verbosity)
        if args.verbosity > 0:
            print('***** Model refined with Rm *****')
            model.print_stats()
            model.save('{}{}_model_Rm'.format(args.output_path, args.graph))

    if args.rule_nesting:
        model = model.nest_rules(verbosity=args.verbosity)
        if args.verbosity:
            print('***** Model refined with Rn *****')
            model.print_stats()
            model.save('{}{}_model_Rm_Rn'.format(args.output_path, args.graph))


    anomaly_detector = AnomalyDetector(model)
    # edge = ('concept:biotechcompany:intuit', 'concept:acquired', 'concept:company:mint')
    # print(anomaly_detector.score_edge(edge))
    # edge = ('concept:company:sap_ag', 'concept:atdate', 'concept:dateliteral:n2008')
    # print(anomaly_detector.score_edge(edge))
    test_set = anom_edges + true_edges
    ranks = rank_edges(test_set, anomaly_detector)
    # print(anom_edges)
    # print(ranks)
    err, k = err_at_k(ranks, 100, anom_edges)
    print(len(ranks))
    print("k:", k)
    print("Precision@100:", err/k)
    print("Recall@100:", err/len(anom_edges))