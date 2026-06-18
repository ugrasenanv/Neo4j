"""
Udemy Neo4j Training Project - Main Orchestration Script

This script orchestrates the complete pipeline:
1. create_graph: Build the knowledge graph
2. create_embeddings: Generate vector embeddings
3. create_search_index: Create vector index in Neo4j
4. neo4j_qa: Query via natural language with LLM (schema-based)
5. vector_search: Semantic search using embeddings

Note: The steps are commented by default for safety.
Uncomment the steps you want to execute.

PREREQUISITES:
- .env file with NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, OPENAI_API_KEY
- Neo4j database running and accessible
- OpenAI API key (for LLM features)
"""

import logging
import sys

# Import all pipeline modules
import create_graph
import create_embeddings
import create_search_index
import neo4j_qa
import vector_search

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the steps to be executed
# IMPORTANT: Uncomment the steps you want to execute in order
steps = [
    # Step 1: Create the graph database with titles and skills
    # Uncomment to create/recreate the knowledge graph from CSV data
    # 'create_graph',

    # Step 2: Create embeddings for skills
    # Uncomment to generate vector embeddings for all skills
    # Only run after 'create_graph' has completed successfully
    # 'create_embeddings',

    # Step 3: Create vector search index
    # Uncomment to create vector index for semantic search
    # Only run after 'create_embeddings' has completed successfully
    # 'create_search_index',

    # Step 4: Schema-based QA (Natural language to Cypher)
    # Uncomment to query using natural language converted to Cypher
    # Requires: create_graph, OPENAI_API_KEY
    # 'neo4j_qa',

    # Step 5: Semantic search using vector embeddings
    # Uncomment to perform semantic similarity search
    # Requires: create_graph, create_embeddings, create_search_index, OPENAI_API_KEY
    # 'vector_search',
]


def execute_steps(steps_to_execute: list) -> dict:
    """
    Execute the specified pipeline steps.
    
    Args:
        steps_to_execute: List of step names to execute
        
    Returns:
        Dictionary with execution results for each step
    """
    results = {
        'total_steps': len(steps_to_execute),
        'completed': 0,
        'failed': 0,
        'step_results': {}
    }
    
    if not steps_to_execute:
        logger.warning("No steps to execute. Please uncomment desired steps in the 'steps' list.")
        return results
    
    logger.info("=" * 70)
    logger.info(f"Starting pipeline execution with {len(steps_to_execute)} step(s)")
    logger.info("=" * 70)
    
    for step in steps_to_execute:
        logger.info(f"\n▶ Executing step: {step}")
        logger.info("-" * 70)
        
        try:
            if step == 'create_graph':
                success = create_graph.go()
                step_name = "Create Graph Database"
                
            elif step == 'create_embeddings':
                success = create_embeddings.go()
                step_name = "Create Embeddings"
                
            elif step == 'create_search_index':
                success = create_search_index.go()
                step_name = "Create Vector Search Index"
                
            elif step == 'neo4j_qa':
                neo4j_qa.go()
                step_name = "Neo4j Schema-Based QA"
                success = True  # go() doesn't return value
                
            elif step == 'vector_search':
                vector_search.go()
                step_name = "Vector Search"
                success = True  # go() doesn't return value
                
            else:
                logger.warning(f"Unknown step: {step}")
                success = False
                step_name = step
            
            # Record results
            if success:
                logger.info(f"✓ {step_name} completed successfully")
                results['completed'] += 1
                results['step_results'][step] = 'SUCCESS'
            else:
                logger.error(f"✗ {step_name} failed")
                results['failed'] += 1
                results['step_results'][step] = 'FAILED'
                # Don't stop on failure, continue with other steps
                
        except Exception as e:
            logger.error(f"✗ Unexpected error in {step}: {str(e)}")
            results['failed'] += 1
            results['step_results'][step] = f'ERROR: {str(e)}'
    
    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("PIPELINE EXECUTION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total steps: {results['total_steps']}")
    logger.info(f"Completed: {results['completed']}")
    logger.info(f"Failed: {results['failed']}")
    
    for step, result in results['step_results'].items():
        status_icon = "✓" if result == 'SUCCESS' else "✗"
        logger.info(f"{status_icon} {step}: {result}")
    
    return results


def print_instructions():
    """Print helpful instructions for running the pipeline."""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║           Neo4j Graph Database with Vector Search                 ║
║                  & LLM Integration Pipeline                       ║
╚════════════════════════════════════════════════════════════════════╝

QUICK START GUIDE:

1. Setup Environment:
   - Create a .env file with required variables:
     NEO4J_URI=<your-neo4j-uri>
     NEO4J_USERNAME=<username>
     NEO4J_PASSWORD=<password>
     OPENAI_API_KEY=<your-openai-key>  # Optional for LLM features

2. Enable Pipeline Steps:
   - Edit main.py and uncomment steps in the 'steps' list
   - Recommended order:
     a) create_graph (builds database)
     b) create_embeddings (generates vectors)
     c) create_search_index (creates vector index)
     d) neo4j_qa (schema-based Q&A)
     e) vector_search (semantic search)

3. Run the Pipeline:
   python src/main.py

PIPELINE STEPS:

create_graph:
  - Loads titles and skills from CSV
  - Creates Title and Skill nodes
  - Establishes REQUIRES relationships
  - Duration: ~5-10 minutes (depends on data size)

create_embeddings:
  - Generates embeddings for skill descriptions
  - Uses SentenceTransformer (384-dim vectors)
  - Saves to embeddings.csv
  - Duration: ~2-5 minutes

create_search_index:
  - Creates vector index in Neo4j
  - Enables semantic search capabilities
  - Uses cosine similarity
  - Duration: ~1-2 minutes

neo4j_qa:
  - Natural language to Cypher conversion
  - Uses LangChain + OpenAI
  - Answers questions about graph structure
  - Example: "What skills require Python?"

vector_search:
  - Semantic similarity search
  - Uses vector embeddings
  - Answers conceptual questions
  - Example: "Find skills related to machine learning"

TROUBLESHOOTING:

Issue: "OPENAI_API_KEY not found"
Solution: Add OPENAI_API_KEY to .env file (optional for some steps)

Issue: "Neo4j connection failed"
Solution: Check NEO4J_URI, username, password in .env file

Issue: "Index already exists"
Solution: This is normal - the system will use the existing index

For more details, see FILE_EXPLANATIONS.md
    """)


if __name__ == '__main__':
    # Print instructions if running interactively
    if len(sys.argv) == 1:
        print_instructions()
    
    execute_steps(steps)
