"""
Test query Neo4j schema - Natural language to Cypher conversion
"""
import os
import logging
from typing import Optional
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cypher generation prompt template
CYPHER_GENERATION_TEMPLATE = """Task: Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Do not return embedding property from Skill node.

Schema:
{schema}

Examples: Here are a few examples of generated Cypher statements for particular questions:
# What skills mention Oracle?
MATCH (s:Skill) WHERE s.name CONTAINS 'Oracle' RETURN s.name, s.description

# What titles require Python?
MATCH (t:Title)-[:REQUIRES]->(s:Skill) WHERE s.name = 'Python' RETURN DISTINCT t.name

# What skills are required for Data Scientist?
MATCH (t:Title)-[:REQUIRES]->(s:Skill) WHERE t.name = 'Data Scientist' RETURN s.name, s.description

Note: Do not include any text except the generated Cypher statement.

Question: {question}
Cypher query:"""

CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE,
)

def initialize_qa_chain(neo4j_uri: str, username: str, password: str, openai_api_key: str) -> Optional[GraphCypherQAChain]:
    """
    Initialize the GraphCypherQAChain for schema-based question answering.
    
    Args:
        neo4j_uri: Neo4j database URI
        username: Neo4j username
        password: Neo4j password
        openai_api_key: OpenAI API key
        
    Returns:
        GraphCypherQAChain instance or None if initialization fails
    """
    try:
        logger.info("Initializing Neo4j Graph connection...")
        graph = Neo4jGraph(
            url=neo4j_uri,
            username=username,
            password=password
        )
        
        logger.info("Loading graph schema...")
        schema = graph.schema
        logger.debug(f"Schema loaded:\n{schema}")
        
        logger.info("Initializing ChatOpenAI LLM...")
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            api_key=openai_api_key
        )
        
        logger.info("Creating GraphCypherQAChain...")
        qa_chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            cypher_prompt=CYPHER_PROMPT,
            verbose=False,
            validate_cypher=True,
            return_intermediate_steps=True,
        )
        
        logger.info("✓ QA Chain initialized successfully")
        return qa_chain
        
    except Exception as e:
        logger.error(f"Error initializing QA chain: {str(e)}")
        return None


def ask_question(qa_chain: Optional[GraphCypherQAChain], question: str) -> Optional[dict]:
    """
    Ask a question and get an answer from the graph database.
    
    Args:
        qa_chain: Initialized GraphCypherQAChain instance
        question: Natural language question
        
    Returns:
        Dictionary with 'answer' and 'intermediate_steps' or None if error
    """
    if qa_chain is None:
        logger.error("QA chain not initialized")
        return None
    
    try:
        logger.info(f"Processing question: {question}")
        result = qa_chain({
            "query": question
        })
        
        # Extract results
        answer = result.get("result", "No answer found")
        intermediate_steps = result.get("intermediate_steps", [])
        
        logger.info(f"✓ Answer generated")
        return {
            "answer": answer,
            "intermediate_steps": intermediate_steps
        }
        
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        return None


def go():
    """
    Main function to demonstrate schema-based question answering.
    """
    load_dotenv()
    
    # Get configuration
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not all([neo4j_uri, neo4j_username, neo4j_password, openai_api_key]):
        logger.error("Missing required environment variables")
        return
    
    # Initialize QA chain
    qa_chain = initialize_qa_chain(neo4j_uri, neo4j_username, neo4j_password, openai_api_key)
    if qa_chain is None:
        logger.error("Failed to initialize QA chain")
        return
    
    # Example questions
    questions = [
        "What skills are required for a Data Scientist?",
        "What titles require Python?",
        "List all certification skills",
    ]
    
    logger.info("=" * 60)
    logger.info("SCHEMA-BASED QA DEMONSTRATIONS")
    logger.info("=" * 60)
    
    for question in questions:
        logger.info(f"\n❓ Question: {question}")
        result = ask_question(qa_chain, question)
        
        if result:
            logger.info(f"✓ Answer: {result['answer']}")
            if result.get('intermediate_steps'):
                logger.debug(f"  Cypher used: {result['intermediate_steps']}")
        else:
            logger.error(f"Failed to answer: {question}")


if __name__=='__main__':
    go()