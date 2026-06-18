"""
    Create graph database with titles and skills
"""
import os
import logging
from typing import List
from dotenv import load_dotenv
from utils import (
    init_driver,
    close_driver,
    execute_query,
    clean_up_database,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CSV_WITH_TITLES_URL = 'https://raw.githubusercontent.com/MidnightSkyUniverse/udemyNeo4j/master/data/titles_and_skills.csv'
CSV_WITH_SKILLS_URL = 'https://raw.githubusercontent.com/MidnightSkyUniverse/udemyNeo4j/master/data/skills_details.csv'


CREATE_CONSTRAINTS_QUERIES = [
    """CREATE CONSTRAINT skillUnique IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE""",
    """CREATE CONSTRAINT titleUnique IF NOT EXISTS FOR (t:Title) REQUIRE t.name IS UNIQUE""",
    """SHOW ALL CONSTRAINTS""",
]

CREATE_DATA_MODEL_QUERIES = [
    f"""LOAD CSV WITH HEADERS FROM '{CSV_WITH_TITLES_URL}' AS row 
        MERGE (t:Title {{name: row.Title}})""",
    f"""LOAD CSV WITH HEADERS from '{CSV_WITH_SKILLS_URL}' AS row 
        MERGE (s:Skill {{name: row.Skill}}) 
        SET s.id = row.ID, 
            s.description = row.Description, 
            s.category=row.Category""",
    f"""LOAD CSV WITH HEADERS from '{CSV_WITH_TITLES_URL}' AS row 
        MATCH (t:Title {{name: row.Title}}) 
        SET t.skills = split(row.Skills, '|')""",
    """MATCH (t:Title) 
        UNWIND t.skills AS skill 
        MERGE (s:Skill {name: skill}) 
        MERGE (t)-[:REQUIRES]->(s)""",
    """MATCH (t:Title) REMOVE t.skills""",
    """MATCH (s:Skill{category:'Certification'}) 
        SET s:Skill:Certification""",
    """MATCH (s:Skill{category:'SpecializedSkill'}) 
        SET s:Skill:SpecializedSkill""",
    """MATCH (s:Skill) REMOVE s.category""",
    """MATCH (t:Title)-[r:REQUIRES]-(s:Skill)
        RETURN COUNT(DISTINCT t) AS TotalTitles, COUNT(r) AS TotalRequires, COUNT(DISTINCT s) AS TotalSkills""",
]


def create_constraints(driver) -> bool:
    """
    Create uniqueness constraints for Skills and Titles.
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Creating constraints...")
    try:
        for query in CREATE_CONSTRAINTS_QUERIES:
            result = execute_query(driver, query)
            if "CONSTRAINT" in query:
                logger.info(f"Constraint created: {query[:60]}...")
        logger.info("Constraints created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating constraints: {str(e)}")
        return False


def populate_database(driver) -> bool:
    """
    Load titles, skills, and create relationships.
    
    Args:
        driver: Neo4j driver instance
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("Populating database with titles and skills...")
    try:
        for i, query in enumerate(CREATE_DATA_MODEL_QUERIES, 1):
            logger.info(f"Executing query {i}/{len(CREATE_DATA_MODEL_QUERIES)}...")
            result = execute_query(driver, query)
            
            # Log stats from the final query
            if i == len(CREATE_DATA_MODEL_QUERIES):
                if result:
                    stats = result[0]
                    logger.info(f"Graph Statistics: {stats}")
        
        logger.info("Database populated successfully")
        return True
    except Exception as e:
        logger.error(f"Error populating database: {str(e)}")
        return False


def go():
    """
    Main function to orchestrate graph creation.
    
    1. Load environment variables
    2. Initialize Neo4j connection
    3. Clean up existing data
    4. Create constraints
    5. Populate database with titles and skills
    6. Close connection
    """
    load_dotenv()
    
    # Get configuration from environment
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    # Validate configuration
    if not all([neo4j_uri, neo4j_username, neo4j_password]):
        logger.error("Missing required environment variables: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD")
        return False
    
    # Initialize driver
    driver = init_driver(uri=neo4j_uri, username=neo4j_username, password=neo4j_password)
    if driver is None:
        logger.error("Failed to initialize Neo4j driver")
        return False
    
    try:
        # Clean up database
        logger.info("Cleaning up existing data...")
        if not clean_up_database(driver):
            logger.warning("Database cleanup had issues, continuing anyway...")
        
        # Create constraints
        if not create_constraints(driver):
            logger.error("Failed to create constraints")
            return False
        
        # Populate database
        if not populate_database(driver):
            logger.error("Failed to populate database")
            return False
        
        logger.info("✓ Graph creation completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Unexpected error in create_graph: {str(e)}")
        return False
    finally:
        close_driver(driver)




if __name__ == '__main__':
    go()