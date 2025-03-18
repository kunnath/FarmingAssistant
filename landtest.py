import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import random

def fetch_climate_data(lat, lon):
    """Fetch climate and sunlight data using OpenWeather API (Example)."""
    api_key = "d315bc077639441a5e59443eed999c9c"  # Replace with a valid API key
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "sunlight_hours": random.randint(6, 12)  # Placeholder for sunlight data
        }
    return None

def predict_agriculture_suitability(climate_data):
    """Basic logic to determine if the location is suitable for agriculture."""
    if climate_data:
        temp = climate_data["temperature"]
        humidity = climate_data["humidity"]
        sunlight = climate_data["sunlight_hours"]
        
        if 10 <= temp <= 35 and 40 <= humidity <= 80 and sunlight >= 6:
            return "Good", "This location is suitable for agriculture. Suggested crops: Wheat, Corn, Rice."
        else:
            return "Not Good", "The climate conditions may not be ideal for agriculture. Consider irrigation or greenhouse farming."
    return "Unknown", "Could not fetch data. Please try again."

def main():
    st.title("🌱 Agriculture Suitability Predictor")
    st.write("Enter a Google Map location (latitude & longitude) to check if it's suitable for farming.")
    
    lat = st.number_input("Enter Latitude", value=52.52, format="%.6f")
    lon = st.number_input("Enter Longitude", value=13.405, format="%.6f")
    
    if st.button("Predict Suitability"):
        climate_data = fetch_climate_data(lat, lon)
        status, message = predict_agriculture_suitability(climate_data)
        
        st.subheader(f"Prediction: {status}")
        st.write(message)
        
        # Show map with marker
        m = folium.Map(location=[lat, lon], zoom_start=10)
        folium.Marker([lat, lon], popup=f"Prediction: {status}").add_to(m)
        folium_static(m)

if __name__ == "__main__":
    main()
