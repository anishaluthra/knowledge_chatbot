import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from chromadb.config import Settings
import ollama
import uuid
from datetime import datetime
from typing import List, Optional
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "default"

class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = "default"

class KnowledgeExtraction(BaseModel):
    topic: str
    content: str
    keywords: List[str]
    importance_score: int  # 1-10

app = FastAPI(title="Local Knowledge Chatbot")

# Add CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Changed to False when using wildcard
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./knowledge_db")

# Create collections
conversations_collection = chroma_client.get_or_create_collection(
    name="conversations",
    metadata={"description": "Raw conversation data"}
)

knowledge_collection = chroma_client.get_or_create_collection(
    name="knowledge_base",
    metadata={"description": "Extracted structured knowledge"}
)

class KnowledgeBot:
    def __init__(self):
        self.model_name = "llama3.1"  # Change to your preferred model
        
    async def extract_knowledge(self, conversation_text: str) -> List[KnowledgeExtraction]:
        """Extract structured knowledge from conversation text"""
        
        prompt = f"""
        Analyze the following conversation and extract key knowledge points.
        For each piece of knowledge, provide:
        1. A clear topic/subject
        2. The actual content/information
        3. Relevant keywords for searchability
        4. Importance score (1-10, where 10 is most important)
        
        Only extract factual information, personal insights, or actionable knowledge.
        Ignore casual conversation, greetings, or filler.
        
        Conversation:
        {conversation_text}
        
        Format your response as a JSON array of objects with fields: topic, content, keywords, importance_score
        """
        
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt
            )
            
            # Parse the response (you might want to add better JSON parsing)
            response_text = response['response']
            
            # Simple extraction - in production, you'd want more robust parsing
            knowledge_items = self._parse_knowledge_response(response_text)
            return knowledge_items
            
        except Exception as e:
            logger.exception("Error extracting knowledge")
            return []
    
    def _parse_knowledge_response(self, response_text: str) -> List[KnowledgeExtraction]:
        """Parse LLM response into structured knowledge"""
        import json

        knowledge_items = []

        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", response_text).strip()

        # Find the first JSON array in the response
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if not match:
            logger.warning("No JSON array found in LLM response")
            return knowledge_items

        try:
            items = json.loads(match.group())
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse JSON from LLM response: %s", e)
            return knowledge_items

        for item in items:
            try:
                knowledge_items.append(KnowledgeExtraction(
                    topic=item.get("topic", "Unknown"),
                    content=item.get("content", ""),
                    keywords=item.get("keywords", []),
                    importance_score=int(item.get("importance_score", 5)),
                ))
            except Exception as e:
                logger.warning("Skipping malformed knowledge item: %s", e)

        return knowledge_items
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text - simplified version"""
        words = re.findall(r'\b\w{4,}\b', text.lower())
        return list(set(words))[:5]  # Return top 5 unique words
    
    async def query_knowledge(self, query: str, n_results: int = 5) -> str:
        """Query the knowledge base using RAG"""
        
        try:
            # Search for relevant knowledge
            results = knowledge_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if not results['documents'][0]:
                return "I don't have any relevant information about that topic yet."
            
            # Combine retrieved documents
            context = "\n".join(results['documents'][0])
            
            # Generate response using RAG
            rag_prompt = f"""
            Based on the following knowledge from previous conversations, answer the user's question.
            If the information isn't available in the context, say so clearly.
            
            Context:
            {context}
            
            User Question: {query}
            
            Answer:
            """
            
            response = ollama.generate(
                model=self.model_name,
                prompt=rag_prompt
            )
            
            return response['response']
            
        except Exception as e:
            logger.exception("Error querying knowledge base")
            return f"Error querying knowledge base: {e}"

# Initialize the bot
bot = KnowledgeBot()

@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    """Process a chat message and extract knowledge"""
    
    try:
        # Store the raw conversation
        conversation_id = str(uuid.uuid4())
        
        conversations_collection.add(
            documents=[message.message],
            metadatas=[{
                "user_id": message.user_id,
                "timestamp": datetime.now().isoformat(),
                "conversation_id": conversation_id
            }],
            ids=[conversation_id]
        )
        
        # Extract knowledge from the message
        knowledge_items = await bot.extract_knowledge(message.message)
        
        # Store extracted knowledge
        for i, knowledge in enumerate(knowledge_items):
            knowledge_id = f"{conversation_id}_knowledge_{i}"
            
            knowledge_collection.add(
                documents=[knowledge.content],
                metadatas=[{
                    "topic": knowledge.topic,
                    "keywords": ",".join(knowledge.keywords),
                    "importance_score": knowledge.importance_score,
                    "user_id": message.user_id,
                    "timestamp": datetime.now().isoformat(),
                    "source_conversation": conversation_id
                }],
                ids=[knowledge_id]
            )
        
        return {
            "status": "success",
            "message": "Knowledge stored successfully",
            "knowledge_items_extracted": len(knowledge_items),
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    """Query the knowledge base"""
    
    try:
        response = await bot.query_knowledge(request.query)
        
        return {
            "status": "success",
            "query": request.query,
            "response": response
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get database statistics"""
    
    try:
        conv_count = conversations_collection.count()
        knowledge_count = knowledge_collection.count()
        
        return {
            "total_conversations": conv_count,
            "total_knowledge_items": knowledge_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search_knowledge(query: str, limit: int = 10):
    """Search knowledge base directly"""
    
    try:
        results = knowledge_collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        return {
            "query": query,
            "results": {
                "documents": results['documents'][0] if results['documents'] else [],
                "metadatas": results['metadatas'][0] if results['metadatas'] else []
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/debug")
async def debug_info():
    """Debug endpoint to see what's stored"""
    try:
        # Get all conversations
        conv_results = conversations_collection.get()
        
        # Get all knowledge
        knowledge_results = knowledge_collection.get()
        
        return {
            "conversations": {
                "count": len(conv_results['documents']) if conv_results['documents'] else 0,
                "documents": conv_results['documents'][:3] if conv_results['documents'] else [],  # Show first 3
                "metadatas": conv_results['metadatas'][:3] if conv_results['metadatas'] else []
            },
            "knowledge": {
                "count": len(knowledge_results['documents']) if knowledge_results['documents'] else 0,
                "documents": knowledge_results['documents'][:3] if knowledge_results['documents'] else [],  # Show first 3
                "metadatas": knowledge_results['metadatas'][:3] if knowledge_results['metadatas'] else []
            }
        }
    except Exception as e:
        logger.exception("Error in debug endpoint")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

