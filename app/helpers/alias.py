import uuid


def create_alias(input_string):
    if not input_string:
        return None
    new_string = ''.join(
        letter for letter in input_string.lower()
        if letter.isalnum() or letter == '-')

    uuid_string = str(uuid.uuid4())[:23]

    return f'{new_string}-{uuid_string}'


def shorten_alias(input_string):
    if not input_string:
        return None
    parts = input_string.split('-')
    if len(parts) >= 3:
        # Join all but the last 4 parts as the name, and the next part as the first part of the uuid
        # Example: name-me-31affa06-9c76-474b-80bc
        # parts: ['name', 'me', '31affa06', '9c76', '474b', '80bc']
        # name: 'name-me', uuid: '31affa06'
        name_part = '-'.join(parts[:-4])
        uuid_part = parts[-4]
        return f"{name_part}-{uuid_part}" if name_part else uuid_part
    return input_string
