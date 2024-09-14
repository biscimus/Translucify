from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from flask_cors import CORS
import sqlalchemy as sql
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase
import enum
import os
from flask import request, jsonify, send_file
from flask_alembic import Alembic
import csv
import pandas as pd
import requests
import uuid
from celery import Celery, Task, shared_task
import shutil

from algorithms.preprocessor import fetch_dataframe
from algorithms.simple_prefix_automaton import discover_translucent_log_from_pa, generate_prefix_automaton
from algorithms.postprocessor import decode_prefix_automaton, encode_prefix_automaton
from algorithms.simple_model_algorithm import discover_translucent_log_from_model
from tasks import process_translucent_log_from_petri_net

# Celery configuration
def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

# Init app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'

# Add Celery
app.config.from_mapping(
    CELERY=dict(
        broker_url="redis://localhost:6379/0",
        result_backend="redis://localhost:6379/0",
        task_ignore_result=True,
    ),
)

# Use command "celery -A app.celery worker --loglevel INFO" to start the worker
celery = celery_init_app(app)

# Enable CORS
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Migration Tool
alembic = Alembic()
alembic.init_app(app)

# Models
class Base(DeclarativeBase):
    pass

# Database
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class EventLogType(enum.Enum):
    CSV = "CSV"
    XES = "XES"

class ProcessModelType(enum.Enum):
    PETRINET = "PETRINET"
    PREFIX_AUTOMATON = "PREFIX_AUTOMATON"

class EventLog(Base):
    __tablename__ = "log"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sql.String(255))
    type: Mapped[EventLogType] = mapped_column(sql.Enum(EventLogType))
    file_path: Mapped[str] = mapped_column(sql.String)
    translucnet_event_logs = db.relationship('TranslucentEventLog', cascade="all,delete", backref='event_log')

class TranslucentEventLog(Base):
    __tablename__ = "translucent_log"
    id: Mapped[UUID]= mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sql.String(255))
    type: Mapped[EventLogType] = mapped_column(sql.Enum(EventLogType))
    file_path: Mapped[str] = mapped_column(sql.String)
    is_ready: Mapped[bool] = mapped_column(sql.Boolean)
    # foreign key to EventLog
    event_log_id: Mapped[int] = mapped_column(sql.ForeignKey('log.id'))

class ProcessModel(Base):
    __tablename__ = "process_model"
    id: Mapped[UUID]= mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sql.String(255))
    type: Mapped[ProcessModelType] = mapped_column(sql.Enum(ProcessModelType))
    value: Mapped[str] = mapped_column(sql.String)

with app.app_context():
    db.create_all()

# Routes

@app.route("/process-models", methods=["GET", "POST"])
def process_models():
    if request.method == "GET":
        rows = db.session.execute(db.select(ProcessModel)).scalars().all()
        return jsonify(rows)
    elif request.method == "POST":
        return "Create a new process model", "hey"

@app.route("/process-models/<uuid:id>", methods=["DELETE"])
def process_model(id):
    process_model = db.get_or_404(ProcessModel, id)
    db.session.delete(process_model)
    db.session.commit()

    
@app.route("/event-logs", methods=["GET", "POST"])
def event_logs():
    if request.method == "GET":
        logs = db.session.execute(db.select(EventLog)).scalars().all()
        # Convert to list of dictionaries for json

        log_dicts = [{
            "id": log.id,
            "name": log.name,
            "type": log.type.value,
            "file_path": log.file_path
        } for log in logs]
        return jsonify(log_dicts)


    elif request.method == "POST":

        if 'value' not in request.files:
            return "No file sent", 400
        
        name, type, file, delimiter = request.form.get("name"), request.form.get("type"), request.files.get("value"), request.form.get("delimiter")


        print("Delimiter: ", delimiter)

        # Save file first
        # Make subdirectory with file name under logs 
        os.makedirs(os.path.join("logs", name), exist_ok=True)

        file_path = os.path.join("logs", name, file.filename)
        print("File path: ", file_path)
        file.save(file_path)

        # Change delimiter if necessary
        if (delimiter != ""):
            print("Changing delimiter") 
            with open(file_path, "r") as infile:    
                reader = csv.reader(infile, delimiter=delimiter) 
                 
                with open(file_path + "delimit", "w") as outfile:
                    writer = csv.writer(outfile, delimiter=';')
                    writer.writerows(reader)

            # Remove old file
            os.remove(file_path)
            # # Rename new file
            os.rename(file_path + "delimit", file_path)
            
        # Save file as database entry
        event_log = EventLog(name=name, type=type, file_path=file_path)

        db.session.add(event_log)
        db.session.commit()

        # Return columns of the dataframe
        df = fetch_dataframe(file_path, type)
        columns = df.columns.tolist()
        print("Columns: ", columns)
        return {
            "id": event_log.id,
            "columns": columns 
        }
    
