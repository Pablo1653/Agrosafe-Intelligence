"""
Google Places API Connector (New) - Text Search.

Official documentation: https://developers.google.com/maps/documentation/places/web-service/text-search

It does not use the “legacy” API (maps.googleapis.com/.../textsearch/json), which Google
is gradually migrating to this new version based on POST + JSON.
"""
import requests

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# We only request the fields we actually use: requesting more than we need costs more
# (Google charges based on the fields included in the FieldMask).
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.websiteUri",
    "places.nationalPhoneNumber",
    "places.addressComponents",
    "places.types",
])


class GooglePlacesError(Exception):
    """Any issues when accessing Google Places (invalid key, no
    connection, error response, etc.) should be reported using this type, so that
    the view can display a clear message without breaking the page"""
    pass


def _extract_city(address_components):
    """
    Google doesn't return a “city” directly: you have to look for it within
    addressComponents, in the component whose type is “locality.”
    """
    for component in address_components or []:
        if "locality" in component.get("types", []):
            return component.get("longText", "")
    return ""


def search_google_places(text_query: str, api_key: str, max_results: int = 20) -> list[dict]:
    """
    Searches for locations using free-text queries (e.g., “grain storage in Rosario, Argentina”)
    and returns a list of pre-normalized dictionaries, ready to create
    RawCompany.

    Note: Text Search (New) returns a maximum of 20 results per call.
    For a larger volume of results, vary your search criteria (by city, by
    county, etc.) and run multiple searches instead of a single one.
    """
    if not api_key:
        raise GooglePlacesError(
            "Falta configurar GOOGLE_PLACES_API_KEY (variable de entorno). "
            "Sin la API key no se puede consultar Google Places."
        )

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    payload = {
        "textQuery": text_query,
        "maxResultCount": min(max_results, 20),
    }

    try:
        response = requests.post(PLACES_SEARCH_URL, json=payload, headers=headers, timeout=15)
    except requests.RequestException as exc:
        raise GooglePlacesError(f"No se pudo conectar con Google Places: {exc}") from exc

    if response.status_code != 200:
        raise GooglePlacesError(
            f"Google Places respondió con error {response.status_code}: {response.text[:300]}"
        )

    places = response.json().get("places", [])

    results = []
    for place in places:
        display_name = (place.get("displayName") or {}).get("text", "")
        if not display_name:
            continue
        results.append({
            "business_name": display_name,
            "website": place.get("websiteUri", ""),
            "city": _extract_city(place.get("addressComponents")),
            "formatted_address": place.get("formattedAddress", ""),
            "phone": place.get("nationalPhoneNumber", ""),
            "place_id": place.get("id", ""),
            "types": place.get("types", []),
        })
    return results