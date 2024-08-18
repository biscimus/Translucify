from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import sqlalchemy as sql
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase
import enum
import os
from flask import request, jsonify
from flask_alembic import Alembic

from algorithms.preprocessor import fetch_dataframe

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

class EventLogType(enum.Enum):
    CSV = "csv"
    XES = "xes"

class ProcessModelType(enum.Enum):
    PETRINET = "petrinet"
    PREFIX_AUTOMATON = "prefix_automaton"

class EventLog(Base):
    __tablename__ = "log"
    id: Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(sql.String(255))
    type: Mapped[EventLogType] = mapped_column(sql.Enum(EventLogType))
    file_path: Mapped[str] = mapped_column(sql.String)

class ProcessModel(Base):
    __tablename__ = "process_model"
    id: Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(sql.String(255))
    type: Mapped[ProcessModelType] = mapped_column(sql.Enum(ProcessModelType))
    value: Mapped[str] = mapped_column(sql.String)


# Database
db = SQLAlchemy(model_class=Base)
db.init_app(app)

with app.app_context():
    db.create_all()


# Routes

@app.route("/process-models", methods=["GET", "POST"])
def process_models():
    if request.method == "GET":
        rows = db.session.execute(db.select(ProcessModel)).scalars().all()
        return jsonify(rows)
        print("Rows: ", rows)
    elif request.method == "POST":
        return "Create a new process model"

@app.route("/process-models/<int:id>", methods=["DELETE"])
def process_model(id):
    process_model = db.get_or_404(ProcessModel, id)
    db.session.delete(process_model)

    
@app.route("/event-logs", methods=["GET", "POST"])
def event_logs():
    if request.method == "GET":
        logs = db.session.execute(db.select(EventLog)).scalars().all()
        print("Logs: ", logs)
        for log in logs:
            print("Log: ", log)
            print("Log ID: ", log.id)
        
        # Convert to list of dictionaires for json

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
        
        name, type = request.form.get("name"), request.form.get("type")
        print("Name: ", name, "Type: ", type)
        
        file = request.files.get("value")
        file_path = os.path.join("logs", file.filename)
        file.save(file_path)

        # Save file as database entry
        event_log = EventLog(name=name, type=type, file_path=file.filename)

        db.session.add(event_log)
        db.session.commit()

        return "Event log posted!"
    
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
