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


#-------------------------- TOM Secrets
api_key = st.secrets["api_key"]
default_assistant = st.secrets["default_assistant"]
secret_key = st.secrets["secret_key"]


#For quickly running local put your API keys and comment out the above area
# api_key = ""
# default_assistant = ""
# secret_key = ""

#.env
# api_key = os.environ.get("api_key")
# default_assistant = os.environ.get("assistant_id")
# secret_key = os.environ.get("secret_key")

#Secret Key / this is just an example you could add database auth to this
requireKey = False
# Boolean flag to determine if assistants should be fetched
fetch_assistants = True
# Youtube does not work when hosted on servers for some reason needs to be local?
# https://stackoverflow.com/questions/78860581/error-fetching-youtube-transcript-using-youtubetranscriptapi-on-server-but-works

#Extra features settings
disable_youtube = True
disable_scraping = False
disable_fileUpload = False


botTitle = "OpenAI Assistants"
botdescription = ""

#These are the avatar settings
userAvatar = None
aiAvatar = None
# userAvatar = ":material/face:" 
# aiAvatar = ":material/neurology:"
# userAvatar = "⌨️" 
# aiAvatar = "🖥️"

#Gifs for Images!
side_bar_image = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExNXY4djdoaWpwbzV6bGp1eTkzdWZ0dnI3M2s1bDIzbDFrM2w4amdicCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/2hgs0P312wdBCOgOAf/giphy.webp"
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
    if disable_scraping:
        return "Scraping is Disabled"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract all text content from the website
        text = ' '.join(soup.stripped_strings)
        return text
    except Exception as e:
        return f"❌Error scraping website: {e}"
    
#---------------------------------------------------- Text File Extraction PDF/TXT
# Function to read text from PDF file
def read_pdf(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return f"❌Error reading PDF file: {e}"

# Function to read text from TXT file
def read_txt(file):
    try:
        return file.read().decode("utf-8")
    except Exception as e:
        return f"❌Error reading TXT file: {e}"
    
#----------------------------------------------------- Image Uploader

def attach_image_to_thread(attachment, thread_id):
    print(f"🔎Attaching file {attachment}")
    client = OpenAI(api_key=st.session_state.api_key)
    
    upload_response = client.files.create(
        purpose='vision',
        file=attachment
    )
    # Attach file to thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=[
            {
                "type": "text",
                "text": "Picture Uploaded"
            },
            {
                "type": "image_file",
                "image_file": {
                    "file_id": upload_response.id,
                    "detail": "high"
                }
            }
        ]
    )
    
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
st.set_page_config(page_title=botTitle, page_icon=":speech_balloon:",layout="wide")

# Sidebar settings
st.sidebar.markdown(f"<h1 style='text-align: center;'>{botTitle}</h1>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h4 style='text-align: center;'>{botdescription}</h4>", unsafe_allow_html=True)
st.sidebar.image(side_bar_image)

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

# Fetch the assistants if the flag is set
if fetch_assistants:
    st.session_state.options = list_assistants()
    if len(st.session_state.options) == 0:
        st.error("No assistants found. Please check API key or setup assistants")
        st.stop()
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
        if message["role"] == "user":             
            with st.chat_message(message["role"],avatar = userAvatar):
                st.markdown(message["content"])
        else:
            with st.chat_message(message["role"],avatar = aiAvatar):
                st.markdown(message["content"])
    # Chat input for the user
    if prompt := st.chat_input(
        placeholder="What is up?",
        accept_file=not disable_fileUpload, # Allow file uploads if not disabled
        file_type=["txt", "csv", "py", "cs", "ts", "js", "pdf", "html", "md", "xml", "yaml", "yml", "sql", "css", "php","png","jpeg","jpg"]
    ):
        if prompt.text.lower() in ["/clear", "/clean"]:
            st.session_state.thread_id = clean_create_thread()
            return
        if st.session_state.thread_id is None:
            st.session_state.thread_id = clean_create_thread()
            st.empty()
    
        # Replace URLs in the prompt with their transcripts or scraped text.
        urls = re.findall(r'(https?://\S+)', prompt.text)
        processed_prompt = prompt.text
        for url in urls:
            transcript = get_transcript_from_url(url)
            processed_prompt = processed_prompt.replace(url, transcript)
    
        # Process uploaded files.
        if prompt and prompt["files"]:
            for file in prompt["files"]:
                if file.type == "application/pdf":
                    file_text = read_pdf(file)
                elif file.type in ["image/jpeg", "image/png"]:
                    st.session_state.messages.append({"role": "user", "content": "Image uploaded"})
                    prompt.text += f" Image uploaded: {file.name}"
                    attach_image_to_thread(file, st.session_state.thread_id)
                    continue
                else:
                    # For all other text-based files (e.g. txt, csv, py, cs, php, etc.)
                    file_text = file.read().decode("utf-8")
                processed_prompt += "\n" + file_text
                processed_prompt += f"\nFile: {file.name}"
                st.session_state.messages.append({"role": "user", "content": "File Uploaded"})
                prompt.text += f" File uploaded: {file.name}"
        # Add user message to the state and display it (keep original URL and file name)
        st.session_state.messages.append({"role": "user", "content": prompt.text})
        with st.chat_message("user",avatar = userAvatar):
            st.markdown(prompt.text)
        print(processed_prompt)
        # Add the processed message to the existing thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=processed_prompt
        )
        streamingText = ""
        with st.spinner('Processing..'):
            on_stream_start(processed_prompt)
            with st.chat_message("assistant",avatar = aiAvatar):
                with client.beta.threads.runs.stream(
                  thread_id=st.session_state.thread_id,
                  assistant_id=st.session_state.assistant_id,
                ) as stream:
                    response = st.write_stream(stream.text_deltas)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                on_stream_done(prompt,response)
 

def chat_loop():
    main_chat()
    st.sidebar.markdown(f"ThreadID: ```{st.session_state.thread_id}```")
    st.sidebar.markdown(f"Assistant: ```{st.session_state.assistant_id}```")
    st.sidebar.link_button("Set your Assistant here", "https://platform.openai.com/assistants")
    st.sidebar.markdown("🤖 Assistants can make mistakes; please check the code and documentation before using it.");
    st.sidebar.markdown("⚠️ Please note that chats are not saved. If you navigate away from this page, you will lose your conversation.")

#Main Loop
if requireKey:
    if st.query_params.__contains__("secretkey") and st.query_params["secretkey"] == secret_key:
        chat_loop()
    else:
        st.header('Access is Denied', divider='rainbow')
        st.image(error_image)
else:
    chat_loop()
