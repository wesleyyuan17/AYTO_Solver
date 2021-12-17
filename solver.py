import pandas as pd
import argparse
import json

from pulp import LpMaximize, LpMinimize, LpProblem, LpStatus, lpSum, LpVariable


def process_match_info(match_info):
    guys = dict(zip(match_info['guys'], range(10)))
    girls = dict(zip(match_info['girls'], range(10)))
    rounds = match_info['rounds']
    truth_booths = match_info['truth_booths']

    # clean up inputs to get tuples from strings
    for r in match_info['rounds']:
        pairs = []
        for p in r['pairs']:
            pairs.append(eval(p))
        r['pairs'] = pairs

    processed_truth_booths = {}
    for k, v in truth_booths.items():
        processed_truth_booths[eval(k)] = v
    truth_booths = processed_truth_booths

    return guys, girls, rounds, truth_booths


def names_to_idx(rounds, truth_booths, guys, girls):
    # convert names to index
    for r in rounds:
        name_to_num = []
        for m, f in r['pairs']:
            name_to_num.append( (guys[m], girls[f]) )
        r['pairs'] = name_to_num

    idx_truth_booths = {}
    for tb, match in truth_booths.items():
        idx_key = (guys[tb[0]], girls[tb[1]])
        idx_truth_booths[idx_key] = match
    truth_booths = idx_truth_booths

    return rounds, truth_booths


def solve(rounds, truth_booths, guys, girls):
    # Create the model
    m1 = LpProblem(name='S', sense=LpMinimize)

    # Define decision variables
    var = [[LpVariable(name='{},{}'.format(i,j), lowBound=0, cat='Binary') for j in range(10)] for i in range(10)]
    var_flat = [x for tup in var for x in tup]

    # Set objective function
    m1 += lpSum(var_flat)

    # each person has at most one confirmed match (allow less than for unsure matches)
    for i in range(10):
        m1 += (lpSum(var[i]) <= 1)
    for i in range(10):
        girl_matches = [var[j][i] for j in range(10)]
        m1 += (lpSum(girl_matches) <= 1)
        
    # truth booth results
    for k, v in truth_booths.items():
        m, f = k
        m1 += (var[m][f] == v)
        
    # matching ceremony results
    for r in rounds:
        matches = [var[m][f] for m, f in r['pairs']]
        m1 += (lpSum(matches) == r['num_matches'])
        
    # Solve the optimization problem
    status = m1.solve()

    # Get the results
    print('status: {}, {}'.format(m1.status, LpStatus[m1.status]))
    print('objective: {}'.format(m1.objective.value()))
        
    results_table = []
    for v in var:
        results_table.append([int(v[i].value()) for i in range(10)])
    results_pd = pd.DataFrame(results_table, index=list(guys.keys()), columns=list(girls.keys()))
    print(results_pd)
    # results_pd.to_csv('output.txt', sep=' ')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--match_info', dest='info', required=True, 
                        help='Path to json file with all round/truth booth results for constraints')
    args = parser.parse_args()

    # Define constraints - results of each round read from json
    # In rounds: index is guys, values is girls
    # In truth_booths: key is (guy, girl), value is result
    with open(args.info, 'r') as f:
        match_info = json.load(f)

    guys, girls, rounds, truth_booths = process_match_info(match_info)

    rounds, truth_booths = names_to_idx(rounds, truth_booths, guys, girls)

    solve(rounds, truth_booths, guys, girls)
