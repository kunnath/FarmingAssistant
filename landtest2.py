import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import random

def fetch_climate_data(lat, lon):
    """Fetch climate and sunlight data using OpenWeather API."""
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

def predict_agriculture_suitability(climate_data, month):
    """Determine if the location is suitable for agriculture based on climate and month."""
    if climate_data:
        temp = climate_data["temperature"]
        humidity = climate_data["humidity"]
        sunlight = climate_data["sunlight_hours"]

        # Adjust predictions based on the month
        if month in [12, 1, 2]:  # Winter months
            suitability = "Not Good"
            message = "Winter conditions may cause frost. Crops like Wheat may survive but others may struggle."
        elif month in [3, 4, 5]:  # Spring months
            if 10 <= temp <= 25 and 40 <= humidity <= 80 and sunlight >= 8:
                suitability = "Good"
                message = "Spring is a good time for crops like Corn, Rice, or Vegetables."
            else:
                suitability = "Not Good"
                message = "Spring conditions are not optimal for agriculture. Consider irrigation or greenhouse farming."
        elif month in [6, 7, 8]:  # Summer months
            if 20 <= temp <= 35 and 40 <= humidity <= 70 and sunlight >= 8:
                suitability = "Good"
                message = "Summer is ideal for crops like Corn and Rice, but ensure proper water management."
            else:
                suitability = "Not Good"
                message = "Summer conditions may lead to drought or high temperatures. Crops may need irrigation."
        else:  # Fall months
            if 10 <= temp <= 20 and 50 <= humidity <= 80 and sunlight >= 6:
                suitability = "Good"
                message = "Fall is good for crops like Wheat and Barley."
            else:
                suitability = "Not Good"
                message = "Fall conditions are suboptimal for some crops. Moisture levels may be low."

        return suitability, message
    return "Unknown", "Could not fetch data. Please try again."

def main():
    st.title("🌱 Agriculture Suitability Predictor")
    st.write("Enter a Google Map location (latitude & longitude) and the month to check if it's suitable for farming.")
    
    lat = st.number_input("Enter Latitude", value=52.52, format="%.6f")
    lon = st.number_input("Enter Longitude", value=13.405, format="%.6f")
    month = st.selectbox("Select the Month", options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

    if st.button("Predict Suitability"):
        climate_data = fetch_climate_data(lat, lon)
        status, message = predict_agriculture_suitability(climate_data, month)
        
        st.subheader(f"Prediction: {status}")
        st.write(message)
        
        # Show map with marker
        m = folium.Map(location=[lat, lon], zoom_start=10)
        folium.Marker([lat, lon], popup=f"Prediction: {status}").add_to(m)
        folium_static(m)

if __name__ == "__main__":
    main()