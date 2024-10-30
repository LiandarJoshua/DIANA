from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime
import google.auth


# Replace with your service account credentials
creds = google.auth.load_credentials_from_file('credentials.json')[0]


calendar_service = build('calendar', 'v3', credentials=creds)

def create_event(summary, start_time, end_time):
    """Create a new calendar event"""
    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'UTC',
        },
    }
    event = calendar_service.events().insert(calendarId='primary', body=event).execute()
    print(f'Event created: {event.get("htmlLink")}')

def get_events(start_time, end_time):
    """Retrieve events within a specified time range"""
    events_result = calendar_service.events().list(
        calendarId='primary', timeMin=start_time.isoformat(), timeMax=end_time.isoformat(),
        singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events

# Example usage with voice commands
start_time = datetime.datetime.now() + datetime.timedelta(hours=1)
end_time = start_time + datetime.timedelta(hours=1)
create_event('Meeting', start_time, end_time)

events = get_events(start_time, end_time)
for event in events:
    start = event['start'].get('dateTime', event['start'].get('date'))
    print(f"- {event['summary']} ({start})")