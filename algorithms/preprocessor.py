import pandas
import pm4py
import inquirer

def import_csv(file_path: str, separator=";") -> pandas.DataFrame:

    log = pandas.read_csv(file_path, sep=separator)
    columns = log.columns.tolist()
    # Create a list of inquirer questions
    questions = [
        inquirer.List('case_column',
                    message="Select the column that contains the case ID",
                    choices=columns,
                    ),
        inquirer.List('activity_column',
                    message="Select the column that contains the activity names",
                    choices=columns,
                    ),
        inquirer.List('timestamp_column',
                    message="Select the column that contains the timestamps",
                    choices=columns,
                    )
    ]
    answers = inquirer.prompt(questions)
    case_id, activity_key, timestamp_key = answers['case_column'], answers['activity_column'], answers['timestamp_column']

    log = pm4py.format_dataframe(log, case_id=case_id, activity_key=activity_key, timestamp_key=timestamp_key)
    return log

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


def preprocess_log(log: pandas.DataFrame, selected_columns: list[str]) -> pandas.DataFrame:
    # TODO: Preprocessing data more efficiently
    # data_log = preprocess_log(log, selected_columns)
    # Preprocess the log for data traces
    questions = []
    for column in selected_columns:
        questions.append(inquirer.List(column,
                      message=f"Select the data type of the column: {column}. I'll give you a couple examples - {str(log[column].head(5).to_list())}",
                      choices=["Categorical", "Numerical"],
                     ))
    # Prompt user to select the activity column
    answers = inquirer.prompt(questions)
    for column in selected_columns:
        if answers[column] == "Categorical":
            log = pandas.get_dummies(log, columns=[column], dtype=int)
    return log

def user_select_case_column(dataframe) -> str:
    # Get all column names from the DataFrame
    columns = dataframe.columns.tolist()
    
    # Create a list of inquirer questions
    questions = [
                inquirer.List('case_column',
                      message="Select the column that contains the case ID",
                      choices=columns,
                     ),
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

    if len(answers['selected_columns']) == 0:
        print("Come on bro select one :<")
        return user_select_columns(dataframe)
    
    # Return the DataFrame with only selected columns
    return answers['selected_columns']