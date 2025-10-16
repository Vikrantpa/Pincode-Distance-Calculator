# 1️⃣ Imports
import streamlit as st
import math
import pandas as pd
from pymongo import MongoClient
from shapely.geometry import shape

# 2️⃣ Haversine distance function
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth's radius (km)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 3️⃣ Function to load pincode data from MongoDB
def load_pincode_data():
    """
    Load all pincodes with geometry and metadata from MongoDB.
    Returns a dict: key = pincode (int), value = dict with centroid and details
    """
    client = MongoClient("mongodb://localhost:27017")  # change if needed
    db = client.vikrant_db
    coll = db.pincode_DB

    data = {}
    for doc in coll.find({}, {"name":1, "geometry_fixed":1, "district":1, "state":1, 
                              "pincode_category":1, "area":1, "_id":0}):
        try:
            pincode = int(doc["name"])  # Convert int64 to int
            geom = doc.get("geometry_fixed")
            if geom and isinstance(geom, dict) and geom.get("type") in ["Polygon", "MultiPolygon"]:
                polygon = shape(geom)
                centroid = polygon.centroid
                lat, lon = centroid.y, centroid.x
                data[pincode] = {
                    "lat": lat,
                    "lon": lon,
                    "district": doc.get("district", ""),
                    "state": doc.get("state", ""),
                    "pincode_category": doc.get("pincode_category", ""),
                    "area": doc.get("area", "")
                }
        except Exception:
            continue
    return data

# 4️⃣ Streamlit UI
st.title("📌 Pincode Distance Calculator")

from_pincode_input = st.text_input("Enter From Pincode", "")
to_pincode_input = st.text_input("Enter To Pincode", "")

if st.button("Calculate Distance"):
    # Validate input
    try:
        from_pincode = int(from_pincode_input)
        to_pincode = int(to_pincode_input)
    except ValueError:
        st.error("❌ Pincode must be a number.")
    else:
        # Load MongoDB data only when button is clicked
        PINCODE_DATA = load_pincode_data()

        if not PINCODE_DATA:
            st.error("❌ No valid pincode geometries found in MongoDB.")
        elif from_pincode not in PINCODE_DATA or to_pincode not in PINCODE_DATA:
            st.error("❌ One or both pincodes not found in the database.")
        else:
            # Get centroids
            lat1, lon1 = PINCODE_DATA[from_pincode]["lat"], PINCODE_DATA[from_pincode]["lon"]
            lat2, lon2 = PINCODE_DATA[to_pincode]["lat"], PINCODE_DATA[to_pincode]["lon"]

            # Calculate distance
            distance = round(haversine(lat1, lon1, lat2, lon2), 2)

            # Display distance in bold
            st.markdown(f"**📏 Distance between {from_pincode} and {to_pincode}: {distance} km**")

            # Prepare table data
            table_data = [
                {
                    "Pincode": from_pincode,
                    "District": PINCODE_DATA[from_pincode]['district'],
                    "State": PINCODE_DATA[from_pincode]['state'],
                    "Pincode Category": PINCODE_DATA[from_pincode]['pincode_category'],
                    "Area": PINCODE_DATA[from_pincode]['area']
                },
                {
                    "Pincode": to_pincode,
                    "District": PINCODE_DATA[to_pincode]['district'],
                    "State": PINCODE_DATA[to_pincode]['state'],
                    "Pincode Category": PINCODE_DATA[to_pincode]['pincode_category'],
                    "Area": PINCODE_DATA[to_pincode]['area']
                }
            ]

            df = pd.DataFrame(table_data)

            st.subheader("📋 Pincode Details")
            st.table(df)  # Use st.dataframe(df) if you want scrollable table