@app.route("/event-logs/<uuid:id>/metadata", methods=["GET"])
def event_log_metadata(id):

    print("Event log id in metadata: ", id)
    event_log = db.get_or_404(EventLog, id)


    return jsonify({
            "id": event_log.id,
            "name": event_log.name,
            "type": event_log.type.value,
        })
    
@app.route("/event-logs/<uuid:id>", methods=["GET", "PATCH", "DELETE"])
def event_log(id):
    print("Event log id in columns: ", id)
    if request.method == "GET":
        event_log = db.get_or_404(EventLog, id)
        # Get file path and send it back
        print("File path: ", event_log.file_path)
        df = fetch_dataframe(event_log.file_path, event_log.type.value)

        # Put Columns case:concept:name, concept:name, time:timestamp in front
        priority_columns = ["case:concept:name", "concept:name", "time:timestamp"]
        df = df[priority_columns + [col for col in df.columns if col not in priority_columns]]

        df_json = df.to_json()
        result = jsonify({
            "id": event_log.id,
            "name": event_log.name,
            "type": event_log.type.value,
            "value": df_json
        })

        return result
    elif request.method == "PATCH":
        return "Update event log"
    elif request.method == "DELETE":

        # Delete event log entity from database & log folder
        event_log = db.get_or_404(EventLog, id)

        # Remove directory with the same name as the event log in the logs subdirectory
        try:
            shutil.rmtree(os.path.join("logs", event_log.name))
        except FileNotFoundError:
            print("Directory not found")
        db.session.delete(event_log)
        db.session.commit()



        return "Deleted event log"

@app.route("/event-logs/<uuid:id>/columns", methods=["PATCH", "GET"])
def event_log_columns(id):
    print("Event log id in columns: ", id)
    if request.method == "GET":
        event_log = db.get_or_404(EventLog, id)
        df = fetch_dataframe(event_log.file_path, event_log.type.value)
        columns = df.columns.tolist()
        return jsonify(columns)
    
    elif request.method == "PATCH":
        event_log = db.get_or_404(EventLog, id)
        file_path = event_log.file_path
        print("Update columns for: ", file_path)
        # Get request body
        body = request.json
        columns = body.get("columns")
        print("Columns: ", columns)

        df = fetch_dataframe(file_path, event_log.type.value)

        df.rename(columns={columns.get("caseId"): "case:concept:name", columns.get("activity"): "concept:name", columns.get("timestamp"): "time:timestamp"}, inplace=True)

        print("Changed dataframe: ", df)

        df.to_csv(file_path, sep=";", index=False)

        return "Update columns for event log"

@app.route("/event-logs/<uuid:id>/prefix-automaton", methods=["GET", "POST"])
def prefix_automaton(id):
    if request.method == "GET":
        event_log = db.get_or_404(EventLog, id)
        df = fetch_dataframe(event_log.file_path, event_log.type.value)
        prefix_automaton = generate_prefix_automaton(df)
        payload = encode_prefix_automaton(prefix_automaton)
        return jsonify(payload)
    elif request.method == "POST":
        event_log = db.get_or_404(EventLog, id)

        base_name, extension = os.path.splitext(event_log.file_path)
        file_path = os.path.join(base_name + "_translucent_petri_net" + extension)

        # Save to database first
        translucent_log = TranslucentEventLog(name=event_log.name + "_translucent_prefix_automaton", type=EventLogType.CSV, file_path=file_path, is_ready=False, event_log_id=event_log.id)
        db.session.add(translucent_log)
        db.session.commit()
        
        body = request.json
        states = body.get("states")
        transitions = body.get("transitions")
        threshold = body.get("threshold")
        selected_columns = body.get("selectedColumns")
        process_translucent_log_from_prefix_automaton.delay(event_log.file_path, states, transitions, threshold, selected_columns, translucent_log.id, translucent_log.file_path)

        return jsonify({
        "message": "Translucent Log Generation (Prefix Automaton) in progress",
        "translucent_log_id": translucent_log.id
        }), 202
        
