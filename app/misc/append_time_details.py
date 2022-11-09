"""
Adds timedetails to any data provided
"""
import datetime
day_names = [
    'Mon', 'Tue', 'Wed',
    'Thu', 'Fri', 'Sat',
    'Sun'
]


def append_time_details(data: dict, just_return=None) -> dict:
    """
    - Adds the date, year, month, day, timestamp to the time provided
    """

    right_now = datetime.datetime.now()
    time_detail = {}
    day = right_now.weekday()

    if just_return:
        day = day
        time_detail['date'] = right_now.day
        time_detail['month'] = right_now.month
        time_detail['year'] = right_now.year
        time_detail['day'] = day_names[day]
        time_detail['timestamp'] = right_now
        return time_detail

    data['creation_time_details'] = {
        'date': right_now.day,
        'month': right_now.month,
        'year': right_now.year,
        'day': day_names[day],
        'timestamp': right_now
    }
    return data
