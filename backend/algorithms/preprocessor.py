import os
import pandas
import pm4py
import inquirer

def import_csv(file_path: str, separator=";") -> pandas.DataFrame:

    log = pandas.read_csv(file_path, sep=separator)
    columns = log.columns.tolist()
    # Pass if the log has the correct columns
    if not ("case:concept:name" in columns and "concept:name" in columns and "time:timestamp" in columns):
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
        # Rename log columns to match the XES naming convention
        log.rename(columns={answers["case_column"]: "case:concept:name", answers["activity_column"]: "concept:name", answers["timestamp_column"]: "time:timestamp"}, inplace=True)
    
    log = log[["case:concept:name", "concept:name", "time:timestamp"] + [col for col in log.columns if col != "case:concept:name" and col != "concept:name" and col != "time:timestamp"]]
    log.to_csv(file_path, index=False)
    return log

def convert_csv_to_xes(csv_file_path: str) -> pandas.DataFrame:
    event_log = pandas.read_csv(csv_file_path, sep=";")
    pm4py.write_xes(event_log, f"./{csv_file_path.split('.csv')[0]}.xes")
    return pm4py.read_xes(f"./{csv_file_path.split('.csv')[0]}.xes")


def preprocess_log(log: pandas.DataFrame, selected_columns: list[str]) -> pandas.DataFrame:
    # TODO: Handle None values, e.g. mean imputation or interpolation
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

def fetch_dataframe(file_path: str, file_type: str) -> pandas.DataFrame:
    if file_type == "CSV":
        return pandas.read_csv(file_path, delimiter=";")
    elif file_type == "XES":
        return pm4py.read_xes(file_path)
    else:
        raise ValueError("Invalid file type. Please provide a valid file type: csv or xes")