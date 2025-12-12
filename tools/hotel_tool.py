import os
from dotenv import load_dotenv
from langchain.tools import tool
from serpapi import GoogleSearch
from loguru import logger
from typing import Optional

load_dotenv()

@tool
def search_hotels(
    location: str,
    check_in: str,
    check_out: str,
    guests: int = 2
) -> str:
    """
    Search for hotels using Google Hotels via SerpApi.
    
    Args:
        location: City or location name (e.g., "Paris", "New York", "Rajahmundry")
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        guests: Number of adults (default: 2)
    
    Returns:
        Structured hotel information including price, rating, and amenities.
    """
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "❌ Error: SERPAPI_API_KEY not found in environment variables."

        params = {
            "api_key": api_key,
            "engine": "google_hotels",
            "q": f"hotels in {location}",
            "hl": "en",
            "gl": "us",
            "check_in_date": check_in,
            "check_out_date": check_out,
            "adults": guests,
            "currency": "INR"
        }
        
        logger.info(f"Searching Google Hotels via SerpApi: {location} ({check_in} to {check_out})")
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "error" in results:
            return f"❌ SerpApi Error: {results['error']}"
            
        # SerpApi returns organic results in 'properties'
        properties = results.get("properties", [])
        
        # Sometimes results are in 'ads' or general list if 'properties' is empty? 
        # But 'properties' is standard for Google Hotels API in SerpApi.
        # User snippet showed 'ads' too, let's include them if properties are scarce.
        if not properties:
             properties = results.get("ads", [])
        
        if not properties:
            return f"❌ No hotels found for {location} from {check_in} to {check_out}."
            
        output = f"🏨 *Hotels in {location}*\n"
        output += f"📅 Dates: {check_in} to {check_out} ({guests} guests)\n\n"
        
        for idx, hotel in enumerate(properties[:5], 1):
            name = hotel.get("name", "Unknown Hotel")
            
            # Price handling: user snippet had 'price': '₹3,292' directly, or nested 'rate_per_night'
            price = hotel.get("price", "N/A")
            if not price or price == "N/A":
                 # Try rate_per_night
                 rate = hotel.get("rate_per_night", {})
                 price = rate.get("lowest", "N/A")

            rating = hotel.get("overall_rating", "N/A")
            reviews = hotel.get("reviews", 0)
            
            # Amenities
            amenities = hotel.get("amenities", [])
            amenities_str = ", ".join(amenities[:3]) # First 3
            
            link = hotel.get("link", "")
            
            output += f"{idx}. *{name}*\n"
            output += f"   💵 {price} | ⭐ {rating} ({reviews} reviews)\n"
            if amenities_str:
                output += f"   ✨ {amenities_str}\n"
            if link:
                output += f"   🔗 [Book Now]({link})\n"
            output += "\n"
            
        # Add link to full results if available
        metadata = results.get("search_metadata", {})
        google_hotels_url = metadata.get("google_hotels_url", "")
        if google_hotels_url:
            output += f"🔗 [View all results on Google]({google_hotels_url})"
            
        return output

    except Exception as e:
        logger.error(f"Error searching hotels: {e}")
        return f"❌ Error executing hotel search: {str(e)}"
