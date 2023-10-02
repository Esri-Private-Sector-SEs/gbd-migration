import time, random

def chunks(lst, n):
    """
    Divides a lst into chunks of size n.
    """
    
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
        
def flatten_data(y):
    """
    Flattens some json (y) to a string.
    """
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x
            
    flatten(y)
    return out

def remove_none_vals(dictionary):
    """
    Removes all none type values from a dictionary of any depth. 
    """
    for k, v in dictionary.items():
        if isinstance(v, list):
            dictionary[k] = [i for i in v if i is not None]
    return dictionary

def retry_with_backoff(fn, retries=5, backoff_in_seconds=1):
    """
    Executes the retry with exponential backoff algorithm to avoid API call timeouts.
    
    Args:
        fn (function): some function to retry
        retries (int): number of retries before raising to caller
        backoff_in_seconds (int): backoff time in seconds for which to calculate exponential sleep length
    """
    x = 0
    while True:
        try:
            return fn()
        except:
            if x == retries:
                raise
            
            sleep = (backoff_in_seconds * 2 ** x + random.uniform(0, 1))
            time.sleep(sleep)
            x += 1

def topological_sort_grouped(G):
    """
    source: https://stackoverflow.com/questions/56802797/digraph-parallel-ordering

    Performs a topological sort where nodes entering the queue at the same time are stored in the same element. 
    
    Arguments:
        - G: <Networkx Directed Graph>
    Returns:
        - <iterator>
        
    Source: https://stackoverflow.com/questions/56802797/digraph-parallel-ordering
    """
    indegree_map = {v: d for v, d in G.in_degree() if d > 0}
    zero_indegree = [v for v, d in G.in_degree() if d == 0]
    while zero_indegree:
        yield zero_indegree
        new_zero_indegree = []
        for v in zero_indegree:
            for _, child in G.edges(v):
                indegree_map[child] -= 1
                if not indegree_map[child]:
                    new_zero_indegree.append(child)
        zero_indegree = new_zero_indegree