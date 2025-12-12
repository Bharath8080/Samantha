import os
from dotenv import load_dotenv
from langchain.tools import tool
from serpapi import GoogleSearch
from loguru import logger
from typing import Optional

load_dotenv()

@tool
def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None
) -> str:
    """
    Search for flights using Google Flights via SerpApi.
    
    Args:
        origin: Departure Airport Code (e.g., "JFK", "LHR", "HYD")
        destination: Arrival Airport Code (e.g., "LAX", "DXB", "BOM")
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Optional return date in YYYY-MM-DD format
    
    Returns:
        Structured flight information including price, airline, duration, and carbon emissions.
    """
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "❌ Error: SERPAPI_API_KEY not found in environment variables."

        params = {
            "api_key": api_key,
            "engine": "google_flights",
            "hl": "en",
            "gl": "us",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": departure_date,
            "currency": "INR"
        }
        
        if return_date:
            params["return_date"] = return_date
            
        logger.info(f"Searching Google Flights via SerpApi: {origin} -> {destination} on {departure_date}")
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "error" in results:
            return f"❌ SerpApi Error: {results['error']}"
            
        best_flights = results.get("best_flights", [])
        other_flights = results.get("other_flights", [])
        
        # Combine lists but prioritize best flights
        all_flights = best_flights + other_flights
        
        if not all_flights:
            return f"❌ No flights found for {origin} to {destination} on {departure_date}."
            
        output = f"✈️ *Flights from {origin} to {destination}*\n"
        output += f"📅 Departure: {departure_date}"
        if return_date:
            output += f" | Return: {return_date}"
        output += "\n\n"
        
        for idx, flight_group in enumerate(all_flights[:5], 1):
            # SerpApi structure: 'flights' is a list of segments. usually 1 for direct, 2 for layover used in total summary
            # But the top level object has 'price', 'total_duration', etc.
            flight_segments = flight_group.get("flights", [])
            price = flight_group.get("price", "N/A")
            total_duration = flight_group.get("total_duration", "N/A")
            
            # Get main airline from first segment
            airline = "Unknown Airline"
            flight_number = ""
            if flight_segments:
                first_segment = flight_segments[0]
                airline = first_segment.get("airline", "Unknown")
                flight_number = first_segment.get("flight_number", "")
                
                # Times
                dep_time_full = first_segment.get("departure_airport", {}).get("time", "")
                arr_time_full = flight_segments[-1].get("arrival_airport", {}).get("time", "") # Last segment arrival
                
                # Extract HH:MM
                dep_time = dep_time_full.split(" ")[1] if " " in dep_time_full else dep_time_full
                arr_time = arr_time_full.split(" ")[1] if " " in arr_time_full else arr_time_full
            
            output += f"{idx}. *{airline}* ({flight_number})\n"
            output += f"   💵 ${price} | ⏱️ {total_duration} min\n"
            output += f"   🛫 {dep_time} -> 🛬 {arr_time}\n"
            
            # Layovers?
            layovers = flight_group.get("layovers", [])
            if layovers:
                 output += f"   🛑 {len(layovers)} stop(s)\n"
            else:
                 output += f"   🚀 Non-stop\n"
            
            output += "\n"
            
        # Add link if available (SerpApi provides search_metadata -> google_flights_url)
        metadata = results.get("search_metadata", {})
        google_flights_url = metadata.get("google_flights_url", "")
        if google_flights_url:
            output += f"🔗 [View on Google Flights]({google_flights_url})"
            
        return output

    except Exception as e:
        logger.error(f"Error searching flights: {e}")
        return f"❌ Error executing flight search: {str(e)}"
