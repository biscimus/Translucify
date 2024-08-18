import pandas
from pm4py.stats import get_start_activities

def add_activities(log: pandas.DataFrame, threshold: float) -> pandas.DataFrame:

    next_activity_table = get_next_activity_table(log)
    
    # Normalize the table
    next_activity_table = next_activity_table.div(next_activity_table.sum(axis=1), axis=0).fillna(0)

    # Clip values below threshold
    next_activity_table[next_activity_table < threshold] = 0

    # Create dictionary of enabled activities
    next_activities_dict = {index: set(next_activity_table.columns[row > 0]) for index, row in next_activity_table.iterrows()}
    # Make a set out of keys of start_activities
    start_activities = set(get_start_activities(log).keys())
    # Add start activities to next_activities_dict
    next_activities_dict.update({"start": start_activities})
    print(next_activities_dict)

    # Add enabled__activities column to DataFrame
    log["enabled__activities"] = None

    def fill_enabled_activities_column(group: pandas.Series) -> pandas.DataFrame:

        enabled_activities = next_activities_dict["start"].copy()

        for index, row in group.iterrows():
            enabled_activities.add(row["concept:name"])
            group.at[index, "enabled__activities"] = tuple(sorted(enabled_activities, key=str.lower))
            enabled_activities = next_activities_dict[row["concept:name"]].copy()
        return group

    return log.groupby("case:concept:name", group_keys=False).apply(fill_enabled_activities_column).reset_index()

def get_next_activity_table(log: pandas.DataFrame) -> pandas.DataFrame:

    # Get all activities in the log
    activities = log["concept:name"].unique()

    # Create a table where next_activity_table(a, b) = 2 means that activity a is followed by activity b twice 
    next_activity_table = pandas.DataFrame(0, activities, activities)

    def fill_next_activity_table(group: pandas.DataFrame) -> pandas.DataFrame:
        trace = list(group["concept:name"].values)
        # Pop first activity from trace and retrieve the activity
        current_activity = trace.pop(0)
        while trace: 
            next_activity = trace.pop(0)
            next_activity_table.loc[current_activity, next_activity] += 1
            current_activity = next_activity
        return group
    
    # Iterate over each group and add the next activities to the next_activity_table
    log.groupby("case:concept:name", group_keys=False).apply(fill_next_activity_table).reset_index()
    print(next_activity_table)
    return next_activity_table