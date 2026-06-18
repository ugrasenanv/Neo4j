"""
Semantic search using vector embeddings
"""
import os
import logging
from typing import List, Optional, Dict, Any
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores.neo4j_vector import Neo4jVector
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def initialize_vector_store(neo4j_uri: str, username: str, password: str, 
                           openai_api_key: str) -> Optional[Neo4jVector]:
    """
    Initialize Neo4j Vector Store for semantic search.
    
    Args:
        neo4j_uri: Neo4j database URI
        username: Neo4j username
        password: Neo4j password
        openai_api_key: OpenAI API key
        
    Returns:
        Neo4jVector instance or None if initialization fails
    """
    try:
        logger.info("Initializing OpenAI embeddings...")
        embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        
        logger.info("Connecting to Neo4j vector store...")
        vector_store = Neo4jVector.from_existing_index(
            embedding=embeddings,
            url=neo4j_uri,
            username=username,
            password=password,
            index_name="skillDescription",
            text_node_property="description",
            embedding_node_property="embedding",
        )
        
        logger.info("✓ Vector store initialized successfully")
        return vector_store
        
    except Exception as e:
        logger.error(f"Error initializing vector store: {str(e)}")
        return None


def initialize_qa_chain(vector_store: Optional[Neo4jVector], 
                       openai_api_key: str) -> Optional[RetrievalQA]:
    """
    Initialize RetrievalQA chain for semantic search.
    
    Args:
        vector_store: Neo4jVector instance
        openai_api_key: OpenAI API key
        
    Returns:
        RetrievalQA instance or None if initialization fails
    """
    if vector_store is None:
        logger.error("Vector store is None")
        return None
    
    try:
        logger.info("Initializing ChatOpenAI LLM...")
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            api_key=openai_api_key
        )
        
        logger.info("Creating RetrievalQA chain...")
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True,
            verbose=False,
        )
        
        logger.info("✓ QA chain initialized successfully")
        return qa_chain
        
    except Exception as e:
        logger.error(f"Error initializing QA chain: {str(e)}")
        return None


def search_skills(qa_chain: Optional[RetrievalQA], query: str) -> Optional[Dict[str, Any]]:
    """
    Perform semantic search on skills.
    
    Args:
        qa_chain: Initialized RetrievalQA chain
        query: Natural language search query
        
    Returns:
        Dictionary with 'answer' and 'source_documents' or None if error
    """
    if qa_chain is None:
        logger.error("QA chain not initialized")
        return None
    
    try:
        logger.info(f"Processing semantic query: {query}")
        result = qa_chain({
            "query": query
        })
        
        answer = result.get("result", "No answer found")
        source_documents = result.get("source_documents", [])
        
        logger.info(f"✓ Found {len(source_documents)} relevant skills")
        return {
            "answer": answer,
            "source_documents": source_documents,
            "num_results": len(source_documents)
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return None


def go():
    """
    Main function to demonstrate semantic search.
    """
    load_dotenv()
    
    # Get configuration
    url = os.getenv('NEO4J_URI')
    username = os.getenv('NEO4J_USERNAME')
    password = os.getenv('NEO4J_PASSWORD')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not all([url, username, password, openai_api_key]):
        logger.error("Missing required environment variables")
        logger.error("Required: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, OPENAI_API_KEY")
        return
    
    # Initialize vector store and QA chain
    logger.info("=" * 60)
    logger.info("SEMANTIC VECTOR SEARCH DEMONSTRATION")
    logger.info("=" * 60)
    
    vector_store = initialize_vector_store(url, username, password, openai_api_key)
    if vector_store is None:
        logger.error("Failed to initialize vector store")
        return
    
    qa_chain = initialize_qa_chain(vector_store, openai_api_key)
    if qa_chain is None:
        logger.error("Failed to initialize QA chain")
        return
    
    # Example queries
    queries = [
        "What skills are related to machine learning and AI?",
        "Find skills about cloud computing",
        "Which skills involve database management?",
    ]
    
    for query in queries:
        logger.info(f"\n🔍 Query: {query}")
        result = search_skills(qa_chain, query)
        
        if result:
            logger.info(f"✓ Answer: {result['answer']}")
            if result.get('source_documents'):
                logger.info(f"  Related skills found: {result['num_results']}")
                for i, doc in enumerate(result['source_documents'][:3], 1):
                    logger.info(f"    {i}. {doc.page_content[:80]}...")
        else:
            logger.error(f"Failed to process query: {query}")


if __name__=='__main__':
    go()





if __name__=='__main__':
    go()