import pandas
import pm4py

def import_csv(file_path: str) -> pandas.DataFrame:
    event_log = pandas.read_csv(file_path, sep=';')
    event_log = pm4py.format_dataframe(event_log, case_id='case_id',
                                           activity_key='activity', timestamp_key='timestamp')
    return event_log

def convert_csv_to_xes(csv_file_path: str) -> pandas.DataFrame:
    event_log = import_csv(csv_file_path)
    pm4py.write_xes(event_log, f"./{csv_file_path.split('.csv')[0]}.xes")
    return pm4py.read_xes(f"./{csv_file_path.split('.csv')[0]}.xes")