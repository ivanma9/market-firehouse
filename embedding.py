import csv
import json
import os
from urllib.parse import urlparse
from pinecone import Pinecone
import requests
from langchain_pinecone import PineconeVectorStore 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv


class AIModel:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv('PINECONE_API_KEY')
            )
    def augment_query(self, contexts, query):
        return "<CONTEXT>\n" + "\n\n-------\n\n".join(contexts[ : 10]) + "\n-------\n</CONTEXT>\n\n\n\nMY QUESTION:\n" + query
    def ask(self, query):

        system_prompt = f"""You are an expert at providing decoding markdown content into important information. Please answer my question provided.
        """

        llm_response = self.client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )

        response = llm_response.choices[0].message.content
        print(response)
        return response

class Embedding:
    def __init__(self):
        load_dotenv()
        
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
        os.environ['PINECONE_API_KEY'] = self.pinecone_api_key

        self.index_name = "news"
        self.namespace = "news-articles"

        self.hf_embeddings = HuggingFaceEmbeddings()
        # self.vectorstore = PineconeVectorStore(
        #     index_name=self.index_name, 
        #     embedding=self.hf_embeddings)
    
    def process_article(self, content, url):
        print(f"Processing article")
        article_data = self.get_article_data(url)

        self.vectorstore = PineconeVectorStore.from_documents(
            documents=[Document(page_content=content, metadata=article_data)],
            embedding=self.hf_embeddings,
            index_name=self.index_name,
            namespace=self.namespace
        )
    def get_article_data(self, url):
        properties = {
            'Url': url,
        }
        return properties

    def createRag(self):
        # Initialize Pinecone
        pc = Pinecone(api_key=self.pinecone_api_key)

        # Connect to your Pinecone index
        pinecone_index = pc.Index(self.index_name)
        query = "What is the author of this article?"
        raw_query_embedding = get_huggingface_embeddings(query)
        top_matches = pinecone_index.query(vector=raw_query_embedding.tolist(), top_k=1, include_metadata=True, namespace=self.namespace)


def main():
    embedding = Embedding()
    input_file = 'news.csv'
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        datasets = [(row['url'], row['content']) for row in reader]
    url, dataset_id = datasets[0]

    api_url = "https://dataset.olostep.com/olostep-p2p-dataset-API"
    headers = {"Authorization": "Bearer olostep_api_test_001201"}
    params = {
        "retrieveMarkdown": "true",  # Changed to get markdown
        "retrieveHtml": "true",
        "datasetId": dataset_id
    }

    try:
        response = requests.get(api_url, headers=headers, params=params)
        response.raise_for_status()
        response_dict = json.loads(response.text)
        content = response_dict['markdown_content']
        embedding.process_article(content, url)
        embedding.createRag()
    except requests.exceptions.RequestException as e:
        print('Error request: ' , e)
    

def get_huggingface_embeddings(self,text, model_name="sentence-transformers/all-mpnet-base-v2"):
    """
    Generates embeddings for the given text using a specified Hugging Face model.

    Args:
        text (str): The input text to generate embeddings for.
        model_name (str): The name of the Hugging Face model to use.
                        Defaults to "sentence-transformers/all-mpnet-base-v2".

    Returns:
        np.ndarray: The generated embeddings as a NumPy array.
    """
    model = SentenceTransformer(model_name)
    return model.encode(text)

if __name__ == "__main__":
    print("Starting dataset content retrieval")
    main()