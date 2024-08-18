from pm4py import read_xes
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def dependency_detection(log: pd.DataFrame):
    activities = log["concept:name"].unique()
    print("activities: ", activities)
    # Create a dataframe matrix with shape of activities x activities
    dependency_matrix = pd.DataFrame(0, activities, activities)

    def fill_dependency_matrix(group: pd.DataFrame) -> pd.DataFrame:
        trace = list(group["concept:name"].values)

        prev_activitiy = None
        for activity in trace:
            current_activity = trace.pop(0)
            if prev_activitiy is not None:
                dependency_matrix.loc[prev_activitiy, current_activity] += 1
            prev_activitiy = current_activity
        return group
    
    log.groupby("case:concept:name", group_keys=False).apply(fill_dependency_matrix, include_groups=False).reset_index()

    print("Dependency:", dependency_matrix)

    # compute correlation of dependency matrix
    # correlation_matrix = dependency_matrix.corr()
    # mean_abs_corr = correlation_matrix.abs().mean()
    # print("independent columns: ", mean_abs_corr.sort_values(ascending=False))

    dependency_matrix = dependency_matrix.div(dependency_matrix.sum(axis=1), axis=0)
    dependency_matrix.fillna(0, inplace=True)
    print("Normalized Dependency:", dependency_matrix)
    dependency_matrix.to_csv("dependency_matrix.csv", sep=";")

    # Count how many times "Leucocytes" occurs between "ER Registration" and "Release A Patient"
    


    # dependency_correlation_matrix = pd.DataFrame(0, activities, activities, dtype="float")

    # for i in range(dependency_matrix.shape[0]):
    #     for j in range(dependency_matrix.shape[1]):
    #         if i != j:
    #             dependency_correlation_matrix.iloc[i, j] = ( dependency_matrix.iloc[i, j] - dependency_matrix.iloc[j, i] ) / ( dependency_matrix.iloc[i, j] + dependency_matrix.iloc[j, i] + 1)
    #         else:
    #             dependency_correlation_matrix.iloc[i, j] = dependency_matrix.iloc[i, j] / (dependency_matrix.iloc[i, j] + 1)

    # print("Correlation:", dependency_correlation_matrix)
    # dependency_correlation_matrix.to_csv("dependency_matrix.csv", sep=";")

def singleton_detection(log: pd.DataFrame):
    activities = log["concept:name"].unique()
    cases = log["case:concept:name"].unique()

    case_activity_matrix = pd.DataFrame(0, cases, activities)

    for case in cases:
        case_activities = log[log["case:concept:name"] == case]["concept:name"].values
        for activity in case_activities:
            case_activity_matrix.loc[case, activity] += 1

    print("case_activity_matrix: ", case_activity_matrix)

    # Return set of columns where all values are max. 1
    singleton_activities = case_activity_matrix.columns[(case_activity_matrix <= 1).all()].to_list()
    print("Singleton activities: ", singleton_activities)

    return singleton_activities

if __name__ == "__main__":
    log = read_xes("../logs/sepsis.xes")
    dependency_detection(log)
    # singleton_detection(log)

    