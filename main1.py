import configparser
import os
import datetime
import sys
import time
import cv2
import random
import speech_recognition as sr
import requests
import wikipedia
import webbrowser
import pyttsx3
import pyjokes
import psutil
import pyautogui
from requests import get
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from transformers import pipeline
from groq import Groq
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import asyncio
import edge_tts
import pygame
from io import BytesIO
import tempfile
import os
from pynput import keyboard
import sqlite3


def execute_sql(sql_query, params=None):
    """
    Execute a SQL query and return the result.
    """
    conn = sqlite3.connect('diana.db')
    cursor = conn.cursor()
    
    if params:
        cursor.execute(sql_query, params)
    else:
        cursor.execute(sql_query)
    
    result = cursor.fetchall()
    conn.commit()
    conn.close()
    return result
def initialize_database():
    sql_create_events_table = """
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date_time TEXT
    )
    """
    sql_create_tasks_table = """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT
    )
    """
    execute_sql(sql_create_events_table)
    execute_sql(sql_create_tasks_table)

# Call the initialize_database function at the start of your script
initialize_database()

# Set up API keys
os.environ["GROQ_API_KEY"] = "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"
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise EnvironmentError("GROQ_API_KEY environment variable is not set.")

# Initialize Groq client
client = Groq(api_key=api_key)

# Initialize text-to-speech engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # Set your preferred voice index
engine.setProperty('rate', 180)  # Set a comfortable speaking rate

# Maintain a context window for recent queries
MAX_CONTEXT_SIZE = 1000 
context_window = []

def update_context(query, response):
    """
    Add a query-response pair to the context window.
    Remove the oldest interaction if the context exceeds MAX_CONTEXT_SIZE.
    """
    context_window.append((query, response))
    if len(context_window) > MAX_CONTEXT_SIZE:
        context_window.pop(0)

def get_context_text():
    """
    Concatenate the recent conversation context to create a relevant dialogue.
    This text will be used as context for generating responses.
    """
    context_text = ""
    for query, response in context_window:
        context_text += f"User: {query}\nDiana: {response}\n"
    return context_text


pygame.mixer.init()

# Flag to control interruption
interrupt_speech = False

def on_press(key):
    global interrupt_speech
    if key == keyboard.Key.space:
        interrupt_speech = True
        pygame.mixer.music.stop()

def on_release(key):
    global interrupt_speech
    if key == keyboard.Key.space:
        interrupt_speech = False

# Setting up keyboard listener for spacebar interruption
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()
VOICE = "en-US-AriaNeural"  # You can change to other voices like "en-GB-SoniaNeural" or "en-US-GuyNeural"
RATE = "+20%"  # Can be adjusted: "-50%" to "+50%"

async def _speak_async(text):
    """
    Internal async function to handle TTS conversion and playback
    """
    global interrupt_speech
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
        temp_file = fp.name
    
    try:
        # Initialize edge-tts
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
        await communicate.save(temp_file)
        
        # Play the audio if not interrupted
        if not interrupt_speech:
            print(text)  # Print the text being spoken
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for the audio to finish or be interrupted
            while pygame.mixer.music.get_busy() and not interrupt_speech:
                pygame.time.Clock().tick(10)
    
    finally:
        # Clean up the temporary file
        pygame.mixer.music.unload()
        try:
            os.unlink(temp_file)
        except:
            pass


# Text-to-speech function with interruption handling
def speak(text):
    """
    Main speaking function that handles the async call
    """
    global interrupt_speech
    interrupt_speech = False
    asyncio.run(_speak_async(text))
import csv

def create_event(name, date_time):
    sql = "INSERT INTO events (name, date_time) VALUES (?, ?)"
    execute_sql(sql, (name, date_time))
    speak(f"Okay, I've created an event called '{name}' at {date_time}.")

def get_events():
    sql = "SELECT name, date_time FROM events"
    events = execute_sql(sql)
    return [{'name': name, 'time': date_time} for name, date_time in events]
tasks = []
def add_task(task):
    sql = "INSERT INTO tasks (task) VALUES (?)"
    execute_sql(sql, (task,))
    speak(f"Task '{task}' has been added.")

def view_tasks():
    sql = "SELECT task FROM tasks"
    tasks = [task[0] for task in execute_sql(sql)]
    if tasks:
        task_list = ', '.join(tasks)
        speak(f"Your tasks are: {task_list}.")
    else:
        speak("You have no tasks in your list.")
