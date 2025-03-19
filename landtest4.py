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

def generate_farming_steps(crop_name):
    """Generate farming steps for a specific crop using AI."""
    prompt = f"""
    Provide a detailed farming guide for growing {crop_name}. Include:
    1. Soil Preparation
    2. Planting Method
    3. Watering and Nutrient Requirements
    4. Pest and Disease Control
    5. Harvesting Process
    """
    
    try:
        response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": prompt}])
        if response and "message" in response:
            return response["message"]["content"]
    except Exception as e:
        st.error(f"Error generating farming guide for {crop_name}: {e}")
    
    return "Farming guide unavailable."

def extract_crops_from_text(text):
    """Extract crop names from AI response (basic method)."""
    lines = text.split("\n")
    crops = []
    for line in lines:
        if ":" in line:  # Example: "Winter Melon: A high-yield crop..."
            crop = line.split(":")[0].strip()
            crops.append(crop)
    return crops

# Function to predict global market trends for a crop
def ai_assistant_for_crop_market(crop, month):
    """AI Assistant for predicting global market trends for a given crop."""
    market_prompt = f"""
    Predict the global market demand for the crop {crop} in the month of {month}.
    Provide insights on:
    - The top countries or regions that have high demand for {crop}
    - Price trends and seasonal factors
    - Any upcoming market fluctuations or potential challenges for growers
    - Recommended markets for selling the crop globally
    """
    
    response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": market_prompt}])
    
    if response:
        return response["message"]["content"]
    return "Market trend data unavailable."


def main():
    st.title("🌱 Agriculture Suitability & Farming Guide")
    st.write("Enter a location (latitude & longitude) and month to check agricultural suitability.")

    lat = st.number_input("Enter Latitude", value=52.52, format="%.6f", key="latm")
    lon = st.number_input("Enter Longitude", value=13.405, format="%.6f", key="lonm")
    month = st.selectbox("Select the Month", options=list(range(1, 13)), key="monthm")

    if st.button("Predict Suitability"):
        climate_data = fetch_climate_data(lat, lon)
        soil_data = fetch_soil_data(lat, lon)
        
        if soil_data:
            st.subheader("🌍 Soil Data Analysis")
            st.write(soil_data)

        status, message = predict_agriculture_suitability(climate_data, soil_data, month)

        st.subheader(f"Prediction: {status}")
        st.write(message)

        # Extract best crops
        crops = extract_crops_from_text(message)

        if crops:
            st.subheader("🌾 Best Crops to Grow in This Area")
            for crop in crops:
                st.markdown(f"✅ **{crop}**")

            # Generate and display farming steps
            st.subheader("📜 Farming Guide")
            for crop in crops:
                st.write(f"### {crop}")
                farming_guide = generate_farming_steps(crop)
                st.write(farming_guide)

        # Show map with marker
        m = folium.Map(location=[lat, lon], zoom_start=10)
        folium.Marker([lat, lon], popup=f"Prediction: {status}").add_to(m)
        folium_static(m)
        
# def fetch_climate_data(lat, lon):
#     """Fetch climate and sunlight data using OpenWeather API."""
#     OPENWEATHER_API_KEY = "d315bc077639441a5e59443eed999c9c"  # Replace with valid key
#     url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
#     response = requests.get(url)
    
#     if response.status_code == 200:
#         data = response.json()
#         return {
#             "temperature": data["main"]["temp"],
#             "humidity": data["main"]["humidity"],
#             "sunlight_hours": random.randint(6, 12)  # Placeholder for sunlight data
#         }
#     return None

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
    
    response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": prompt}])
    
    if response:
        return response["message"]["content"]  # Extract soil data
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
        
        response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": analysis_prompt}])
        
        if response:
            return "Analysis Complete", response["message"]["content"]
    
    return "Unknown", "Could not fetch data. Please try again."

def predict_market_for_crop(crop, month):
    """Predict the market demand for a given crop based on current trends."""
    # Example: A simulated response from an AI model or data source
    prompt = f"""
    Predict the market trends for the crop {crop} in the month of {month}.
    Suggest the possible markets where this crop is in high demand during that month and any other relevant market trends.
    """
    
    response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": prompt}])
    
    if response:
        return response["message"]["content"]
    return "Market data unavailable."



# Export Process Steps
export_steps = [
    "Step 1: Crop Selection - Select the crop you want to export.",
    "Step 2: Destination Country - Enter the country you want to export to.",
    "Step 3: Export Documentation - Prepare necessary export documents.",
    "Step 4: Government Certification - Obtain necessary export permits and certifications from the government.",
    "Step 5: Export Registration - Register with relevant authorities in the country of origin.",
    "Step 6: Export Approval - Wait for approval and clearance to export the crop.",
    "Step 7: Shipment - Prepare the shipment and ensure compliance with international standards.",
    "Step 8: Delivery & Tracking - Finalize shipment and track the cargo."
]

# Function to generate export documentation
def generate_export_documentation(crop, country, shipment_details):
    documentation = f"""
    Export Documentation for Crop: {crop}
    Destination Country: {country}

    1. Export Certificate: A certificate issued by the relevant agriculture authority in the home country.
    2. Phytosanitary Certificate: Ensures the crop is free of pests and diseases.
    3. Invoice and Packing List: Detailed list of crops and shipment information.
    4. Export Permit: Government-issued permit for exporting crops to {country}.
    5. Health Certification: Certification ensuring the crop is safe for consumption.
    6. Certificate of Origin: Confirming the origin of the crop.
    
    Shipment Details:
    - Weight: {shipment_details['weight']}
    - Volume: {shipment_details['volume']}
    - Packaging Type: {shipment_details['packaging_type']}
    
    The documentation will be verified by the authorities before the export is approved.
    """

    return documentation

