from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import sqlalchemy as sql
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase
import enum
import os
from flask import request, jsonify, send_file
from flask_alembic import Alembic
import csv
import pandas as pd

from algorithms.preprocessor import fetch_dataframe
from algorithms.simple_model_algorithm import discover_translucent_log_from_model

# Init app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'

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
    id: Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(sql.String(255))
    type: Mapped[EventLogType] = mapped_column(sql.Enum(EventLogType))
    file_path: Mapped[str] = mapped_column(sql.String)
    translucnet_event_logs = db.relationship('TranslucentEventLog', backref='event_log')

class TranslucentEventLog(Base):
    __tablename__ = "translucent_log"
    id: Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(sql.String(255))
    type: Mapped[EventLogType] = mapped_column(sql.Enum(EventLogType))
    file_path: Mapped[str] = mapped_column(sql.String)
    is_ready: Mapped[bool] = mapped_column(sql.Boolean)
    # foreign key to EventLog
    event_log_id: Mapped[int] = mapped_column(sql.ForeignKey('log.id'))

class ProcessModel(Base):
    __tablename__ = "process_model"
    id: Mapped[int] = mapped_column(primary_key = True)
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

@app.route("/process-models/<int:id>", methods=["DELETE"])
def process_model(id):
    process_model = db.get_or_404(ProcessModel, id)
    db.session.delete(process_model)

    
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
        
        name, type, file = request.form.get("name"), request.form.get("type"), request.files.get("value")

        # Detect delimiter
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(file.stream.readline().decode("utf-8"))
        # reset file pointer
        file.stream.seek(0)

        print("Delimiter: ", dialect.delimiter)

        # Save file first
        file_path = os.path.join("logs", file.filename)
        print("File path: ", file_path)
        file.save(file_path)

        # Change delimiter to ; if it is ,
        if (dialect.delimiter != ";"):
            print("Changing delimiter") 
            with open(file_path, "r") as infile:    
                reader = csv.reader(infile, delimiter=dialect.delimiter) 
                 
                with open(file_path + "delimit", "w") as outfile:
                    writer = csv.writer(outfile, delimiter=';')
                    writer.write
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
    
@app.route("/event-logs/<int:id>", methods=["GET", "PATCH", "DELETE"])
def event_log(id):
    if request.method == "GET":
        event_log = db.get_or_404(EventLog, id)
        # Get file path and send it back
        print("File path: ", event_log.file_path)
        print("Type: ", event_log.type.value)
        df = fetch_dataframe(event_log.file_path, event_log.type.value)

        df_json = df.to_json()

        print("DF JSON: ", df_json)
        
        result = jsonify({
            "id": event_log.id,
            "name": event_log.name,
            "type": event_log.type.value,
            "value": df_json
        })

        print("Result: ", result)

        return result
    elif request.method == "PATCH":
        return "Update event log"
    elif request.method == "DELETE":
        event_log = db.get_or_404(EventLog, id)
        db.session.delete(event_log)

@app.route("/event-logs/<int:id>/columns", methods=["PATCH"])
def event_log_columns(id):
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

@app.route("/event-logs/<int:id>/petri-net/columns", methods=["GET", "POST"])
def event_log_petri_net(id):
    if request.method == "GET":
        event_log = db.get_or_404(EventLog, id)
        df = fetch_dataframe(event_log.file_path, event_log.type.value)
        columns = df.columns.tolist()
        print("Columns: ", columns)
        return jsonify(columns)
    
    if request.method == "POST":
        body = request.json
        data_columns = body.get("columns")
        threshold: float = body.get("threshold")
        print("Data columns: ", data_columns)
        print("Type of data columns: ", type(data_columns))

        event_log = db.get_or_404(EventLog, id)
        base_name, extension = os.path.splitext(event_log.file_path)
        print("Base name: ", base_name)
        print("extension: ", extension)
        file_path = os.path.join(base_name + "_translucent_petri_net" + extension)

        # Save to database first
        translucent_log = TranslucentEventLog(name=event_log.name + "_translucent_petri_net", type=EventLogType.CSV, file_path=file_path, is_ready=False, event_log_id=event_log.id)

        print("created translucent log: ", translucent_log)
        db.session.add(translucent_log)
        db.session.commit()

        df = discover_translucent_log_from_model(event_log.file_path, data_columns, threshold)

        # Save the translucent log to file system
        df.to_csv(file_path, sep=";", index=False)

        print("ID of log: ", translucent_log.id)

        translucent_log = db.get_or_404(TranslucentEventLog, translucent_log.id)

        print("Readiness: ", translucent_log.is_ready)

        # Edit the database entry to mark it as ready
        translucent_log.is_ready = True
        db.session.commit()

        return df.to_json()

@app.route("/event-logs/<int:id>/translucent-logs", methods=["GET"])
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

@app.route("/translucent-event-logs/<int:id>", methods=["Get"])
def translucent_log(id):
    translucent_log = db.get_or_404(TranslucentEventLog, id)
    file_path = translucent_log.file_path
    print("file path: ", file_path)
    
    return send_file(file_path, as_attachment=True)
