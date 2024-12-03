import json
import argparse
import os

# calculate hash of a number set, so as to distinct between two sets
def set_hash(set_in):
    str_res = ""
    for num in set_in:
        str_res = f"{str_res}_{num}"
    return hash(str_res)

class MProxy():
    stored = ''
    leaf = None

    def print(self, str_in=''):
        self.stored += str_in + '\n'

    def get(self):
        return self.stored

    def get_leave_hash(self, ob):
        if self.leaf is None:
            self.leaf = hash(ob)
        return self.leaf 

# dfs function
# node: the current node to be visit
# logs: stores the name and some other might be useful attrs(now some of them are useless though)
# insides: stores all the nodes' full name of the same kind. For bundles, also stores the index of the unique bundle
# prefix: prefix str of current node
# bundle_names_counter: store the bundle name, which might be useful in the future
def visit(node, logs, insides, prefix, bundle_names_counter, rp:MProxy):
    leaf = True
    sons = set()
    for son_name in node:
        
        if type(node[son_name]) == dict:
            leaf = False
            whole_name = f"{prefix}{son_name}"
            grandsons, son_leaf = visit(node[son_name], logs, insides, f"{whole_name}_", bundle_names_counter, rp)
            inside_hash = set_hash(grandsons)
            cur_hashes = set()
            cur_hashes.add(son_name)
            cur_hashes.add(inside_hash)
            son_hash = set_hash(cur_hashes)
            if son_hash not in logs.keys():
                if son_leaf:
                    # son hash as outsiders with name added to hash
                    logs[son_hash] = (True, inside_hash, son_name, whole_name)
                else:
                    logs[son_hash] = (False, inside_hash, son_name, whole_name, grandsons)  
            if inside_hash not in insides.keys():
                insides[inside_hash] = [son_leaf, []]
                if not son_leaf:
                    # new bundle appears
                    insides[inside_hash].append(bundle_names_counter[0])
                    bundle_names_counter[1].append(f"_{bundle_names_counter[0]}Bundle")
                    rp.print(f"class {bundle_names_counter[1][bundle_names_counter[0]]}(Bundle):")

                    leaves = []
                    son_bundles = {}
                    for grandson in grandsons:
                        name = logs[grandson][2]
                        if logs[grandson][0]:
                            if prefix != "":
                                name = f"_{name}"
                            leaves.append(f"{name}")
                        else:
                            grandson_inside = logs[grandson][1]
                            if grandson_inside not in son_bundles:
                                son_bundles[grandson_inside] = []
                            son_bundles[grandson_inside].append(name)
                    if len(leaves) > 0:
                        leaves_str = ', '.join(leaves)
                        after_str = f"Signals({len(leaves)})" if len(leaves) > 1 else "Signal()"
                        rp.print(f"\t{leaves_str} = {after_str}")
                    for bundle_hash in son_bundles.keys():
                        bundle_cls = bundle_names_counter[1][insides[bundle_hash][2]]
                        for var_name in son_bundles[bundle_hash]:
                            if len(prefix) > 0:
                                var_name = f"_{var_name}"
                            rp.print(f"\t{var_name} = {bundle_cls}.from_prefix(\"{var_name}\")")
                    
                    rp.print()

                    bundle_names_counter[0] += 1

            insides[inside_hash][1].append(whole_name)
        else:
            son_hash = rp.get_leave_hash(node[son_name]) # for all leaves, ways to deal in toffee are same, they are all signals, so get a staic value equal to

        sons.add(son_hash)

    return sons, leaf

def main(signals_path, target_path):
    with open(signals_path, "r", encoding="utf-8") as sig_file:
        data = json.load(sig_file)

    notes = {}
    insides = {}
    module_name = "PredCheckerAll"
    rpr = MProxy()
    rpr.print("from toffee import Bundle, Signals, Signal\n")
    data = {module_name: data}
    sons, _ = visit(data, notes, insides, "", [0, []], rpr)

    with open(target_path, "w", encoding="utf-8") as tgt_f:
        tgt_f.write(rpr.get())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('signal', type=str, default='')
    parser.add_argument('target', type=str, default='')
    args = parser.parse_args()
    main(args.signal, args.target)