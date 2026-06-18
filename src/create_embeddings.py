"""
Create embeddings for skills in the Udemy training project
"""

import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
import pandas as pd
from utils import (
    init_driver,
    close_driver,
    execute_query,
    _embedding_function,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CSV_EMBEDDINGS_URL = 'https://raw.githubusercontent.com/MidnightSkyUniverse/udemyNeo4j/master/data/embeddings.csv'

EMBEDDING_QUERY = """
    MATCH (s:Skill)
    WHERE s.description IS NOT NULL
    RETURN s.name AS name, s.description AS description
"""

def create_skill_embeddings(driver) -> bool:
    """
    Create embeddings for all skills with descriptions.
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("*** Creating skill embeddings ***")
    
    try:
        # Query skills from Neo4j
        logger.info("Fetching skills from database...")
        results = execute_query(driver, EMBEDDING_QUERY)
        
        if not results:
            logger.warning("No skills found with descriptions")
            return False
        
        logger.info(f"Found {len(results)} skills with descriptions")
        df = pd.DataFrame(results)
        
        # Create embeddings using the imported _embedding_function
        logger.info("Initializing embedding model...")
        embedding_model = _embedding_function()
        embeddings = []
        
        logger.info("Generating embeddings...")
        for idx, (_, row) in enumerate(df.iterrows(), 1):
            if idx % 50 == 0:
                logger.info(f"Progress: {idx}/{len(df)} skills processed")
            
            embedding_table = embedding_model.embed_documents([row['description']])
            embeddings.append({
                "Skill": row['name'],
                "Embedding": embedding_table[0],
            })
        
        # Save to CSV
        embeddings_df = pd.DataFrame(embeddings)
        output_path = '../data/embeddings.csv'
        embeddings_df.to_csv(output_path, index=False)
        
        embedding_dim = len(embeddings[0]['Embedding'])
        logger.info(f"✓ Created embeddings for {len(embeddings)} skills")
        logger.info(f"✓ Embedding dimension: {embedding_dim}")
        logger.info(f"✓ Saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating embeddings: {str(e)}")
        return False

def go():
    """
    Main function to orchestrate embedding creation.
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
        success = create_skill_embeddings(driver)
        if success:
            logger.info("✓ Embedding creation completed successfully!")
        return success
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return False
    finally:
        close_driver(driver)

if __name__ == '__main__':
    go()
