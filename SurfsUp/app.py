import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save reference to the table
measurement = Base.classes.measurement
stations = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes for HI Weather:<br/>"
        f"-- Daily Precipitation for 2016-2017 Season: <a href=\"/api/v1.0/precipitation\">/api/v1.0/precipitation<a><br/>"
        f"-- Weather Stations: <a href=\"/api/v1.0/stations\">/api/v1.0/stations<a><br/>"
        f"-- Daily Temperature Observations for Station USC00519281 for 2016-2017 Season: <a href=\"/api/v1.0/tobs\">/api/v1.0/tobs<a><br/>"
        f"-- Enter a start date to get the minimum, maximum, and average temperatures for all dates after the specified date: /api/v1.0/yyyy-mm-dd<br>"
        f"-- Enter both a start and end date to get the minimum, maximum, and average temperatures for that date range: /api/v1.0/yyyy-mm-dd/yyyy-mm-dd<br>"
    )


@app.route("/api/v1.0/precipitation")
def names():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all precipitation"""
    # Convert the query results from your precipitation analysis
    
    prev12_prcp  = session.query(measurement.date, measurement.prcp).\
        filter(measurement.date <= '2017-08-23').\
        filter(measurement.date > '2016-08-23').\
        order_by(measurement.date).all()

    session.close()

    # precip analysis to a dictionary using date as the key and prcp as the value.
    precipitaton_query_values = []
    for prcp, date in prev12_prcp:
        precipitation_dict = {}
        precipitation_dict["precipitation"] = prcp
        precipitation_dict["date"] = date
        precipitaton_query_values.append(precipitation_dict)

    return jsonify(precipitaton_query_values) 
 
@app.route("/api/v1.0/stations")
def station(): 

    session = Session(engine)

    """Return a list of stations from the database""" 
    active_stations = session.query(measurement.station).\
        group_by(measurement.station).all()
    session.close()
    
    stations_list = list(np.ravel(active_stations))
    return jsonify (stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    
    # query: the most active stations last year 
    active_station= session.query(measurement.station, func.count(measurement.station)).\
        order_by(func.count(measurement.station).desc()).\
        group_by(measurement.station).first()
    
    most_active_station = active_station[0] 

    session.close()
    
    #only the most active station: 
    print(most_active_station)
    
    dates_tobs_last_year_query_results = session.query(measurement.date, measurement.tobs, measurement.station).\
        filter(measurement.date > '2016-08-23').\
        filter(measurement.station == most_active_station) 
    
    # Create a list of dates,tobs,and stations that will be appended with dictionary values for date, tobs, and station number queried above
    dates_tobs_last_year_query_values = []
    for date, tobs, station in dates_tobs_last_year_query_results:
        dates_tobs_dict = {}
        dates_tobs_dict["date"] = date
        dates_tobs_dict["tobs"] = tobs
        dates_tobs_dict["station"] = station
        dates_tobs_last_year_query_values.append(dates_tobs_dict)
        
    return jsonify(dates_tobs_last_year_query_values) 

# Dynamic Route

@app.route("/api/v1.0/<start_date>")
# Accepts the start date as a parameter from the URL 
def start_route(start_date):
    # the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range
    session = Session(engine)
    
    query_result = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start_date).all()
    session.close()

    # For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date.
    start_stats = []
    for tmin, tavg, tmax in query_result:
        start_dict = {}
        start_dict["Min"] = tmin
        start_dict["Average"] = tavg
        start_dict["Max"] = tmax
        start_stats.append(start_dict)

    # If the query returned non-null values return the results,
    # otherwise return an error message
    if start_dict['Min']: 
        return jsonify(start_stats)
    else:
        return jsonify({"error": f"Date {start_date} not found or not formatted as YYYY-MM-DD."}), 404
  
@app.route("/api/v1.0/<start_date>/<end_date>")
# Accepts the start & end date as a parameter from the URL 
def start_end_route(start_date, end_date):
    
    # JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range
    session = Session(engine)
    query_result = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start_date).filter(measurement.date <= end_date).all()
    session.close()

    # calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive.
    startend_stats = []
    for Tmin, Tavg, Tmax in query_result:
        startend_dict = {}
        startend_dict["Min"] = Tmin
        startend_dict["Average"] = Tavg
        startend_dict["Max"] = Tmax
        startend_stats.append(startend_dict)

    # If the query returned non-null values return the results,
    # otherwise return an error message
    if startend_dict['Min']: 
        return jsonify(startend_stats)
    else:
        return jsonify({"error": f"Date(s) not found, invalid date range or dates not formatted correctly."}), 404

if __name__ == '__main__':
    app.run(debug=True)