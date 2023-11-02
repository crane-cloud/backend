import uuid


def create_alias(input_string):
    if not input_string:
        return None
    new_string = ''.join(
        letter for letter in input_string.lower()
        if letter.isalnum() or letter == '-')

    uuid_string = str(uuid.uuid4())[:23]

    return f'{new_string}-{uuid_string}'