@shared_task
def process_translucent_log_from_prefix_automaton(file_path, states, transitions, threshold, selected_columns, translucent_log_id, translucent_log_file_path):
    prefix_automaton = decode_prefix_automaton(states, transitions)
    df = discover_translucent_log_from_pa(file_path, prefix_automaton, selected_columns, threshold)

    # Save the translucent log to file system
    df.to_csv(translucent_log_file_path, sep=";", index=False)

    translucent_log = db.get_or_404(TranslucentEventLog, translucent_log_id)

    # Edit the database entry to mark it as ready
    translucent_log.is_ready = True
    db.session.commit()

    return df.to_json()


@app.route("/event-logs/<uuid:id>/petri-net", methods=["POST"])
def event_log_petri_net(id):
    body = request.json
    data_columns = body.get("columns")
    threshold: float = body.get("threshold")

    event_log = db.get_or_404(EventLog, id)
    base_name, extension = os.path.splitext(event_log.file_path)
    file_path = os.path.join(base_name + "_translucent_petri_net" + extension)

    # Save to database first
    translucent_log = TranslucentEventLog(name=event_log.name + "_translucent_petri_net", type=EventLogType.CSV, file_path=file_path, is_ready=False, event_log_id=event_log.id)

    db.session.add(translucent_log)
    db.session.commit()

    process_translucent_log_from_petri_net.delay(event_log.file_path, data_columns, threshold, translucent_log.id, translucent_log.file_path)

    return jsonify({
        "message": "Translucent Petri Net generation in progress",
        "translucent_log_id": translucent_log.id
    }), 202

@shared_task
def process_translucent_log_from_petri_net(file_path, data_columns, threshold, translucent_log_id, translucent_log_file_path):

    # Perform the long-running task
    df = discover_translucent_log_from_model(file_path, data_columns, threshold)

    # Save the translucent log to file system
    df.to_csv(translucent_log_file_path, sep=";", index=False)

    # Mark the translucent log as ready in the database
    translucent_log = db.get_or_404(TranslucentEventLog, translucent_log_id)
    translucent_log.is_ready = True
    db.session.commit()

    return translucent_log.id

    
@app.route("/event-logs/<uuid:id>/transformer", methods=["POST"])
def event_log_transformer(id):

    event_log = db.get_or_404(EventLog, id)
    base_name, extension = os.path.splitext(event_log.file_path)
    file_path = os.path.join(base_name + "_translucent_transformer" + extension)

    # Save to database first
    translucent_log = TranslucentEventLog(name=event_log.name + "_translucent_transformer", type=EventLogType.CSV, file_path=file_path, is_ready=False, event_log_id=event_log.id)

    print("created translucent log: ", translucent_log)
    db.session.add(translucent_log)
    db.session.commit()

    threshold = request.json.get("threshold")
    # df = translucify_with_transformer(df, data_columns, threshold)

    # Get csv file
    with open(event_log.file_path, 'rb') as file:
        # Create the payload with the file object
        files = {'file': file}
        print("Sending request...")
        # Get translucent log from transformer microservice 
        response = requests.post("http://127.0.0.1:3000/", files=files, data={'id': str(id), 'threshold': str(threshold)})
        print("Response in post: ", response)
        df = pd.read_json(response.text)
        print("translucnet data frame: ", df)
        # Save the translucent log to file system
        df.to_csv(file_path, sep=";", index=False)

        translucent_log = db.get_or_404(TranslucentEventLog, translucent_log.id)

        # Edit the database entry to mark it as ready
        translucent_log.is_ready = True
        db.session.commit()

        return "Transformed event log"


@app.route("/event-logs/<uuid:id>/translucent-logs", methods=["GET"])
def translucent_logs(id):
    translucent_logs = db.session.execute(db.select(TranslucentEventLog).filter_by(event_log_id=id)).scalars()

    log_dicts = [{
        "id": log.id,
        "name": log.name,
        "type": log.type.value,
        "file_path": log.file_path,
        "is_ready": log.is_ready
    } for log in translucent_logs]
    return jsonify(log_dicts)

@app.route("/translucent-event-logs/<uuid:id>", methods=["GET", "DELETE"])
def translucent_log(id):
    if request.method == "GET":
        translucent_log = db.get_or_404(TranslucentEventLog, id)
        file_path = translucent_log.file_path
        print("file path: ", file_path)
        
        return send_file(file_path, as_attachment=True)
    elif request.method == "DELETE":
        translucent_log = db.get_or_404(TranslucentEventLog, id)
        db.session.delete(translucent_log)
        db.session.commit()
        return "Deleted translucent log"
