def generate_shopping_cart(sc_ingredients):
    text = 'Список покупок:\n\n'
    for ingredient in sc_ingredients:
        text += (
            f'{ingredient["name"]} '
            f'({ingredient["measurement_unit"]}) - '
            f'{ingredient["amount"]}\n'
        )
    return text
