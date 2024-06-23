
import pm4py
from input_manager import convert_csv_to_xes
from alignment_based_generation import generate_translucent_log
import argparse
from simple_algorithm import add_activities

if __name__ == "__main__":

    parser = argparse.ArgumentParser("simple_example")
    parser.add_argument("threshold", help="The cutoff percentage.", type=float)
    args = parser.parse_args()

    log = convert_csv_to_xes("log1.csv")
    log = add_activities(log, args.threshold)

    print(log)


    # log = generate_translucent_log(log)
    # print(log)
    # pm4py.write_xes(log, "log1_translucent.xes")