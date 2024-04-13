import streamlit as st
import google.generativeai as genai
import os
import time
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings,GoogleGenerativeAI,ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from PIL import Image
import json
 
 
st.set_page_config(
    page_title="ChatCUD",
    page_icon="💬",
    )
 
gemini_config = {'temperature': 0.7, 'top_p': 1, 'top_k': 1, 'max_output_tokens': 2048}
page_config = {
    st.markdown(
    "<h1 style='text-align: center; color: #b22222; font-family: Arial, sans-serif; background-color: #292f4598;'>chatCUD 💬</h1>",
    unsafe_allow_html=True
    ),
    st.markdown("<h4 style='text-align: center; color: white; font-size: 20px; animation: bounce-and-pulse 60s infinite;'>Your CUD AI Assistant</h4>", unsafe_allow_html=True),
}
 
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model=genai.GenerativeModel(model_name="models/gemini-pro",generation_config=gemini_config)
 
#Extracting and Splitting PDF
def extract_text_and_get_chunks(pdf_file):
 
   
       
            loader = PyPDFLoader(pdf_file.name)
            all_Text = loader.load()
       
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len, add_start_index=True)
            chunks=text_splitter.split_documents(all_Text)
            return chunks
 
 
 
#Embedding and storing the pdf Local
def get_embeddings_and_store_pdf(chunk_text):
    if not isinstance(chunk_text, list):
        raise ValueError("Text must be a list of text documents")
    try:
        embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        create_embedding = FAISS.from_documents(chunk_text, embedding=embedding_model)
        create_embedding.save_local("embeddings_index")
    except Exception as e:
        st.error(f"Error creating embeddings: {e}")
 
#Generating user response for the pdf
def get_generated_user_input(user_question):
    # Initialize Google Generative AI Embeddings with the specified model
    text_embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
   
    # Load stored embeddings using FAISS, allowing dangerous deserialization
    stored_embeddings = FAISS.load_local("embeddings_index", text_embedding, allow_dangerous_deserialization=True)
   
    # Search for similarity between user question and stored embeddings
    check_pdf_similarity = stored_embeddings.similarity_search(user_question)
    context_text = "\n\n--\n\n".join([doc.page_content for doc in check_pdf_similarity])
 
    # Generate a prompt for answering the query based on the context and user question
    prompt = f"Answer this query based on the Context: \n{context_text}?\nQuestion: \n{user_question}"
 
    # Send the prompt as a message in the chat history and retrieve the response
    pdf_response = st.session_state.chat_history.send_message(prompt)
    # Return the response
    return pdf_response
 
#Clearing Chat
def clear_chat_convo():
    st.session_state.chat_history.history=[]
 
#Changing Role Names/Icons
def role_name(role):    
    if role == "model":  
        return "bot.png"  
    elif role=='user':
        return 'user.png'
    else:
        return None
 
#Text Splits
def stream(response):
    for word in response.text.split(" "):
        yield word + " "
        time.sleep(0.04)
 
#Extracts the user question from pdf prompt in get_generated_user_input()
def extract_user_question(prompt_response):
    # Iterate through the parts of the prompt response in reverse order
    for part in reversed(prompt_response):
        # Check if the part contains the keyword "Question:"
        if "Question:" in part.text:
            # Split the text after "Question:" and return the extracted user question
            return part.text.split("Question:")[1].strip()
 
def main():
    # Opening CSS File
    # Read the contents of 'dark.css' file and embed it in the HTML style tag
    with open('dark.css') as f:
        # Apply the CSS style to the page
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    with st.sidebar:
       
            pdf_file = st.file_uploader("Choose a PDF file (optional)", type="pdf",accept_multiple_files=False)
            if pdf_file:
               
                   
                    with open(pdf_file.name, mode='wb') as w:
                        w.write(pdf_file.getvalue())
           
                    if st.sidebar.button("Process") and pdf_file is not None:
                        with st.spinner("Processing..."):
                            texts = extract_text_and_get_chunks(pdf_file)
                            get_embeddings_and_store_pdf(texts)
                       
                       
                       
                        st.success("Success")
    st.sidebar.button("Click to Clear Chat History", on_click=clear_chat_convo)
 
    # Start a conversation using the model, initially with an empty history
    start_conversation = model.start_chat(history=[])
 
    # Check if 'chat_history' is not already in the session state
    if "chat_history" not in st.session_state:
        # If not, initialize 'chat_history' with the start of the conversation
        st.session_state.chat_history = start_conversation
   
    # Iterate over each message in the chat history
    for message in st.session_state.chat_history.history:
        # Get the role name of the message and fetch corresponding avatar if available
        avatar = role_name(message.role)
        # Check if avatar exists
        if avatar:
            # Display the message with the role's avatar
            with st.chat_message(message.role, avatar=avatar):
                # Check if the message has 'content' in its parts
                if "content" in message.parts[0].text:
                    # Extract the user's question from the message parts (if available)
                    user_question = extract_user_question(message.parts)
                    # Check if a user question is extracted
                    if user_question:
                        # Display the user question using Markdown
                        st.markdown(user_question)
                else:  
                    # If 'content' is not found in the parts, display the message text using Markdown
                    st.markdown(message.parts[0].text)
           
    # Get user input from the chat interface
    user_question = st.chat_input("Ask ChatCUD...")
 
    # Processing user input
    if user_question is not None and user_question.strip() != "":
        # Display the user input message with user avatar
        with st.chat_message("user", avatar="user.png"):
            st.write(user_question)
 
            # Pre-load PDFs and extract text from them
           
       
        # Get generated responses for the user input
        responses = get_generated_user_input(user_question)
       
        # If responses are generated
        if responses:
            # Display the responses with assistant's avatar
            with st.chat_message("assistant", avatar="bot.png"):
                # Write the responses to the chat
                st.write_stream(stream(responses))
 
    # Add a button in the sidebar to clear the chat history
   
 
 
if __name__ == "__main__":
    main()
