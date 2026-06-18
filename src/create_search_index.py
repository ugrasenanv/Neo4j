"""
Create vector search index for skills in the Udemy training project
"""

import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from utils import (
    init_driver,
    close_driver,
    execute_query,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CSV_EMBEDDINGS_URL = 'https://raw.githubusercontent.com/MidnightSkyUniverse/udemyNeo4j/master/data/embeddings.csv'

INSERT_EMBEDDINGS_QUERY = f"""
    LOAD CSV WITH HEADERS FROM '{CSV_EMBEDDINGS_URL}' AS row
    MATCH (s:Skill {{name: row.Skill}})
    CALL db.create.setNodeVectorProperty(s, 'embedding', apoc.convert.fromJsonList(row.Embedding))
    RETURN count(*) as embeddingsAdded
"""

CREATE_INDEX_QUERY = """
    CALL db.index.vector.createNodeIndex(
        'skillDescription',
        'Skill',
        'embedding',
        384,
        'cosine'
    )
"""

CHECK_INDEX_QUERY = """SHOW INDEXES YIELD id, name, type WHERE type='VECTOR' """


def insert_embeddings(driver) -> bool:
    """
    Load embeddings from CSV and add to Skill nodes.
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Loading embeddings from CSV...")
    try:
        result = execute_query(driver, INSERT_EMBEDDINGS_QUERY)
        if result:
            embeddings_added = result[0].get('embeddingsAdded', 0)
            logger.info(f"✓ Added {embeddings_added} embeddings to skill nodes")
            return True
        else:
            logger.warning("No embeddings were added")
            return False
    except Exception as e:
        logger.error(f"Error inserting embeddings: {str(e)}")
        return False


def create_vector_index(driver) -> bool:
    """
    Create vector index for semantic search.
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Creating vector index...")
    try:
        result = execute_query(driver, CREATE_INDEX_QUERY)
        logger.info("✓ Vector index 'skillDescription' created successfully")
        return True
    except Exception as e:
        # Index might already exist, which is not an error
        if "already exists" in str(e).lower():
            logger.info("Vector index already exists")
            return True
        logger.error(f"Error creating vector index: {str(e)}")
        return False


def verify_index(driver) -> bool:
    """
    Verify that vector index exists.
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        True if index exists, False otherwise
    """
    logger.info("Checking vector indexes...")
    try:
        result = execute_query(driver, CHECK_INDEX_QUERY)
        if result:
            logger.info(f"✓ Found {len(result)} vector index(es)")
            for idx in result:
                logger.info(f"  - Index: {idx.get('name')}")
            return True
        else:
            logger.warning("No vector indexes found")
            return False
    except Exception as e:
        logger.error(f"Error checking indexes: {str(e)}")
        return False


def go():
    """
    Main function to orchestrate vector index creation.
    
    1. Load environment variables
    2. Initialize Neo4j connection
    3. Insert embeddings into database
    4. Create vector index
    5. Verify index creation
    6. Close connection
    """
    load_dotenv()
    
    # Get configuration from environment
    url = os.getenv('NEO4J_URI')
    username = os.getenv('NEO4J_USERNAME')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not all([url, username, password]):
        logger.error("Missing required environment variables")
        return False
    
    driver = init_driver(uri=url, username=username, password=password)
    if driver is None:
        return False
    
    try:
        # Insert embeddings
        if not insert_embeddings(driver):
            logger.error("Failed to insert embeddings")
            return False
        
        # Create vector index
        if not create_vector_index(driver):
            logger.error("Failed to create vector index")
            return False
        
        # Verify index
        if not verify_index(driver):
            logger.warning("Could not verify vector index")
        
        logger.info("✓ Vector search index creation completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False
    finally:
        close_driver(driver)



if __name__ == '__main__':
    go()