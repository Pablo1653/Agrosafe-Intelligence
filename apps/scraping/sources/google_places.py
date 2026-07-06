"""
Conector para Google Places API (New) - Text Search.

Documentación oficial: https://developers.google.com/maps/documentation/places/web-service/text-search

No usa la API "legacy" (maps.googleapis.com/.../textsearch/json), que Google
está migrando gradualmente hacia esta versión nueva basada en POST + JSON.
"""
import requests

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# Solo pedimos los campos que realmente usamos: pedir de más sale más caro
# (Google cobra según los campos incluidos en el FieldMask).
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
    """Cualquier problema al consultar Google Places (key inválida, sin
    conexión, respuesta de error, etc.) se reporta con este tipo, para que
    la vista pueda mostrar un mensaje claro sin romper la página."""
    pass


def _extract_city(address_components):
    """
    Google no devuelve una 'ciudad' directa: hay que buscarla dentro de
    addressComponents, en el componente cuyo tipo es 'locality'.
    """
    for component in address_components or []:
        if "locality" in component.get("types", []):
            return component.get("longText", "")
    return ""


def search_google_places(text_query: str, api_key: str, max_results: int = 20) -> list[dict]:
    """
    Busca lugares por texto libre (ej. "acopio de granos en Rosario, Argentina")
    y devuelve una lista de diccionarios ya normalizados, listos para crear
    RawCompany.

    Nota: Text Search (New) devuelve como máximo 20 resultados por llamada.
    Para más volumen, hay que variar la búsqueda (por localidad, por
    partido, etc.) y correr varias búsquedas en vez de una sola.
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