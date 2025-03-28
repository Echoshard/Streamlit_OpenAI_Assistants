## Open AI Assistant Agent StreamLit

This is a StreamLit example that uses threads and OpenAI's assistant API. 

This StreamLit bot uses the assistants API with threads.

### Supports

- Web scraping 
- File upload (Text files are put in stream not uploaded to thread)
- Vision (Image upload)
- Private keying
- Assistant loading and switching
- Thread clearing
- Youtube transcript 'unstable'

A note that uploading files or vision will add to your openAI storage. 

### Configuration

When running on Streamlit cloud this can be configured for a secret key and assistant API or the user can insert there own keys and assistant IDs.

```
#-------------------------- TOM Secrets
openai_key = st.secrets["openai_key"]
default_assistant = st.secrets["default_assistant"]
secret_key = st.secrets["secret_key"]
```

Additionally there are settings for plain text and setting a .env. Uncomment and comment the ones needed.

```
#------------------------------ Local Quick Keying
# openai_key = ""
# default_assistant = ""
# secret_key = ""

#----------------------------- .env
# openai_key = os.environ.get("openai_key")
# default_assistant = os.environ.get("assistant_id")
# secret_key = os.environ.get("secret_key")
```

As for the rest of the settings.


This will fetch all the assistants listed on this OpenAI's project account if set to false it will only talk to the default assistant. Useful for sharing a bunch of GPTS the assistant named `Default Assistant` Will always be at the top of the list if it exists

```
fetch_assistants = True
```

Flags for enabling/disabling features

```
disable_youtube = True
disable_scraping = False
disable_fileUpload = False
```

## Using the Secret Key

The secret key is designed to stop your app from being public entirely it can be activated by setting `requireKey` to true This will the require the user to put the correct param when navigating for example.

```
www.yourStreamLitAssistant.com/?secretkey=SECRET
```

## Local Running
- Download this repo and set your keys up
```
 pip install -r requirements.txt
```

```
 python -m streamlit run PATH:\\OpenAI_Streamlit_Assistants.py
```

# Hosting your App:
The fastest way to run this using streamlit using https://streamlit.io/gallery. 
Another site for doing this is https://render.com/

