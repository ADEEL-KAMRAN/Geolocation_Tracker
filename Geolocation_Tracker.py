import requests
import folium
import webbrowser
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

# Cache to store geolocation data to avoid repeated API calls
geo_cache = {}

def setup_session():
    """Set up a requests session with retry logic for better reliability."""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def get_ip_geolocation(ip_address=None, session=None):
    """Fetches the geolocation details of an IP address with caching."""
    # === API KEY BLOCK START ===
    # API key for ipinfo.io
    API_KEY = "20020022f148d7"  # Inserted API key as provided
    # === API KEY BLOCK END ===

    # Use the provided IP or fetch the user's IP
    url = f"https://ipinfo.io/{ip_address}/json" if ip_address else "https://ipinfo.io/json"
    
    # Add the API key to the request as a query parameter
    params = {"token": API_KEY} if API_KEY else {}

    # Check cache first
    cache_key = url + str(params)  # Include params in cache key to differentiate requests
    if cache_key in geo_cache:
        print("Using cached data...")
        return geo_cache[cache_key]
    
    try:
        response = session.get(url, params=params, timeout=5)
        response.raise_for_status()
        geo_data = response.json()
        geo_cache[cache_key] = geo_data  # Cache the result
        return geo_data
    except requests.exceptions.Timeout:
        print("Error: Request timed out. Please check your connection.")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error: {req_err}")
    return None

def create_map(latitude, longitude, zoom_level=10, marker_color="blue", details=None):
    """Creates an interactive map with customizable options."""
    try:
        map_filename = "geolocation_map.html"
        map_object = folium.Map(location=[latitude, longitude], zoom_start=zoom_level)
        
        # Create a detailed popup if additional details are provided
        popup_text = "Location"
        if details:
            popup_text = f"""
            <b>Location Details</b><br>
            IP: {details.get('ip', 'N/A')}<br>
            City: {details.get('city', 'N/A')}<br>
            Region: {details.get('region', 'N/A')}<br>
            Country: {details.get('country', 'N/A')}<br>
            Coordinates: {latitude}, {longitude}
            """
        
        folium.Marker(
            [latitude, longitude],
            popup=popup_text,
            icon=folium.Icon(color=marker_color)
        ).add_to(map_object)
        
        map_object.save(map_filename)
        webbrowser.open(map_filename)
        print(f"Map has been saved and opened: {map_filename}")
    except Exception as e:
        print(f"Error creating the map: {e}")

def save_to_file(geo_data, filename="geolocation_data.json"):
    """Saves geolocation data to a file."""
    try:
        with open(filename, "a") as f:
            json.dump(geo_data, f, indent=4)
            f.write("\n")
        print(f"Geolocation data saved to {filename}")
    except Exception as e:
        print(f"Error saving data to file: {e}")

def display_details(geo_data):
    """Displays detailed geolocation information."""
    if not geo_data:
        print("No geolocation data to display.")
        return
    
    print("\n=== Geolocation Details ===")
    print(f"IP: {geo_data.get('ip', 'N/A')}")
    print(f"City: {geo_data.get('city', 'N/A')}")
    print(f"Region: {geo_data.get('region', 'N/A')}")
    print(f"Country: {geo_data.get('country', 'N/A')}")
    print(f"Organization: {geo_data.get('org', 'N/A')}")
    print(f"Timezone: {geo_data.get('timezone', 'N/A')}")
    loc = geo_data.get("loc", "N/A")
    print(f"Coordinates: {loc}")

def get_valid_input(prompt, valid_options=None, type_cast=int):
    """Gets valid user input with error handling."""
    while True:
        try:
            value = type_cast(input(prompt).strip())
            if valid_options and value not in valid_options:
                print(f"Please choose from: {valid_options}")
                continue
            return value
        except ValueError:
            print(f"Invalid input! Please enter a valid {'number' if type_cast == int else 'value'}.")

def display_menu():
    """Displays the main menu."""
    print("\n=== IP Geolocation Tracker ===")
    print("1. Geolocate my IP")
    print("2. Geolocate a specific IP")
    print("3. View last geolocation details")
    print("4. Save last geolocation to file")
    print("5. Create map with custom options")
    print("6. Exit")
    return get_valid_input("Choose an option (1-6): ", valid_options=[1, 2, 3, 4, 5, 6])

def main():
    """Main function to run the geolocation tracker."""
    session = setup_session()
    last_geo_data = None  # Store the last fetched geolocation data
    
    while True:
        choice = display_menu()
        
        if choice == 1:
            # Geolocate user's IP
            print("\nFetching geolocation for your IP...")
            geo_data = get_ip_geolocation(session=session)
            if geo_data:
                last_geo_data = geo_data
                display_details(geo_data)
        
        elif choice == 2:
            # Geolocate a specific IP
            ip_address = input("\nEnter IP address to geolocate: ").strip()
            print(f"Fetching geolocation for IP: {ip_address}...")
            geo_data = get_ip_geolocation(ip_address, session=session)
            if geo_data:
                last_geo_data = geo_data
                display_details(geo_data)
        
        elif choice == 3:
            # View last geolocation details
            if last_geo_data:
                display_details(last_geo_data)
            else:
                print("\nNo geolocation data available. Fetch data first.")
        
        elif choice == 4:
            # Save last geolocation to file
            if last_geo_data:
                save_to_file(last_geo_data)
            else:
                print("\nNo geolocation data to save. Fetch data first.")
        
        elif choice == 5:
            # Create map with custom options
            if not last_geo_data:
                print("\nNo geolocation data available. Fetch data first.")
                continue
            
            try:
                loc = last_geo_data.get("loc", "").split(",")
                if len(loc) != 2:
                    print("Error: Could not extract location data.")
                    continue
                lat, lon = float(loc[0]), float(loc[1])
                
                # Get custom options from user
                zoom_level = get_valid_input("Enter zoom level (1-18, default 10): ", type_cast=int)
                if not 1 <= zoom_level <= 18:
                    zoom_level = 10
                    print("Zoom level out of range. Using default (10).")
                
                print("\nAvailable marker colors: red, blue, green, purple, orange")
                marker_color = input("Enter marker color (default blue): ").strip().lower()
                if marker_color not in ["red", "blue", "green", "purple", "orange"]:
                    marker_color = "blue"
                    print("Invalid color. Using default (blue).")
                
                create_map(lat, lon, zoom_level=zoom_level, marker_color=marker_color, details=last_geo_data)
            except ValueError:
                print("Error: Invalid location data format.")
        
        elif choice == 6:
            print("\nExiting IP Geolocation Tracker. Goodbye!")
            break

if __name__ == "__main__":
    main()