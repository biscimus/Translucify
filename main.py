from algorithms.preprocessor import convert_csv_to_xes, import_csv
from algorithms.alignment_based_generation import generate_translucent_log
import argparse
from algorithms.simple_algorithm import add_activities
from pm4py import read_xes
import pandas as pd
if __name__ == "__main__":

    # parser = argparse.ArgumentParser("simple_example")
    # parser.add_argument("threshold", help="The cutoff percentage.", type=float)
    # args = parser.parse_args()

    # log = convert_csv_to_xes("logs/log1.csv")
    # log = add_activities(log, args.threshold)

    log = import_csv("logs/helpdesk.csv", ",")

    log.rename(columns={"case_id": "case:concept:name", "activity": "concept:name", "timestamp": "time:timestamp"}, inplace=True)
    print(log)
    # log = read_xes("logs/sepsis.xes")
    # log = log[["case:concept:name", "concept:name"] + [col for col in log.columns if col != "case:concept:name" and col != "concept:name"]]
    # log.to_csv("logs/sepsis-sorted.csv", index=False)

    # print(log)