def remove_task(task):
    sql = "DELETE FROM tasks WHERE task = ?"
    if execute_sql(sql, (task,)):
        speak(f"Task '{task}' has been removed.")
    else:
        speak(f"Task '{task}' is not found in your list.")
        
def send_email(to_email, subject, message, file_location=None):
    email = 'joshuxvro@gmail.com'  # Your email
    password = 'msdhoni123'     # Your email account password

    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    # If there is a file to attach
    if file_location:
        filename = os.path.basename(file_location)
        try:
            with open(file_location, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename={filename}")
                msg.attach(part)
        except Exception as e:
            speak(f"Could not attach the file. Error: {str(e)}")
            return

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, to_email, msg.as_string())
        server.quit()
        speak("Email has been sent successfully.")
    except Exception as e:
        speak(f"Failed to send email. Error: {str(e)}")


# Voice recognition to text
def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)  # Adjust for ambient noise
        print("Listening...")
        try:
            audio = r.listen(source, timeout=30, phrase_time_limit=40)  # Listening with a timeout
            print("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            print(f"User said: {query}")
            return query.lower()
        except sr.UnknownValueError:
            return "none"
        except sr.RequestError:
            return "none"
        except Exception as e:
            print(f"Error: {str(e)}")
            return "none"

# Greeting the user based on time
from datetime import datetime
import time

def greet_user():
    hour = datetime.now().hour
    tt = time.strftime("%I:%M %p")
    if hour < 12:
        speak(f"Good morning, it's {tt}")
    elif hour < 18:
        speak(f"Good afternoon, it's {tt}")
    else:
        speak(f"Good evening, it's {tt}")
    speak("I am Diana. How can I help you?")

# Function to handle non-command prompts
def get_groq_response(input_text: str) -> str:
    """
    Use Groq API to generate a response based on user input and context.
    """
    # Include the context in the prompt for continuity
    context_text = get_context_text()
    prompt = f"{context_text}User: {input_text}\nDiana:"

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a helpful assistant with personality, sass, and humor."},
                      {"role": "user", "content": prompt}],
            model="llama3-8b-8192"
        )
        generated_text = chat_completion.choices[0].message.content

        # Update the context window with the new interaction
        update_context(input_text, generated_text)
        
        return generated_text
    except Exception as e:
        return f"An error occurred: {e}"

# Fetching weather data from Weather.com
import requests
from bs4 import BeautifulSoup

def weather():
    speak("Checking the details for weather...")
    
    # Using OpenWeatherMap API for more reliable weather data
    API_KEY = "e10af6d03a21b46cb2db08d2c45ae477"
    CITY = "Dubai"  # Default city
    
    try:
        # Make API request
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': CITY,
            'appid': API_KEY,
            'units': 'metric'  # For Celsius
        }
        
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
        
        weather_data = response.json()
        
        # Extract weather information
        temperature = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        humidity = weather_data['main']['humidity']
        description = weather_data['weather'][0]['description']
        
        # Convert Celsius to Fahrenheit
        temp_f = (temperature * 9/5) + 32
        feels_like_f = (feels_like * 9/5) + 32
        
        # Prepare weather report
        weather_report = f"The temperature in {CITY} is {temp_f:.1f}°F ({temperature:.1f}°C) "
        weather_report += f"and it feels like {feels_like_f:.1f}°F ({feels_like:.1f}°C). "
        weather_report += f"The humidity is {humidity}% and the weather is {description}."
        
        speak(weather_report)
        
        # Additional clothing recommendation based on temperature
        if temperature < 10:  # Below 10°C (50°F)
            speak("It's quite cold. I'd recommend wearing warm clothes or a heavy jacket.")
        elif temperature < 20:  # Below 20°C (68°F)
            speak("It's cool outside. A light jacket would be appropriate.")
        elif temperature < 30:  # Below 30°C (86°F)
            speak("The temperature is moderate. Light clothing should be comfortable.")
        else:  # 30°C (86°F) and above
            speak("It's quite warm. Wear light, breathable clothing and don't forget to stay hydrated.")
            
    except requests.exceptions.RequestException as e:
        speak(f"Sorry, I encountered an error while fetching weather data: {str(e)}")
        speak("Please check your internet connection or try again later.")
    except KeyError as e:
        speak("Sorry, I couldn't parse the weather data properly. The city might not be found.")
    except Exception as e:
        speak(f"An unexpected error occurred: {str(e)}")

# Optional: Function to set the city
def set_weather_city(city_name):
    global CITY
    CITY = city_name
    speak(f"Weather location set to {city_name}")
