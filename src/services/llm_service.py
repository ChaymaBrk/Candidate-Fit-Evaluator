import os
from typing import List, Dict, Any, Optional
import logging
import json
from dotenv import load_dotenv
from groq import Groq
import asyncio
load_dotenv()

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM-based evaluation and reasoning using Groq"""
    
    def __init__(self, groq_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"):
        self.groq_model = groq_model
        self.groq_client = None
        
        groq_api_key = os.getenv("CROQ_API_KEY")
        if groq_api_key:
            self.groq_client = Groq(api_key=groq_api_key)
            logger.info(f"Groq client initialized with model: {groq_model}")
        else:
            logger.warning("Groq API key not found.")
    
    async def _call_groq_model(self, prompt: str, system_prompt: str = None) -> str:
        """Call Groq model with the specified prompt"""
        try:
            if not self.groq_client:
                raise Exception("Groq client not initialized")
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            completion = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling Groq model: {str(e)}")
            raise
    
    async def extract_job_requirements(self, job_description: str) -> List[str]:
        """Extract job requirements from job description"""
        if not self.groq_client:
            return "error : groq client is not intialized"
        
        try:
            prompt = f"""
            Extract specific job requirements from the following job description. 
            Return only the requirements as a JSON array of strings.
            
            Job Description:
            {job_description}
            
            Requirements:
            """
            
            system_prompt = "You are a job requirements extractor. Return only valid JSON arrays with a key 'requirements'."
           
            try:
                content = await self._call_groq_model(prompt, system_prompt)
            except:
                raise
            
            requirements = json.loads(content)
            print(requirements)
            return requirements
            
        except Exception as e:
            logger.error(f"Error extracting requirements: {str(e)}")
            return e
    
    async def extract_candidate_profile(self, resume_text: str) -> Dict[str, List[str]]:
        """Extract candidate profile information from resume"""
        if not self.groq_client:
            return "error: groq is not intialized"
        
        try:
            prompt = f"""
            Extract candidate information from the following resume. 
            Return the information as a JSON object with these keys: education, skills, experience, certifications, languages.
            Each value should be an array of strings.
            
            Resume:
            {resume_text}
            
            Profile:
            """
            
            system_prompt = "You are a resume parser. Return only valid JSON objects."
            
            try:
                content = await self._call_groq_model(prompt, system_prompt)
            except:
                raise
            
            
            profile = json.loads(content)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error extracting profile: {str(e)}")
            return e
    
    async def evaluate_requirement_match(self, requirement: str, resume_chunks: List[str]) -> Dict[str, Any]:
        """Evaluate if a requirement is matched by resume content"""
        if not self.groq_client:
            return "error: groq client is not intialized"
        
        try:
            resume_context = "\n".join(resume_chunks)  # Use top 3 chunks
            
            prompt = f"""
            Evaluate if the candidate's resume matches the following job requirement.
            Consider the resume content and provide a detailed analysis.
            
            Job Requirement: {requirement}
            
            Resume Content:
            {resume_context}
            
            Return a JSON object with these fields:
            - match: boolean (true if requirement is met)
            - confidence: float (0.0 to 1.0)
            - explanation: string (detailed reasoning)
            """
            
            system_prompt = "You are a job requirement evaluator. Return only valid JSON objects."
           
            try:
                content = await self._call_groq_model(prompt, system_prompt)
            except:
                raise
            
            evaluation = json.loads(content)
            print(evaluation)
            return evaluation 
        
        except Exception as e:
            logger.error(f"Error evaluating requirement: {str(e)}")
            return e
    
    async def generate_fit_evaluation(self, requirements: List[str], matches: List[Dict[str, Any]], 
                                    candidate_profile: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate overall fit evaluation"""
        if not self.groq_client:
            return "error: groq client is not intialized"
        
        try:
            match_summary = "\n".join([
                f"Requirement: {req}\nMatch: {match['match']}\nExplanation: {match['explanation']}\n"
                for req, match in zip(requirements, matches)
            ])
            
            prompt = f"""
            Based on the following information, provide a comprehensive fit evaluation:
            
            Candidate Profile:
            {json.dumps(candidate_profile, indent=2)}
            
            Requirement Matches:
            {match_summary}
            
            Return a JSON object with these fields:
            - fit_score: string (Strong Fit, Moderate Fit, Weak Fit, or Poor Fit)
            - fit_percentage: float (0.0 to 100.0)
            - explanation: string (detailed reasoning)
            - strengths: array of strings
            - weaknesses: array of strings
            - recommendations: array of strings
            """
            
            system_prompt = "You are a candidate fit evaluator. Return only valid JSON objects."
          
            try:
                content = await self._call_groq_model(prompt, system_prompt)
            except:
                raise
            
            evaluation = json.loads(content)
            return evaluation
        
        except Exception as e:
            logger.error(f"Error generating evaluation: {str(e)}")
            return e
  
    
    
   