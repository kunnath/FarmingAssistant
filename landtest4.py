import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import random
import ollama  # Using local Ollama for AI processing
import firebase_admin
from firebase_admin import credentials, db
from twilio.rest import Client
import googlemaps
from firebase_admin import credentials, firestore

# ---- Configuration ----
GOOGLE_MAPS_API_KEY = "AIzaSyA2b5SMduPgTlj_TSatxZ_tyZB5p-T1CIw"
TWILIO_ACCOUNT_SID = "ACfa077e3b32a800afee1da427ae1286fe"
TWILIO_AUTH_TOKEN = "cf3fb1e62229cfcbec3112231728fbb4"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
API_KEY = "b13d5fdb-c215-4949-9d45-4271eb66b9eb"
# ---- Google Maps API Key ----
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# ---- Twilio WhatsApp Config ----
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("./crop-d0953-firebase-adminsdk-fbsvc-12d916884c.json")
    firebase_admin.initialize_app(cred, {"databaseURL": "https://your-database.firebaseio.com"})

# ---- Function: Contact Expert via WhatsApp ----
def contact_expert(message):
    twilio_client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_NUMBER,
        to="whatsapp:+USER_PHONE_NUMBER"
    )
    return "Message sent to agricultural expert."

# ---- Function: Save Deal in Firebase ----
def save_deal(crop, retailer, price, status):
    deal_data = {"crop": crop, "retailer": retailer, "price": price, "status": status}
    db.collection("deals").add(deal_data)
    return "Deal saved successfully."

# ---- Functions ----

def get_crop_price(crop_symbol, country=None):
    """Fetch real-time crop price from CommodityPriceAPI, optionally filtering by country."""
    url = "https://api.commoditypriceapi.com/v2/rates/latest"
    headers = {"x-api-key": API_KEY}
    params = {"symbols": crop_symbol}  # Example: 'wheat', 'corn', 'soybeans'

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        rates = data.get("rates", {})

        # If country filtering is needed, this logic must be adapted based on the API's response structure
        if country:
            country_specific_key = f"{crop_symbol}_{country.upper()}"  # Some APIs use country codes
            return rates.get(country_specific_key, {}).get("rate", f"Price not available for {country}")
        
        return rates.get(crop_symbol, {}).get("rate", "Price not available")
    
    else:
        return f"Failed to fetch price: {response.status_code}"
    

# ---- Function: AI-Based Crop Pricing ----
def get_crop_price_g(crop):
    price_prompt = f"""
    Fetch the latest global price trends for {crop}.
    Include:
    - Price per ton (current & historical)
    - Seasonal price changes
    - Best markets for selling based on pricing trends
    """
    
    response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": price_prompt}])
    return response["message"]["content"]

def send_whatsapp_message_user_number(user_number, message):
    """Send WhatsApp message via Twilio."""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        client.messages.create(from_=TWILIO_WHATSAPP_NUMBER, body=message, to=f"whatsapp:{user_number}")
        return "Message sent successfully!"
    except Exception as e:
        return f"Error: {e}"


def send_whatsapp_message(user_number, message):
    """Send a WhatsApp message via Twilio."""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    try:
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=f"whatsapp:{user_number}"
        )
        return f"Message sent successfully! Message SID: {message.sid}"
    except Exception as e:
        return f"Error: {e}"



# ---- Function: Fetch Retailers Near ZIP Code ----
def get_retailers(zip_code):
    places_result = gmaps.places(query=f"retailers near {zip_code}")
    return [{"name": p["name"], "address": p["formatted_address"]} for p in places_result.get("results", [])]

# ---- Function: AI-Based Market Analysis ----
def ai_market_analysis(crop, month):
    market_prompt = f"""
    Predict the global market demand for the crop {crop} in the month of {month}.
    Provide insights on:
    - Top countries or regions with high demand
    - Price trends and seasonal factors
    - Potential challenges and market fluctuations
    - Recommended global markets for selling
    """
    
    response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": market_prompt}])
    return response["message"]["content"]

def fetch_retailers(zip_code):
    """Fetch retailers using Google Places API."""
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=retailers+in+{zip_code}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    return response.json().get("results", []) if response.status_code == 200 else []

def store_proposal(crop, retailer, status="Pending"):
    """Store a crop deal proposal in Firebase."""
    ref = db.reference("deals")
    ref.push({"crop": crop, "retailer": retailer, "status": status})

def get_deals():
    """Retrieve deals from Firebase."""
    ref = db.reference("deals")
    return ref.get() or {}


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

# Function to calculate transportation cost
def calculate_transportation_cost(distance, vehicle_type, crop_weight, budget):
    # Example: Basic calculation, assuming distance and vehicle type affect the cost.
    if vehicle_type == "Truck":
        cost_per_km = 0.5  # Cost per kilometer for trucks
    elif vehicle_type == "Container":
        cost_per_km = 1.0  # Cost per kilometer for containers
    else:
        cost_per_km = 0.8  # Default cost for other vehicles

    # Basic cost calculation
    transportation_cost = distance * cost_per_km * (crop_weight / 1000)  # Weight in tons for simplicity
    within_budget = transportation_cost <= budget

    return transportation_cost, within_budget



