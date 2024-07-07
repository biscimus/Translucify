import pandas
import pm4py
import inquirer

def import_csv(file_path: str, case_id="case:concept:name", activity_key="concept:name", timestamp_key="time:timestamp", separator=";") -> pandas.DataFrame:
    event_log = pandas.read_csv(file_path, sep=separator)
    event_log = pm4py.format_dataframe(event_log, case_id=case_id,
                                           activity_key=activity_key, timestamp_key=timestamp_key)
    return event_log

def convert_csv_to_xes(csv_file_path: str) -> pandas.DataFrame:
    event_log = import_csv(csv_file_path)
    pm4py.write_xes(event_log, f"./{csv_file_path.split('.csv')[0]}.xes")
    return pm4py.read_xes(f"./{csv_file_path.split('.csv')[0]}.xes")

def user_select_activity_column(dataframe) -> str:
    # Get all column names from the DataFrame
    columns = dataframe.columns.tolist()
    
    # Create a list of inquirer questions
    questions = [
        inquirer.List('activity_column',
                      message="Select the column that contains the activity names",
                      choices=columns,
                      )
    ]
    
    # Prompt user to select the activity column
    answers = inquirer.prompt(questions)
    
    # Return the activity column name
    return answers['activity_column']

def user_select_case_column(dataframe) -> str:
    # Get all column names from the DataFrame
    columns = dataframe.columns.tolist()
    
    # Create a list of inquirer questions
    questions = [
        inquirer.List('case_column',
                      message="Select the column that contains the case ID",
                      choices=columns,
                      )
    ]
    
    # Prompt user to select the activity column
    answers = inquirer.prompt(questions)
    
    # Return the activity column name
    return answers['case_column']

def user_select_columns(dataframe) -> list[str]:
    # Get all column names from the DataFrame
    columns = dataframe.columns.tolist()
    
    # Create a list of inquirer questions
    questions = [
        inquirer.Checkbox('selected_columns',
                          message="Select columns you want to include in the output DataFrame",
                          choices=columns,
                          )
    ]
    
    # Prompt user to select columns
    answers = inquirer.prompt(questions)
    
    # Return the DataFrame with only selected columns
    return answers['selected_columns']