import os
import requests

from pprint import PrettyPrinter
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, send_file
from geopy.geocoders import Nominatim


################################################################################
## SETUP
################################################################################

app = Flask(__name__)

# Get the API key from the '.env' file
load_dotenv()

pp = PrettyPrinter(indent=4)

API_KEY = os.getenv('API_KEY')
API_URL = 'http://api.openweathermap.org/data/2.5/weather'


################################################################################
## ROUTES
################################################################################

@app.route('/')
def home():
    """Displays the homepage with forms for current or historical data."""
    context = {
        'min_date': (datetime.now() - timedelta(days=5)),
        'max_date': datetime.now()
    }
    return render_template('home.html', **context)

def get_letter_for_units(units):
    """Returns a shorthand letter for the given units."""
    return 'F' if units == 'imperial' else 'C' if units == 'metric' else 'K'

@app.route('/results')
def results():
    """Displays results for current weather conditions."""
    # Retrieve the city and units from query parameters
    city = request.args.get('city', '')
    units = request.args.get('units', 'imperial')  # Default to 'imperial'

    # Query parameters for API request
    params = {
        'appid': API_KEY,
        'q': city,
        'units': units
    }

    # API call
    result_json = requests.get(API_URL, params=params).json()

    # Check if the city is valid
    if result_json.get('cod') != 200:
        error_message = f"City '{city}' not found. Please try again."
        return render_template('error.html', error_message=error_message)

    # Extract relevant data from the API response
    context = {
        'date': datetime.now(),
        'city': result_json['name'],
        'description': result_json['weather'][0]['description'].capitalize(),
        'temp': result_json['main']['temp'],
        'humidity': result_json['main']['humidity'],
        'wind_speed': result_json['wind']['speed'],
        'sunrise': datetime.fromtimestamp(result_json['sys']['sunrise']),
        'sunset': datetime.fromtimestamp(result_json['sys']['sunset']),
        'units_letter': get_letter_for_units(units)
    }

    return render_template('results.html', **context)

def fetch_weather_data(city, units):
    """Helper function to fetch weather data for a given city."""
    params = {
        'appid': API_KEY,
        'q': city,
        'units': units
    }
    response = requests.get(API_URL, params=params).json()
    if response.get('cod') != 200:
        return None  # City not found or API error
    return {
        'name': response['name'],
        'temp': response['main']['temp'],
        'humidity': response['main']['humidity'],
        'wind_speed': response['wind']['speed'],
        'sunset': datetime.fromtimestamp(response['sys']['sunset']),
        'description': response['weather'][0]['description'],
        'icon': response['weather'][0]['icon']
    }

@app.route('/comparison_results')
def comparison_results():
    """Displays the relative weather for two different cities."""
    city1 = request.args.get('city1', '')
    city2 = request.args.get('city2', '')
    units = request.args.get('units', 'imperial')

    # Fetch weather data for both cities
    city1_data = fetch_weather_data(city1, units)
    city2_data = fetch_weather_data(city2, units)

    # Handle invalid cities
    if not city1_data or not city2_data:
        error_message = "One or both cities not found. Please try again."
        return render_template('error.html', error_message=error_message)

    # Calculate relative differences
    temp_diff = city1_data['temp'] - city2_data['temp']
    humidity_diff = city1_data['humidity'] - city2_data['humidity']
    wind_speed_diff = city1_data['wind_speed'] - city2_data['wind_speed']
    sunset_diff = (city1_data['sunset'] - city2_data['sunset']).total_seconds() / 3600

    context = {
        'city1_info': city1_data,
        'city2_info': city2_data,
        'temp_diff': temp_diff,
        'humidity_diff': humidity_diff,
        'wind_speed_diff': wind_speed_diff,
        'sunset_diff': sunset_diff,
        'units_letter': get_letter_for_units(units)
    }

    return render_template('comparison_results.html', **context)

if __name__ == '__main__':
    app.config['ENV'] = 'development'
    app.run(debug=True)
