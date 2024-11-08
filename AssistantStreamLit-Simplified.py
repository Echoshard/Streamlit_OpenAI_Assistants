#------------------------- IMPORTS

import streamlit as st
from openai import OpenAI
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
import requests
import fitz  # PyMuPDF
from io import BytesIO


#-------------------------- Secrets from OPEN AI 
#Do Not push secrets to Github!
#EnvSecrets
api_key = os.environ.get("api_key")
default_assistant = os.environ.get("assistant_id")
secretKey = os.environ.get("secretKey")

#Streamlit Secrets
#api_key = st.secrets["api_key"]
#default_assistant = st.secrets["assistant_id"]
#secretKey = st.secrets["secretKey"]
#For quickly running local put your API keys and comment out the above area
#api_key = "FOR KEYED"
#default_assistant = "assistantKEY"
isKeyed = True
# Boolean flag to determine if assistants should be fetched
fetch_assistants = True
# Youtube does not work when hosted on servers for some reason needs to be local?
# https://stackoverflow.com/questions/78860581/error-fetching-youtube-transcript-using-youtubetranscriptapi-on-server-but-works
disable_youtube = True
disable_url_scrape = True

side_bar_image = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExMmZvNTgzNHI5dm4ybnh1ZjY1bGtxc3E4dHBpMnhubzNhZnliZjU4MCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/7VzgMsB6FLCilwS30v/giphy.webp"
error_image = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExcGlqcGxmaHE2ajM3YnBrMGV0dDdwbTF6NXd5aWM2MXJzMWZubWpqayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/273P92MBOqLiU/giphy.gif"

#---------------------------- URL Transcriptions

# Function to get transcript or scraped text from URL
def get_transcript_from_url(url):
    if "youtube.com" in url or "youtu.be" in url:
        return get_youtube_transcript(url)
    else:
        return scrape_website(url)

# Function to get YouTube transcript
def get_youtube_transcript(url):
    if disable_youtube:
        return "Youtube Processing is Disabled"
    video_id = extract_youtube_video_id(url)
    if not video_id:
        return "Invalid YouTube URL"
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry['text'] for entry in transcript_list])
        return transcript
    except Exception as e:
        print(f"Error retrieving YouTube transcript: {e}")
        return f"Error retrieving YouTube transcript: {e}"

# Function to extract video ID from YouTube URL
def extract_youtube_video_id(url):
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.match(pattern, url)
    return match.group(1) if match else None

# Function to scrape website content
def scrape_website(url):
    if disable_url_scrape:
        return "Url Scraping is Disabled"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract all text content from the website
        text = ' '.join(soup.stripped_strings)
        return text
    except Exception as e:
        return f"❌Error scraping website: {e}"

    
#---------------------------------------------------- Open AI Thread and cleaning
# Clean Thread
def clean_create_thread(thread_id=None):
    client = OpenAI(api_key=st.session_state.api_key)
    st.session_state.messages = []
    if thread_id is None:
        try:
            # Create a new thread
            new_thread = client.beta.threads.create()
            print(f"New thread created with ID: {new_thread.id}")
            return new_thread.id
        except Exception as e:
            print(f"Error creating new thread: {e}")
            return None
    else:
        try:
            # Delete the specified thread
            client.beta.threads.delete(thread_id=thread_id)
            print(f"Thread {thread_id} deleted successfully.")
        except Exception as e:
            print(f"Error deleting thread: {e}")
            return None
        try:
            # Create a new thread
            new_thread = client.beta.threads.create()
            print(f"New thread created with ID: {new_thread.id}")
            return new_thread.id
        except Exception as e:
            print(f"Error creating new thread: {e}")
            return None
        
        
#----------------------------------------------------- StreamLit UI
# Session States
st.session_state.setdefault('thread_id', None)
st.session_state.setdefault('assistant_id', default_assistant)
st.session_state.setdefault('api_key', api_key)

st.session_state.setdefault('systemPrompt', "You are a friendly and helpful assistant.")
st.session_state.setdefault('preprompt', "")
st.set_page_config(page_title="AI Assistants", page_icon=":speech_balloon:",layout="wide")

# Sidebar settings
st.sidebar.header('AI Assistants')
st.sidebar.image(side_bar_image)

if isKeyed:
    st.session_state.api_key = api_key
    st.session_state.assistant_id = default_assistant
else:
    st.session_state.api_key = st.sidebar.text_input('OpenAI API Key')
    st.session_state.assistant_id = st.sidebar.text_input('Assistant ID')


#--------------------------------------------------------------- Assistant List

def list_assistants():
    # Retrieve the list of assistants
    client = OpenAI(api_key=st.session_state.api_key)
    assistants = client.beta.assistants.list()
    
    # Initialize the options dictionary with the Default Assistant first
    options = {}

    for assistant in assistants.data:
        if assistant.name == "Default Assistant":
            options["Default Assistant"] = assistant.id
            break

    # Add the rest of the assistants to the options dictionary
    for assistant in assistants.data:
        if assistant.name != "Default Assistant":
            options[assistant.name] = assistant.id

    return options

if fetch_assistants:
    st.session_state.options = list_assistants()
    # Create a sidebar with a dropdown menu
    selected_assistant = st.sidebar.selectbox("Assistants", list(st.session_state.options.keys()))
    st.session_state.assistant_id = st.session_state.options[selected_assistant]

#--------------------------------------------------------------- System Prompt and Thread buttons

# Buttons
if st.sidebar.button("Clear/New Thread", use_container_width=True):
    if st.session_state.assistant_id == "":
        st.error("No assistant for thread")
    else:
        st.toast("Memory Cleared")
        st.session_state.thread_id = clean_create_thread()
        
#------------------------------------------------------------------------ Stream end and File Upload Cleaning
        
def on_stream_done(user_input,agent_output):
    #a stub for accessing input and output
    print("AI Stream Done")
def on_stream_start(user_input):
    #a stub for accessing input and output
    print("AI Stream Started")

def main_chat():
    # Initialize the model and messages list if not already in session state
    client = OpenAI(api_key=st.session_state.api_key)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    # Display existing messages in the chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    # Chat input for the user
    if prompt := st.chat_input("What is up?"):
        if st.session_state.thread_id is None:
            st.session_state.thread_id = clean_create_thread()
            st.empty()

        # Detect URLs in the prompt and replace with transcripts or scraped text for processing
        urls = re.findall(r'(https?://\S+)', prompt)
        processed_prompt = prompt
        for url in urls:
            transcript = get_transcript_from_url(url)
            processed_prompt = processed_prompt.replace(url, transcript)
            
        # Add user message to the state and display it (keep original URL and file name)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add the processed message to the existing thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=processed_prompt
        )
        # Streaming run    
        on_stream_start(prompt)
        streamingText = ""
        with st.chat_message("assistant"):
            with client.beta.threads.runs.stream(
                thread_id=st.session_state.thread_id,
                assistant_id=st.session_state.assistant_id,
            ) as stream:
                response = st.write_stream(stream.text_deltas)
                st.session_state.messages.append({"role": "assistant", "content": response})
            on_stream_done(prompt,response)
        
if st.query_params.__contains__("secretkey") and st.query_params["secretkey"] == secretKey:
    main_chat()
    st.sidebar.markdown(f"ThreadID: ```{st.session_state.thread_id}```")
    st.sidebar.markdown(f"Assistant: ```{st.session_state.assistant_id}```")
    st.sidebar.link_button("Set your Assistant here", "https://platform.openai.com/assistants")
else:
    st.header('Access is Denied', divider='rainbow')
    st.image(error_image)




# Display current data