# Function to simulate obtaining government approval
def obtain_government_approval(crop, country):
    approval = f"""
    Government Approval Process for Exporting {crop} to {country}:
    
    1. Application Submission: Submit the necessary forms and documentation to the export authority.
    2. Documentation Verification: Authorities will verify the authenticity of the submitted documents.
    3. Approval Issuance: Once verified, the export permit and phytosanitary certificate will be issued.
    4. Customs Clearance: Final approval for export from customs authorities.
    """

    return approval


# Main Streamlit interface
def main():
    # Title for the app
    st.title("🌱 AI Assistant for Personalized Farming Guidance and Market Trends")

    # User selects what they want: Farming Suitability or Market Trends
    option = st.radio("Select Assistant Mode", ("AI Assistant for Farming Suitability", "AI Assistant for Crop Market Trends"))
    
    # Common inputs: Location (Latitude & Longitude), Month, and Crop (if applicable)
    lat = st.number_input("Enter Latitude", value=52.52, format="%.6f", key="lat")
    lon = st.number_input("Enter Longitude", value=13.405, format="%.6f", key="lon")
    month = st.selectbox("Select the Month", options=list(range(1, 13)), key="month")
    
    # Show different sections based on the option selected
    if option == "AI Assistant for Farming Suitability":
        st.write("Enter a crop and month to check farming suitability.")

        crop = st.text_input("Enter Crop Name", value="Wheat", key="crop")

        if st.button("Predict Suitability"):
            # Fetch Climate and Soil Data
            climate_data = fetch_climate_data(lat, lon)
            soil_data = fetch_soil_data(lat, lon)

            if soil_data:
                st.subheader("🌍 Soil Data Analysis")
                st.write(soil_data)

            # Generate and display farming steps
            st.subheader("📜 Farming Guide")
            farming_guide = generate_farming_steps(crop)
            st.write(farming_guide)

            # Show map with marker
            m = folium.Map(location=[lat, lon], zoom_start=10)
            folium.Marker([lat, lon], popup=f"Farming Guide for {crop}").add_to(m)
            folium_static(m)

    elif option == "AI Assistant for Crop Market Trends":
        st.write("Enter a crop and month to predict global market demand.")

        crop = st.text_input("Enter Crop Name", value="Wheat", key="crop")

        if st.button("Predict Suitability & Market Trends"):
            # Fetch Climate and Soil Data (if needed, for better predictions)
            climate_data = fetch_climate_data(lat, lon)
            #soil_data = fetch_soil_data(lat, lon)
            
            # if soil_data:
            #     st.subheader("🌍 Soil Data Analysis")
            #     st.write(soil_data)

            # Market Demand Prediction using AI Assistant
            market_trends = ai_assistant_for_crop_market(crop, month)
            st.subheader(f"📈 Market Demand for {crop} in Month {month}")
            st.write(market_trends)

            # Show map with marker
            m = folium.Map(location=[lat, lon], zoom_start=10)
            folium.Marker([lat, lon], popup=f"Market Trends for {crop}").add_to(m)
            folium_static(m)
            
    st.title("🌍 AI Crop Export Assistant")

    # Step 1: Crop Selection
    crop = st.selectbox("Select the Crop to Export", ["Wheat", "Rice", "Corn", "Soybeans", "Cotton", "Other"])
    
    # Step 2: Destination Country
    country = st.text_input("Enter the Destination Country", value="Germany")
    
    # Step 3: Export Documentation
    st.subheader("📑 Export Documentation Preparation")
    weight = st.number_input("Enter the weight of the crop (kg)", value=1000)
    volume = st.number_input("Enter the volume of the crop (m³)", value=10)
    packaging_type = st.selectbox("Select the packaging type", ["Bagged", "Crated", "Loose", "Other"])

    # Step 4: Government Certification
    st.subheader("📜 Government Certification")
    certificate_requested = st.checkbox("I have all the necessary documents and certifications")
    
    if st.button("Generate Export Documentation & Government Approval"):
        if certificate_requested:
            shipment_details = {
                'weight': weight,
                'volume': volume,
                'packaging_type': packaging_type
            }
            
            # Generate Export Documentation
            documentation = generate_export_documentation(crop, country, shipment_details)
            st.subheader("📑 Export Documentation")
            st.write(documentation)

            # Generate Government Approval Process
            approval = obtain_government_approval(crop, country)
            st.subheader("📜 Government Approval Process")
            st.write(approval)

            # Step 5: Provide confirmation message
            st.success("Export process initiated successfully. Please follow the steps above to complete the process.")
        
        else:
            st.error("Please ensure you have all the necessary documents and certifications before proceeding.")

    # Additional information: Track Shipment and Export Status
    st.subheader("🚚 Shipment Tracking")
    tracking_number = st.text_input("Enter the shipment tracking number", value="")
    
    if tracking_number:
        st.write(f"Tracking shipment with number: {tracking_number}")
        # Simulate shipment tracking details
        st.write(f"Tracking status: In Transit to {country}")
        st.write("Estimated delivery time: 5-7 days.")
    else:
        st.write("Please enter a valid shipment tracking number.")

if __name__ == "__main__":
    main()