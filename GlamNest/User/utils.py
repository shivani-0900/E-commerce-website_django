# utils.py
import requests

def get_coordinates_osm(address):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': address,
        'format': 'json'
    }
    response = requests.get(url, params=params, headers={'User-Agent': 'glamnest'})
    data = response.json()

    if data:
        return float(data[0]['lat']), float(data[0]['lon'])
    return None, None