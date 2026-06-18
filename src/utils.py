import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import Neo4jError
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.embeddings import OpenAIEmbeddings

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


########### Neo4j ###########
def init_driver(uri: str, username: str, password: str) -> Optional[Driver]:
    """
    Initialize and return a Neo4j driver connection.
    
    Args:
        uri: Neo4j database URI (e.g., 'neo4j+s://abc123.databases.neo4j.io')
        username: Database username
        password: Database password
        
    Returns:
        Driver object if successful, None otherwise
    """
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        # Test the connection
        with driver.session() as session:
            session.run("RETURN 1")
        logger.info(f"Successfully connected to Neo4j at {uri}")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j driver: {str(e)}")
        return None

def close_driver(driver: Optional[Driver]) -> bool:
    """
    Close the Neo4j driver and all open sessions.
    
    Args:
        driver: Neo4j Driver object
        
    Returns:
        True if successful, False otherwise
    """
    if driver is None:
        logger.warning("Attempted to close None driver")
        return False
    try:
        driver.close()
        logger.info("Neo4j driver closed successfully")
        return True
    except Exception as e:
        logger.error(f"Error closing driver: {str(e)}")
        return False

def clean_up_database(driver: Optional[Driver]) -> bool:
    """
    Delete all nodes, relationships, constraints, and indexes from the database.
    USE WITH CAUTION - This deletes all data!
    
    Args:
        driver: Neo4j Driver object
        
    Returns:
        True if successful, False otherwise
    """
    if driver is None:
        logger.warning("Cannot clean database: driver is None")
        return False
        
    delete_queries = [
        "MATCH (n) DETACH DELETE n",
        "DROP CONSTRAINT skillUnique IF EXISTS",
        "DROP CONSTRAINT titleUnique IF EXISTS",
        "DROP INDEX skillDescription IF EXISTS",
    ]
    
    try:
        with driver.session() as session:
            for query in delete_queries:
                session.run(query)
                logger.info(f"Executed cleanup query: {query[:50]}...")
        logger.info("Database cleanup completed successfully")
        return True
    except Neo4jError as e:
        logger.error(f"Neo4j error during cleanup: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {str(e)}")
        return False

def execute_query(driver: Optional[Driver], query: str) -> List[Dict[str, Any]]:
    """
    Execute a Cypher query and return results.
    
    Args:
        driver: Neo4j Driver object
        query: Cypher query string
        
    Returns:
        List of result dictionaries, empty list if error
    """
    if driver is None:
        logger.error("Cannot execute query: driver is None")
        return []
    
    if not query or not query.strip():
        logger.warning("Empty query provided")
        return []
    
    try:
        with driver.session() as session:
            result = session.run(query)
            data = [dict(record) for record in result]
            logger.debug(f"Query executed successfully. Returned {len(data)} records")
            return data
    except Neo4jError as e:
        logger.error(f"Neo4j error executing query: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error executing query: {str(e)}")
        return []



########### Embeddings & LLMs ###########
def _embedding_function() -> SentenceTransformerEmbeddings:
    """
    Initialize local embedding function using SentenceTransformer.
    
    Returns:
        SentenceTransformerEmbeddings object (384-dimensional vectors)
    """
    embedding_model_name = 'all-MiniLM-L6-v2'
    logger.info(f"Loading embedding model: {embedding_model_name}")
    return SentenceTransformerEmbeddings(model_name=embedding_model_name)

def _embedding_function_openai() -> OpenAIEmbeddings:
    """
    Initialize OpenAI embedding function.
    
    Returns:
        OpenAIEmbeddings object (1536-dimensional vectors)
        
    Note:
        Requires OPENAI_API_KEY environment variable
    """
    logger.info("Loading OpenAI embeddings")
    return OpenAIEmbeddings()


########### Supportive functions ###########
def load_cypher_queries(file_path: str) -> List[str]:
    """
    Load and parse Cypher queries from a file.
    
    Args:
        file_path: Path to the Cypher file
        
    Returns:
        List of query strings (comments and empty lines filtered)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    queries = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # Strip whitespace
                line = line.strip()

                # Check if line is empty or starts with //
                if not line or line.startswith('//'):
                    continue

                # Add the line to the list of queries
                queries.append(line)
        logger.info(f"Loaded {len(queries)} queries from {file_path}")
        return queries
    except FileNotFoundError:
        logger.error(f"Query file not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error loading queries from {file_path}: {str(e)}")
        return []
