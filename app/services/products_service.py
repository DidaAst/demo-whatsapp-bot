import json

def get_top_3_products():
    products = [
        {
            "id": 1,
            "title": "Knitted Romper 'Marshmallow'",
            "description": "Cozy knitted romper for infants, perfect for cool weather. Made from soft wool, does not irritate the skin.",
            "sku": "ZZ1234"
        },
        {
            "id": 2,
            "title": "Summer Dress 'Sunbeam'",
            "description": "Bright summer dress for girls with a floral and butterfly print. The light and airy material provides comfort in hot weather.",
            "sku": "SL4567"
        },
        {
            "id": 3,
            "title": "Jacket 'Little Explorer'",
            "description": "Waterproof and windproof jacket for active outdoor walks. Features bright reflective elements for safety in the dark.",
            "sku": "EX8901"
        }
    ]
    return json.dumps(products)
