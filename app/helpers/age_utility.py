from datetime import datetime


def get_item_age(time=None):
    """
    Get a datetime object or an int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc.
    """

    now = datetime.now()

    if time is None:
        return "Invalid time provided"

    diff = now - time

    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return f"{int(second_diff)} seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return f"{int(second_diff / 60)} minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return f"{int(second_diff / 3600)} hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return f"{int(day_diff)} days ago"
    if day_diff < 31:
        return f"{int(day_diff / 7)} weeks ago"
    if day_diff < 365:
        return f"{int(day_diff / 30)} months ago"
    return f"{int(day_diff / 365)} years ago"