# Main Streamlit interface
def main():
    # Title for the app
    st.title("🌱 AI Assistant for Personalized Farming Guidance and Market Trends")

    # User selects what they want: Farming Suitability or Market Trends
    option = st.radio("Select Assistant Mode", ("AI Assistant for Farming Suitability", "AI Assistant for Crop Market Trends","Crop Export Assistant","Ai bot Assistant"))
    
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
            #climate_data = fetch_climate_data(lat, lon)
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
    elif option == "Crop Export Assistant":
                
        st.title("🌍 Crop Export Assistant")

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

        # Step 6: Transportation to the Export Destination
        st.title("🚛 Transportation Details")

        # Transportation Inputs
        distance = st.number_input("Enter the distance from the field to the export destination (km)", value=100)
        vehicle_type = st.selectbox("Select the type of vehicle for transportation", ["Truck", "Container", "Other"])
        transportation_budget = st.number_input("Enter your transportation budget (in USD)", value=2000)

        # Calculate transportation cost and check budget
        transportation_cost, within_budget = calculate_transportation_cost(distance, vehicle_type, weight, transportation_budget)

        st.subheader("🚚 Transportation Cost Estimate")
        st.write(f"Estimated transportation cost: ${transportation_cost:.2f}")

        if within_budget:
            st.success("The transportation cost is within your budget!")
        else:
            st.error("The transportation cost exceeds your budget. Please adjust your budget or logistics.")

    elif option == "Ai bot Assistant":   
       
            # ---- Streamlit UI ----
        st.title("🌍 AI Assistant for Crop Market")

        # ---- Crop Pricing ----
        st.subheader("💰 Get Real-Time Crop Prices")
        crop_name = st.text_input("Enter Crop Name", value="Wheat")
        country_name = st.text_input("Enter Country", value="Germany")

        if st.button("Check Price"):
            price = get_crop_price(crop_name, country_name)
            st.write(f"💲 Current price of {crop_name} in {country_name}: **{price} per ton**")

        # ---- Chat with Experts ----
        st.subheader("📲 Chat with Experts via WhatsApp")
        user_number = st.text_input("Enter Your WhatsApp Number", value="+4917632815898")
        user_message = st.text_area("Enter your message")

        if st.button("Send Message"):
            response = send_whatsapp_message(user_number, user_message)
            st.success(response)

        # ---- Find Retailers ----
        st.subheader("🛒 Find Retailers Near You")
        zip_code = st.text_input("Enter ZIP Code or City")

        if st.button("Search Retailers"):
            retailers = fetch_retailers(zip_code)
            if retailers:
                for r in retailers:
                    st.write(f"🏪 **{r['name']}** - {r['formatted_address']}")
            else:
                st.warning("No retailers found.")

        # ---- Submit Deal Proposal ----
        st.subheader("📑 Send Proposal to Retailers")
        selected_retailer = st.text_input("Enter Retailer Name")
        if st.button("Send Proposal"):
            store_proposal(crop_name, selected_retailer)
            st.success("Proposal sent successfully!")

        # ---- Deal Tracking ----
        st.subheader("📊 Track Your Deals")
        if st.button("View Deals"):
            deals = get_deals()
            if deals:
                for key, deal in deals.items():
                    st.write(f"🌱 Crop: **{deal['crop']}** | 🛒 Retailer: **{deal['retailer']}** | 📊 Status: **{deal['status']}**")
            else:
                st.write("No active deals found.")
                
        st.subheader("📜 Track Your Deals")
        retailer_name = st.text_input("Retailer Name")
        crop_price = st.number_input("Enter Crop Price", min_value=0.0)
        deal_status = st.selectbox("Deal Status", ["Pending", "Accepted", "Rejected"])
        

        if st.button("Save Deal"):
            db.collection("deals").add({"crop": crop_name, "retailer": retailer_name, "price": crop_price, "status": deal_status})
            st.success("Deal saved successfully.")
    

        # ---- Map Visualization ----
        st.subheader("🗺️ Retailer Locations")
        map_center = [52.52, 13.405]  # Default: Berlin
        m = folium.Map(location=map_center, zoom_start=10)
        folium_static(m)   

                # ---- AI Market Insights ----
        st.subheader("📊 AI Market Analysis for Your Crop")
        use_ai = st.checkbox("Use AI for Market Trends")

        if use_ai:
            crop_for_ai = st.text_input("Enter Crop Name", value="Wheat", key="crop_ai")
            month_for_ai = st.selectbox("Select the Month", options=list(range(1, 13)), key="month_ai")

            if st.button("Get AI Market Insights"):
                ai_market_data = ai_assistant_for_crop_market(crop_for_ai, month_for_ai)
                st.subheader(f"🌍 AI Market Insights for {crop_for_ai}")
                st.write(ai_market_data)

if __name__ == "__main__":
    main()