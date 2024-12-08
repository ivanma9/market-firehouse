import csv
import json
import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from pinecone import Pinecone
import requests
from langchain_pinecone import PineconeVectorStore 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    all_divs = soup.find_all(['article', 'h1', 'h2', 'p'])
    combined_text = "".join([div.get_text() for div in all_divs])
    return combined_text
    

class AIModel:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv('GROQ_API_KEY')
            )
    def augment_query(self, contexts, query):
        return "<CONTEXT>\n" + "\n\n-------\n\n".join(contexts[ : 10]) + "\n-------\n</CONTEXT>\n\n\n\nMY QUESTION:\n" + query
    
    def is_article(self, content):
        prompt = f"""
        Determine whether content is an article page or other kind of page
        An article consists of a piece of writing included with others in a newspaper, magazine, or other print or online publication.
        This piece of writing focuses on one title, an author who wrote it, and the article body content.

        This is an example of an article from url = https://www.theguardian.com/media/2024/dec/08/disney-influencer-dominique-brown-dies
        ------------------------

        <Title/Headline>: 
        Disney influencer Dominique Brown dies after medical emergency at event

        <Author>:
        Michael Sainato
        
        <Article content/body>:
        A Disney-inspired social media influencer, Dominique Brown, 34, died after suffering a medical emergency during a lunch in downtown Los Angeles hosted by the pop-culture themed retail merchandiser BoxLunch on 5 December.

Brown co-founded Black Girl Disney in 2018 with her friend Mia Von in response to noticing a lack of representation of Black women among Disney influencers.

According a user on X who claimed she was their mother’s best friend of 10 years, Brown had a severe peanut allergy and was told there were no peanuts in the food at the event, but instantly felt bad and asked to be taken to a hospital. An investigation is ongoing into her cause of death, reported SFGate.

In a statement made to Us Weekly , BoxLunch said: “We are devastated by the passing of Dominique Brown, a beloved member of the BoxLunch Collective, who suffered a medical emergency at an event hosted by BoxLunch Thursday in Los Angeles. Our hearts go out to her family and friends, and we will do everything we can to support them and the members of the BoxLunch Collective and our team during this painful time.”

An unnamed source told Us Weekly that 911 was called immediately and that the company alerted the venue of food allergies of all guests. In Brown’s last Instagram post, she wore a Winnie the Pooh sweater, crediting BoxLunch.

A People Magazine reporter at the event said CPR was immediately administered on Brown at the event. She had most recently attended the Disney premiere of the film Moana 2.

“This didn’t have to happen. 😔…it just didn’t,” wrote a friend of Brown’s on Threads posting photos of them together.

Brown’s brother in a comment on her final Instagram post wrote: “I wanted to take a moment to say thank you to her social media fam for showing her so much love and light. Disney did bring her joy, but it was unparalleled that she found a community who loved her and Disney as much as she did. I will miss my sister and best friend and that infectious smile she always had. Thank you, truly, from the bottom of my heart.”        
        ------------------------        
        
        Respond `True` if content is an article. Respond `False` if content is not an article. Please make sure that the answer is strictly `True` or `False`. 

        Article: {content}
        """
        llm_response = self.client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response = llm_response.choices[0].message.content
        if (response.lower() == "true"):
            return True
        print("Falso", response)
        return False
    
    def ask(self, content):

        prompt = f"""
        Extract the following information from the article below:
        - Title
        - Author
        - Publisher
        - Date
        - Body (Main content)
        - Related sector (e.g., politics, technology, health, etc.)

        Article {content}
        
        
        Return the results in the following format:
        Title: <Title>
        Author: <Author>
        Publisher: <Publisher>
        Date: <Date>
        Body: <Body>
        Sector: <Sector>
        """

        llm_response = self.client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                # {"role": "system", "content": prompt},
                {"role": "user", "content": prompt}
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
        print(url)
        article_data = self.get_article_data(url)
        print(article_data)
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
        html_content = response_dict['html_content']
        with open('res.html', 'w') as f:
            f.write(html_content)
        content = extract_text_from_html(html_content)
        # print(content)
        soup = BeautifulSoup(html_content, 'html.parser')
        print(len(content))
        # article_tags = has_author_info(soup)
        ai = AIModel()
        if ai.is_article(content):
            print("ASKING")
            response = ai.ask(content)
        else:
            print("NOT an article")
        print("Finished ai")
        
        # embedding.process_article(content, url)
        # embedding.createRag()
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