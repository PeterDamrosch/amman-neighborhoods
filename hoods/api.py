import os
import os.path
import json
import requests

from flask import request, Response, url_for
from jsonschema import validate, ValidationError

from . import decorators
from hoods import app

# Get table name from config - different tables for testing and dev
table_points = app.config["TABLE_POINTS"]
cartodb_key = os.environ["CARTODB_KEY"]

# JSON Schema describing the structure of the POST request data
point_schema = {
    "properties": {
        "coordinates" : {
            "type": "object",
            "properties": {"lat" : {"type": "string"},
                            "lng" : {"type": "string"}
            },
        "required": ["lat","lng"]
        },
        "name": {"type": "string"},
        "description": {"type":"string"}
    },
    "required": ["coordinates","name"]
}

@app.route("/api/geometry", methods=["POST"])
@decorators.require("application/json")
def point_post():
    """ Post a point from client map to CartoDB table """
    data = request.json
    
    # Check that JSON is in right format using the schema, if not return 422
    try:
        validate(data,point_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")
    
    # Get data from request
    coordinates = data["coordinates"]
    enteredDescription = data["description"]
    enteredName = data["name"]
    
    # Compose SQL Query
    sql1="INSERT INTO "+table_points+" (the_geom, description, name) VALUES (ST_SetSRID(ST_GeomFromGeoJSON('"
    sql2='{"type":"Point","coordinates":[' +coordinates['lng'] + "," + coordinates['lat'] + "]}'),4326),'" + enteredDescription +"','" +enteredName +"')"
    sql_query = sql1 + sql2
    
    # Parameters dictionary for requests with query and api key
    params = {"q": sql_query,"api_key": cartodb_key}
    
    # Send insert query to CartoDB
    r = requests.post("https://peterdamrosch.cartodb.com/api/v2/sql",params=params)
    
    # Check that POST was successful, send client success message
    if r.json()['total_rows'] == 1:
        data_response =  {"result": "Feature successfully added to CartoDB"}
        return Response(json.dumps(data_response), 201, mimetype="application/json")

@app.route("/api/geometry", methods=["GET"])
def point_get():
    """ Get points in GeoJSON from CartoDB """

    sqlQueryAll = "SELECT * FROM "+table_points
    
    # Send insert query to CartoDB
    r = requests.get("https://peterdamrosch.cartodb.com/api/v2/sql?format=GeoJSON&q="+sqlQueryAll)
    
    # Check that GET was successful, send relay data to client
    print(r.status_code)
    print(r.json())
    
    if r.status_code == 200:
        return Response(json.dumps(r.json()), 200, mimetype="application/json")
    else:
        return Response(json.dumps(r.json()), 400,mimetype="application/json")
    

    