# Function to simulate text-to-speech (replace this with your actual implementation)
def open_website(url, name="the website"):
    """Generic function to open websites with error handling"""
    try:
        webbrowser.open(url)
        speak(f"Opening {name}")
    except Exception as e:
        speak(f"Sorry, I couldn't open {name}. Error: {str(e)}")

def open_google():
    open_website("https://www.google.com", "Google")

def open_youtube():
    open_website("https://www.youtube.com", "YouTube")

# Fetching news 494000f6bb27427eae34bd8835f74f1f
def fetch_news(category='general'):
    """
    Fetch news from multiple sources with category support
    Categories: general, technology, business, science, health, sports, entertainment
    """
    # You can get your API key from https://newsapi.org/
    API_KEY = '494000f6bb27427eae34bd8835f74f1f'
    
    try:
        # Get news from multiple sources
        sources = [
            {'name': 'Top Headlines', 'url': f'https://newsapi.org/v2/top-headlines?country=us&category={category}&apiKey={API_KEY}'},
            {'name': 'Technology News', 'url': f'https://newsapi.org/v2/top-headlines?category=technology&apiKey={API_KEY}'},
            {'name': 'Business News', 'url': f'https://newsapi.org/v2/top-headlines?category=business&apiKey={API_KEY}'}
        ]
        
        speak(f"Here are today's {category} headlines.")
        
        for source in sources:
            response = requests.get(source['url'])
            news_data = response.json()
            
            if news_data['status'] == 'ok' and news_data['articles']:
                speak(f"\nFrom {source['name']}:")
                for i, article in enumerate(news_data['articles'][:3], 1):
                    headline = article['title']
                    speak(f"{i}. {headline}")
                        
    except Exception as e:
        speak(f"Sorry, I encountered an error while fetching news: {str(e)}")
import re
def is_valid_email(email):
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email) is not None

# Getting IP address
def get_ip_address():
    try:
        ip = get('https://api.ipify.org').text
        speak(f"Your IP address is {ip}")
    except requests.RequestException:
        speak("Unable to fetch IP address at the moment.")

# Fetching battery status
def battery_status():
    battery = psutil.sensors_battery()
    percentage = battery.percent
    speak(f"Battery is at {percentage} percent.")
    if battery.power_plugged:
        speak("System is charging.")

# Taking a screenshot
def take_screenshot():
    screenshot_name = f"C://Users//{psutil.users()[0].name}//Desktop//screenshot.png"
    pyautogui.screenshot(screenshot_name)
    speak("Screenshot saved to desktop.")

# Shutting down the system
def shutdown():
    speak("Shutting down.")
    os.system("shutdown /s /t 1")

# Restarting the system
def restart():
    speak("Restarting.")
    os.system("shutdown /r /t 1")
def remove_event(event_name):
    sql = "DELETE FROM events WHERE name = ?"
    execute_sql(sql, (event_name,))
    speak(f"Event '{event_name}' has been removed.")
import webbrowser
from pytube import Search

# Function to search and play a song on YouTube
import webbrowser
from youtube_search import YoutubeSearch

def play_youtube_song(song_name):
    # Use youtube-search-python to search for the song
    results = YoutubeSearch(song_name, max_results=1).to_dict()
    
    if results:
        video_id = results[0]['id']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Open the video URL in the web browser
        webbrowser.open(video_url)
        speak(f"Playing {song_name} on YouTube.")
    else:
        speak(f"Sorry, I couldn't find a video for '{song_name}' on YouTube.")


# Putting the system to sleep
def sleep_system():
    speak("Putting system to sleep.")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

# Open camera function
# Open camera function with option to close by pressing '1'

def open_camera():
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, img = cap.read()
        if not ret:
            break
        cv2.imshow('Webcam', img)
        
        # Wait for key event with 1ms delay; closes if '1' is pressed
        if cv2.waitKey(1) & 0xFF == ord('1'):
            break  
        # Close the camera feed

    cap.release()
    cv2.destroyAllWindows()
    speak("Camera closed. I'm listening for commands again.")


def play_music():
    music_dir = "E:\\music"  
    songs = [song for song in os.listdir(music_dir) if song.endswith('.mp3')]
    if songs:
        random_song = random.choice(songs)
        os.startfile(os.path.join(music_dir, random_song))
        speak(f"Playing {random_song}")
    else:
        speak("No music files found in the directory.")

def tell_time():
    current_time = datetime.now().strftime("%I:%M %p")
    speak(f"The current time is {current_time}")

