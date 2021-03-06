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
table_polygons = app.config["TABLE_POLYGONS"]
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
    if "properties" in data:
        print(data)
        
        enteredDescription = data["properties"]["description"]
        enteredName = data["properties"]["name"]
        
        geom = data["geometry"]["coordinates"][0]
        wkt_string = "POLYGON(("
        for geo in geom:
            wkt_string+= str(geo[0])
            wkt_string+= " "
            wkt_string+= str(geo[1])
            wkt_string+= ", "
        wkt_string = wkt_string[:-2]
        wkt_string += "))"
        print(wkt_string)
            
        sql_query = "INSERT INTO "+table_polygons+" (the_geom, description, name) VALUES (ST_GeomFromText('"+wkt_string+"', 4326),'"+enteredDescription+"','"+enteredName+"')"
        
    elif "description" in data:
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
    # Get query args
    limit = request.args.get('limit')
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    
    # Basic sql_query for all points
    sql_query = "SELECT * FROM "+table_points
    
    # If optional limit supplied, add second part to query
    if limit:
        sql_add_on = " ORDER BY the_geom <-> ST_SetSRID(ST_MakePoint("+lng+","+lat+"), 4326) LIMIT "+limit
        sql_query += sql_add_on
        
    # Send get all closest points query to CartoDB
    r = requests.get("https://peterdamrosch.cartodb.com/api/v2/sql?format=GeoJSON&q="+sql_query)
    
    # Cehck status code and return either as a success or not
    if r.status_code == 200:
        return Response(json.dumps(r.json()), 200, mimetype="application/json")
    else:
        return Response(json.dumps(r.json()), 400,mimetype="application/json")
        