import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import random
import ollama  # Using local Ollama for AI processing

def fetch_climate_data(lat, lon):
    """Fetch climate and sunlight data using OpenWeather API."""
    OPENWEATHER_API_KEY = "d315bc077639441a5e59443eed999c9c"  # Replace with a valid key
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        
        data = response.json()
        return {
            "temperature": data["main"].get("temp", 25),  # Default 25°C if missing
            "humidity": data["main"].get("humidity", 50),  # Default 50%
            "sunlight_hours": random.randint(6, 12)  # Placeholder for sunlight data
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching climate data: {e}")
        return None

def fetch_soil_data(lat, lon):
    """Fetch soil quality data using local Ollama model."""
    prompt = f"""
    Analyze soil conditions for agriculture at the location:
    - Latitude: {lat}
    - Longitude: {lon}
    
    Provide details on:
    - Soil fertility
    - Moisture levels
    - pH value
    - Organic matter
    - Any potential issues for farming.
    """
    
    try:
        response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": prompt}])
        if response and "message" in response:
            return response["message"]["content"]  # Extract soil data
    except Exception as e:
        st.error(f"Error fetching soil data: {e}")
    
    return "Soil data unavailable."

def predict_agriculture_suitability(climate_data, soil_data, month):
    """Determine if the location is suitable for agriculture based on climate, soil, and month."""
    if climate_data and soil_data:
        temp = climate_data["temperature"]
        humidity = climate_data["humidity"]
        sunlight = climate_data["sunlight_hours"]

        # Ask DeepSeek R1 to analyze and refine the prediction
        analysis_prompt = f"""
        Given the climate data:
        - Temperature: {temp}°C
        - Humidity: {humidity}%
        - Sunlight: {sunlight} hours/day

        And the soil data:
        {soil_data}

        For the month of {month}, analyze if this location is good for agriculture.
        Suggest the best crops to grow and any necessary improvements.
        """
        
        try:
            response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": analysis_prompt}])
            if response and "message" in response:
                return "Analysis Complete", response["message"]["content"]
        except Exception as e:
            st.error(f"Error analyzing agriculture suitability: {e}")
    
    return "Unknown", "Could not fetch data. Please try again."

def main():
    st.title("🌱 Agriculture Suitability Predictor (Local AI)")
    st.write("Enter a location (latitude & longitude) and month to check agricultural suitability.")

    lat = st.number_input("Enter Latitude", value=52.52, format="%.6f")
    lon = st.number_input("Enter Longitude", value=13.405, format="%.6f")
    month = st.selectbox("Select the Month", options=list(range(1, 13)))

    if st.button("Predict Suitability"):
        climate_data = fetch_climate_data(lat, lon)
        soil_data = fetch_soil_data(lat, lon)
        
        if soil_data:
            st.subheader("🌍 Soil Data Analysis")
            st.write(soil_data)

        status, message = predict_agriculture_suitability(climate_data, soil_data, month)

        st.subheader(f"Prediction: {status}")
        st.write(message)

        # Show map with marker
        m = folium.Map(location=[lat, lon], zoom_start=10)
        folium.Marker([lat, lon], popup=f"Prediction: {status}").add_to(m)
        folium_static(m)

if __name__ == "__main__":
    main()
    
    