# Command execution based on input
def execute_command(query):
    functional_commands = ["open notepad", "open command prompt", 
                           "open camera", "play", "tell me a joke", "news", 
                           "wikipedia", "open youtube", "open google", 
                           "ip address", "battery", "screenshot", "shutdown", 
                           "restart", "sleep", "tell me the time", "weather","alarm","wifi speed","internet speed","add task","view tasks","remove task","show tasks","show task","create event","list events","remove event","delete event"]

    if any(cmd in query for cmd in functional_commands):
        if "open notepad" in query:
            os.startfile("C:\\Windows\\system32\\notepad.exe")
        elif "open command prompt" in query:
            os.system("start cmd")
        elif "play" in query:
            song_name = query.replace("play song", "").replace("play", "").strip()  # Extract song name from the query
            play_youtube_song(song_name)
        elif "open camera" in query:
            open_camera()
        if "open google" in query:
            open_google()
        elif "open youtube" in query:
            open_youtube()
        elif "play music" in query:
            play_music()
        elif "add task" in query:
            task = query.replace("add task", "").strip()
            add_task(task)
        elif "remove task" in query or "delete task" in query:
            task = query.replace("remove task", "").strip()
            remove_task(task)
        elif "show tasks" in query or "show task" in query:
            view_tasks()
        elif "tell me a joke" in query:
            speak(pyjokes.get_joke())
        elif "news" in query:
            fetch_news()
        elif "ip address" in query:
            get_ip_address()
        elif "battery" in query:
            battery_status()
        elif "screenshot" in query:
            take_screenshot()
        elif "shutdown" in query:
            shutdown()
        elif "restart" in query:
            restart()
        elif "remove event" in query or "delete event" in query:
            speak("Which event would you like to remove?")
            event_name = take_command()
            remove_event(event_name)
        elif "sleep" in query:
            sleep_system()
        elif "create event" in query or "add events" in query:
            speak("What would you like to call the event?")
            event_name = take_command()
            speak("When should the event be scheduled?")
            event_time = take_command()
            create_event(event_name, event_time)
        elif "list events" in query or "show events" in query:
            events = get_events()
            if events:
                speak("Here are your upcoming events:")
                for event in events:
                    speak(f"{event['name']} on {event['time']}")
            else:
                speak("You don't have any events scheduled.")
        elif "tell me the time" in query:
            tell_time()
        elif 'volume up' in query or 'increase volume' in query:
            pyautogui.press("volumeup")
        elif 'volume down' in query or 'decrease volume' in query:
            pyautogui.press("volumedown")
        elif 'mute' in query:
            pyautogui.press("volumemute")
        elif "email" in query:
            speak("Sir, who should I send the email to?")
            recipient_email = take_command().lower()  # Capture the recipient's email

            if not is_valid_email(recipient_email):
                speak("That doesn't seem like a valid email address. Please provide a correct email address.")
                return  # Exit or ask for the email again

            speak("Sir, what should I say?")
            query = take_command().lower()

            if "send a file" in query:
                speak("Okay sir, what is the subject for this email?")
                subject = take_command().lower()
                speak("And sir, what is the message for this email?")
                message = take_command().lower()
                speak("Sir, please enter the correct path of the file into the shell.")
                file_location = input("Please enter the path here: ")

                speak("Please wait, I am sending the email now.")
                send_email(recipient_email, subject, message, file_location)

            else:
                speak("What is the subject for this email?")
                subject = take_command().lower()
                message = query  # Use the message captured earlier

                send_email(recipient_email, subject, message)

        elif 'alarm' in query:
            speak("When should i set the alarm to?")
            tt=take_command()
            tt=tt.replace("set alarm to ","")
            tt=tt.replace(".","")
            tt=tt.upper()
            import myalarm
            myalarm.alarm(tt) 
        elif "weather" in query:
            weather()  # Call the weather function
        elif "Wi-Fi speed" in query or "internet speed" in query:
            import speedtest

            st = speedtest.Speedtest()
            dl = st.download() /1000000
            up = st.upload() /1000000
            speak(f"Right now, the download speed is {dl:.2f} Mbps, and the upload speed is {up:.2f} Mbps")

        else:
            search_term = query.replace("wikipedia", "").strip()
            summary = wikipedia.summary(search_term, sentences=1)
            speak(summary)
    else:
        response = get_groq_response(query)
        speak(response)

if __name__ == "__main__":
    while True:
        quer=take_command()
        if "wake" in quer or "hey diana" in quer:
            
            greet_user()
            while True:
                query = take_command()
                if query == "none":
                    continue
                if "exit" in query or "bye" in query:
                    speak("Goodbye! Have a great day!")
                    sys.exit()
                execute_command(query)
        
