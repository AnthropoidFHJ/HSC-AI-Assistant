from flask import Flask, request, Response
from src.chunker import download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_groq import ChatGroq
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from src.prompt import system_prompt
import os
from collections import deque
import json

app = Flask(__name__)

load_dotenv()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

embeddings = download_hugging_face_embeddings()
index_name = "hsc-ai-assistant"

docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = docsearch.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 7}
)

llm = ChatGroq(
    temperature=0.5,
    model_name="llama3-70b-8192"
)

conversation_history = deque(maxlen=10)

def format_response(qa_pairs):
    return "\n".join(json.dumps(qa, ensure_ascii=False) for qa in qa_pairs)

@app.route("/")
def home():
    return "Server is running. please use the /chat endpoint to interact."

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()
    
    if not user_input:
        return Response(
            json.dumps({"error": "Message is required"}, ensure_ascii=False),
            status=400,
            mimetype='application/json'
        )
    
    try:
        recent_questions = [qa["Question"] for qa in conversation_history]
        formatted_system_prompt = system_prompt.format(
            recent_inputs="\n".join(recent_questions),
            context="{context}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", formatted_system_prompt),
            ("human", "{input}")
        ])

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        response = rag_chain.invoke({"input": user_input})
        bot_response = response["answer"]

        qa_pair = {
            "Question": user_input,
            "Answer": bot_response
        }
        conversation_history.append(qa_pair)

        return Response(
            format_response(conversation_history),
            mimetype='application/json'
        )

    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            status=500,
            mimetype='application/json'
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7654, debug=True)