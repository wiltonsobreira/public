from ast import main
from unicodedata import normalize
from re import sub

# =============================================================================
#  transform_snake_case
# =============================================================================

def transform_snake_case(string_to_transform: str) -> str:

    # Remove accents from characters
    normalized_string = normalize('NFKD', string_to_transform).encode(
        'ASCII', 'ignore').decode('utf-8')

    # Replace spaces and special characters with underscores
    snake_case_string = sub(r'[^a-zA-Z0-9]+', '_', normalized_string)

    # Remove leading and trailing underscores
    snake_case_string = snake_case_string.strip('_')

    # Convert to lowercase
    snake_case_string = snake_case_string.lower()

    return snake_case_string

if __name__ == "__main__":
   str = "Impulsiona Tech - Integração Contínua"
   print(transform_snake_case(str))
   