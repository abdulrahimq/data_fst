import argparse
import os
import random
import sys

from tqdm import tqdm
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def parse_att_file(att_path):
    """
    Parse a .att file and return:
      - transitions: list of (src, dst, in_symbol, out_symbol)
      - final_states: set of final-state IDs
    """
    transitions = []
    final_states = set()

    with open(att_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            # Check if line denotes a final state (1 column or 2 columns).
            if len(parts) == 1:
                # Single number => final state
                state_id = parts[0]
                final_states.add(state_id)
            elif len(parts) in [4, 5]:
                # src, dst, in_sym, out_sym, [weight?]
                src, dst, i_sym, o_sym = parts[:4]
                transitions.append((src, dst, i_sym, o_sym))
            else:
                pass
    return transitions, final_states


def extract_alphabet(transitions):
    """
    Returns all symbols that appear as input or output in the transitions.
    """
    alpha = set()
    for src, dst, i_sym, o_sym in transitions:
        alpha.add(i_sym)
        alpha.add(o_sym)
    return alpha


def transform_identity_arc(in_sym, out_sym, alphabet, args):
    """
    For arcs where in_sym == out_sym, randomly transform them with
    roughly 1/3 for deletion, 1/3 for substitution, 1/3 for addition.
    Sub-options for "add":
        - append 1/3
        - prepend 1/3
        - duplicate 1/3
    Returns (new_in, new_out).
    """
    choice = random.random()

    if choice < args.deletion_prob:
        # Deletion: c:ε
        return (in_sym, "")  # We'll interpret "" as epsilon/0
    elif choice < args.substitution_prob:
        # Substitution: c:x
        possible_subs = list(alphabet)
        # If you want to ensure the substitution is different from out_sym, do:
        # possible_subs = [x for x in alphabet if x != out_sym]
        if not possible_subs:
            return (in_sym, out_sym)
        new_out = random.choice(possible_subs)
        return (in_sym, new_out)
    else:
        # Add
        add_choice = random.random()
        possible_adds = list(alphabet)
        if not possible_adds:
            return (in_sym, out_sym)
        add_letter = random.choice(possible_adds)

        # Append c:cx
        if add_choice < args.append_prob:
            return (in_sym, out_sym + add_letter)
        # Prepend c:xc
        elif add_choice < args.prepend_prob:
            return (in_sym, add_letter + out_sym)
        else:
            # Duplicate c:cc
            return (in_sym, out_sym + out_sym)


def generate_randomized_fst(transitions, final_states, args, out_prefix="TLT_random", prefix_name=""):
    """
    Generate n new .att FSTs by randomly transforming identity arcs.
    Save them in the local folder (or adapt path as needed).
    """
    alpha = extract_alphabet(transitions)
    prefix = prefix_name[:-4].replace(".", "_")
    prefix = f"converted_fst/{prefix}"
    for i in range(args.num_variations):
        new_transitions = []
        for (src, dst, i_sym, o_sym) in transitions:
            new_in, new_out = transform_identity_arc(i_sym, o_sym, alpha, args)
            new_transitions.append((src, dst, new_in, new_out))

        # Write out a new .att
        output_dir = os.path.join(args.base_dir, prefix)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        out_file = (f"deletion_{args.deletion_prob}_substitution_{args.substitution_prob}_addition_{args.addition_prob}"
                    f"_prepend_{args.prepend_prob}_append_{args.append_prob}_{out_prefix}_{i}_"
                    f"{args.num_variations}").replace(".", "_") + ".att"
        out_path = os.path.join(output_dir, out_file)
        with open(out_path, 'w', encoding='utf-8') as f:
            # Transitions
            for (src, dst, i_sym, o_sym) in new_transitions:
                # interpret "" => "0" for epsilon
                if o_sym == "":
                    o_sym = "0"
                line = f"{src}\t{dst}\t{i_sym}\t{o_sym}\n"
                f.write(line)
            # Final states
            for st in sorted(final_states):
                f.write(f"{st}\n")
        # logger.info(f"Wrote randomized FST to {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_dir", type=str, default=os.path.dirname(os.path.abspath(__file__)),
                        help="Main directory")
    parser.add_argument("--data_dir", type=str, default="data", help="Data directory")
    parser.add_argument("--deletion_prob", type=float, default=0.33, help="Probability of deletion")
    parser.add_argument("--substitution_prob", type=float, default=0.33, help="Probability of substitution")
    parser.add_argument("--addition_prob", type=float, default=0.33, help="Probability of addition")
    parser.add_argument("--prepend_prob", type=float, default=0.5, help="Probability of prepend")
    parser.add_argument("--append_prob", type=float, default=0.5, help="Probability of append")
    parser.add_argument("--num_variations", type=int, default=100, help="Probability of append")
    parser.add_argument("--test", type=bool, default=False, help="Testing")
    args = parser.parse_args()

    logger.info(f"Args: {args}\nCommand Line: {sys.argv}\n")
    logger.info(f"Dict format: {vars(args)}")

    data_dir = os.path.join(args.base_dir, args.data_dir)
    files = os.listdir(data_dir)
    if args.test:
        files = files[:3]

    for att_filename in tqdm(files):
        att_path = os.path.join(data_dir, att_filename)
        if not os.path.isfile(att_path):
            logger.warning(f"Warning: {att_path} not found.")
            continue

        logger.info(f"Generating {args.num_variations} random FST(s) from {att_path} ...")
        transitions, final_states = parse_att_file(att_path)
        generate_randomized_fst(transitions, final_states, args, out_prefix="RandomFST", prefix_name=att_filename)

        logger.info(f"Wrote randomized FST to {att_filename}")
    logger.info(f"Finished running the whole code")


if __name__ == "__main__":
    main()
