import os
from dotenv import load_dotenv
from langchain.tools import tool
from serpapi import GoogleSearch
from loguru import logger
from typing import Optional

load_dotenv()

@tool
def search_recipes(
    query: str,
    location: Optional[str] = None,
    google_domain: str = "google.com",
    language: str = "en",
    country: str = "us"
) -> str:
    """
    Search for recipes using Google Search via SerpApi.
    
    Args:
        query: Recipe or dish name to search for (e.g., "cheesecake", "tiramisu", "pasta carbonara")
        location: Optional location for localized results (e.g., "Italy", "United States")
        google_domain: Google domain to use (default: "google.com")
        language: Language code for results (default: "en")
        country: Country code for results (default: "us")
    
    Returns:
        Structured recipe information including title, source, rating, cooking time, and ingredients.
    """
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "❌ Error: SERPAPI_API_KEY not found in environment variables."

        params = {
            "q": query,
            "google_domain": google_domain,
            "hl": language,
            "gl": country,
            "api_key": api_key
        }
        
        # Add location if provided
        if location:
            params["location"] = location
        
        logger.info(f"Searching recipes via SerpApi: {query}")
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "error" in results:
            return f"❌ SerpApi Error: {results['error']}"
            
        # Extract recipe results
        recipes = results.get("recipes_results", [])
        
        if not recipes:
            return f"❌ No recipes found for '{query}'."
            
        # Build formatted output
        output = f"👨‍🍳 *Recipes for: {query}*\n\n"
        
        for idx, recipe in enumerate(recipes[:8], 1):  # Show top 8 recipes
            title = recipe.get("title", "Unknown Recipe")
            source = recipe.get("source", "Unknown Source")
            link = recipe.get("link", "")
            rating = recipe.get("rating", "N/A")
            reviews = recipe.get("reviews", 0)
            total_time = recipe.get("total_time", "N/A")
            
            # Ingredients
            ingredients = recipe.get("ingredients", [])
            ingredients_str = ", ".join(ingredients[:5]) if ingredients else "N/A"
            if len(ingredients) > 5:
                ingredients_str += f" (+{len(ingredients) - 5} more)"
            
            # Thumbnail
            thumbnail = recipe.get("thumbnail", "")
            
            # Badge (e.g., "ANTEPRIMA", "VIDEO")
            badge = recipe.get("badge", "")
            
            # Video
            video = recipe.get("video", "")
            
            output += f"{idx}. *{title}*\n"
            output += f"   📰 Source: {source}\n"
            
            # Rating and reviews
            if rating != "N/A" and reviews:
                output += f"   ⭐ {rating}/5 ({reviews} reviews)\n"
            elif rating != "N/A":
                output += f"   ⭐ {rating}/5\n"
            
            # Cooking time
            if total_time != "N/A":
                output += f"   ⏱️ Time: {total_time}\n"
            
            # Ingredients
            if ingredients_str != "N/A":
                output += f"   🥘 Ingredients: {ingredients_str}\n"
            
            # Badge
            if badge:
                output += f"   🏷️ {badge}\n"
            
            # Links
            if video:
                output += f"   🎥 [Watch Video]({video})\n"
            if link:
                output += f"   🔗 [View Recipe]({link})\n"
            
            # Thumbnail (just mention it's available, don't embed in text output)
            if thumbnail:
                output += f"   🖼️ [Thumbnail]({thumbnail})\n"
            
            output += "\n"
        
        # Add search metadata if available
        metadata = results.get("search_metadata", {})
        search_url = metadata.get("google_url", "")
        if search_url:
            output += f"🔗 [View all results on Google]({search_url})"
            
        return output

    except Exception as e:
        logger.error(f"Error searching recipes: {e}")
        return f"❌ Error executing recipe search: {str(e)}"
