
import streamlit as st
import requests



st.set_page_config(page_title=" LAW FIRMS  ", page_icon=":)", layout="centered")

st.title("Firm Intelligence UI ")



#This makes it horzizontally allignee
tab1, tab2, tab3, tab4 = st.tabs(["1 - Ask Agent", "2 - Semantic Search", "3 -  Stream Summary", "EXTRA - Firm Benchmarks"] )

API_URL  = "http://127.0.0.1:8000"


#Feature 1: Ask
#A text box where someone can type a question in plain English, and a button to send it.

#When clicked, it must call POST /agent/ask with the question, and:

#Show the answer text if the request completed successfully
#Show something sensible if it did not complete (the agent hit its iteration limit)
#Show the number of tool calls made and the token counts somewhere on screen
#Show a clear error message if the request fails, do not let it crash silently

with tab1: 
    Question = st.text_area("FEATURE 1 - ASK AGENT HERE ")

    if st.button("Click me to ask agent something"):

        try:
            # Call POST /agent/ask with the question as a query parameter
            response = requests.post(f"{API_URL}/agent/ask", params={"question": Question}, timeout=60)
            if response.status_code !=200:
                st.write(f"ERROR HAS OCCURED ON API END - HERE IS STATUS CODE: {response.status_code}  ")
            data =  response.json()
            st.write(f"Connection successfull heres info: {data}")
        except requests.exceptions.Timeout:
            st.error("The request timed out. The agent took too long to respond.")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API server. Make sure Uvicorn is running at http://127.0.0.1:8000.")
        except Exception as e:
            # Prevent silent crashing
            st.error(f"An unexpected error occurred: {str(e)}")

#Feature 2: Search only
#A separate text box and button for retrieval without generation.
#When clicked, it must call POST /knowledge/search, and:
#List every result returned, with its title and its score
#Handle the case where the index has not been built yet, this returns a specific status code, not a generic failure
#Handle a normal failure differently from the “index not built” case

with tab2: 
    Query = st.text_area("FEATURE 2-  SEMANTIC SEARCH (knowledge/search )  ")
    Top_K = 3

    if st.button("Click me to search"):

        try:
            #Knowledge/search 
            payload = {"question": Query, "top_k": Top_K}
            response = requests.post(f"{API_URL}/knowledge/search", json=payload, timeout=60)
            if response.status_code !=200:
                st.write(f"ERROR HAS OCCURED ON API END - HERE IS STATUS CODE:  {response.status_code}  ")
            data =  response.json()
            st.write(f"Connection successfull heres the  info: {data}")
        except requests.exceptions.Timeout:
            st.error("The request timed out. API took too long to respond.")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API server. Make sure Uvicorn is running at http://127.0.0.1:8000.")
        except Exception as e:
            # Prevent silent crashing
            st.error(f"An unexpected error occurred: {str(e)}")



#Feature 3: Streaming summary
#A way to pick a firm, by id, and a button to request its summary.
#When clicked, it must call the streaming summary endpoint from Friday, and:
#Display the text as it arrives, not all at once after a wait
#Work for every firm id currently in the data

with tab3: 
    firm_id = st.text_area("FEATURE 3 - STREAM LLM SUMMARY- WRITE FIRM IDNUMBER TO SUMMMARISE IT ")

    if st.button("Click me to stream an LLM summary of something."):

        try:
            #Knowledge/search 
            response = requests.get(
                f"http://127.0.0.1:8000/firms/{firm_id}/summary/stream",
                stream=True
            )
            
            # Simplest way to loop through incoming text chunks:
            if response.status_code == 200:
                            # Generator function yields decoded text chunks to st.write_stream
                            def generate_chunks():
                                for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                                    if chunk:
                                        yield chunk

                            # Streams text progressively in real time into a single paragraph
                            st.write_stream(generate_chunks)
            else:
                st.write(f"ERROR HAS OCCURED ON API END - HERE IS STATUS CODE:  {response.status_code}  ")
        except requests.exceptions.Timeout:
            st.error("The request timed out. API took too long to respond.")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API server. Make sure Uvicorn is running at http://127.0.0.1:8000.")
        except Exception as e:
            # Prevent silent crashing
            st.error(f"An unexpected error occurred: {str(e)}")


with tab4: 
    firm_id = st.text_area("FEATURE 4- Get firm benchmarks/statisticss with firm id ")
    if st.button("Click me to get firm statistics ."):

        try:
            #Knowledge/search 
            response = requests.get(f"http://127.0.0.1:8000/firms/{firm_id}/benchmarks")
            
            # Simplest way to loop through incoming text chunks:
            if response.status_code == 200:
                data = response.json()
                st.write(f"Connection successfull heres info: {data}")
            else:
                st.write(f"ERROR HAS OCCURED ON API END - HERE IS STATUS CODE:  {response.status_code}  ")
        except requests.exceptions.Timeout:
            st.error("The request timed out. API took too long to respond.")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API server. Make sure Uvicorn is running at http://127.0.0.1:8000.")
        except Exception as e:
            # Prevent silent crashing
            st.error(f"An unexpected error occurred: {str(e)}")


