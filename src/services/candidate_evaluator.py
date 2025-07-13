import time
from typing import List, Dict, Any, Optional
from fastapi import UploadFile
import logging

from .document_parser import DocumentParser
from .text_chunker import TextChunker
from .vector_store import VectorStore
from .llm_service import LLMService
from ..models.response_models import (
    FitEvaluationResponse, 
    CandidateProfile, 
    RequirementMatch, 
    ComparisonMatrix
)

logger = logging.getLogger(__name__)

class CandidateEvaluator:
    """Main service for candidate fit evaluation"""
    
    def __init__(self):
        self.document_parser = DocumentParser()
        self.text_chunker = TextChunker()
        self.vector_store = VectorStore()
        self.llm_service = LLMService()
    
    async def evaluate_fit(self, resume_file: UploadFile, job_description_file: UploadFile, 
                          candidate_name: Optional[str] = None) -> FitEvaluationResponse:
        """Main evaluation method"""
        start_time = time.time()
        
        try:
            logger.info(f"Starting evaluation for candidate: {candidate_name or 'Unknown'}")
            
            # Step 1: Parse documents
            resume_text = await self.document_parser.parse_document(resume_file)
            job_description_text = await self.document_parser.parse_document(job_description_file)
            
            logger.info("Documents parsed successfully")
            
            # Step 2: Extract candidate profile
            candidate_profile_dict = await self.llm_service.extract_candidate_profile(resume_text)
            candidate_profile = CandidateProfile(**candidate_profile_dict)
            
            logger.info("Candidate profile extracted")
            
            # Step 3: Extract job requirements
            job_requirements_dict = await self.llm_service.extract_job_requirements(job_description_text)
            if (
                isinstance(job_requirements_dict, dict)
                and 'requirements' in job_requirements_dict
                and isinstance(job_requirements_dict['requirements'], list)
                and len(job_requirements_dict['requirements']) > 0
            ):
                job_requirements = job_requirements_dict['requirements']
            else:
                job_requirements = job_requirements_dict

            if not isinstance(job_requirements, list) or len(job_requirements) == 0:
                logger.warning(f"Empty or invalid job requirements provided: {job_requirements}")
            else:
                logger.info(f"Extracted {len(job_requirements)} job requirements")
            
            # Step 4: Chunk resume text
            resume_chunks = self.text_chunker.chunk_text(resume_text)
            
            # Step 5: Add to vector store
            self.vector_store.clear_collections()  # Clear previous data
            self.vector_store.add_resume_chunks(resume_chunks)
            self.vector_store.add_job_requirements(job_requirements)
            
            logger.info("Documents added to vector store")
            
            # Step 6: Evaluate each requirement
            requirement_matches = []
            for requirement in job_requirements:
                # Find relevant resume chunks for this requirement
                similar_chunks = self.vector_store.find_similar_chunks(requirement, n_results=3)
                resume_chunks_for_requirement = [chunk['document'] for chunk in similar_chunks]
                
                # Evaluate the match
                match_result = await self.llm_service.evaluate_requirement_match(
                    requirement, resume_chunks_for_requirement
                )
                
                requirement_match = RequirementMatch(
                    requirement=requirement,
                    match=match_result.get('match', False),
                    confidence=match_result.get('confidence', 0.0),
                    explanation=match_result.get('explanation', 'No explanation available')
                )
                requirement_matches.append(requirement_match)
            
            logger.info("Requirement matches evaluated")
            
            # Step 7: Generate overall evaluation
            evaluation_result = await self.llm_service.generate_fit_evaluation(
                job_requirements, 
                [match.dict() for match in requirement_matches], 
                candidate_profile_dict
            )
            
            # Step 8: Calculate overall match percentage
            matched_requirements = sum(1 for match in requirement_matches if match.match)
            total_requirements = len(requirement_matches)
            overall_match_percentage = (matched_requirements / total_requirements * 100) if total_requirements > 0 else 0
            
            # Step 9: Create comparison matrix as a list of dicts
            comparison_matrix = [
                {"requirement": match.requirement, "match": match.match}
                for match in requirement_matches
            ]
            
            # Step 10: Calculate processing time
            processing_time = time.time() - start_time
            
            # Step 11: Create final response
            response = FitEvaluationResponse(
                fit_score=evaluation_result.get('fit_score', 'Unknown'),
                fit_percentage=evaluation_result.get('fit_percentage', overall_match_percentage),
                candidate_profile=candidate_profile,
                comparison_matrix=comparison_matrix,
                explanation=evaluation_result.get('explanation', 'Evaluation completed'),
                strengths=evaluation_result.get('strengths', []),
                weaknesses=evaluation_result.get('weaknesses', []),
                recommendations=evaluation_result.get('recommendations', []),
                processing_time=processing_time
            )
            
            logger.info(f"Evaluation completed in {processing_time:.2f} seconds")
            return response
            
        except Exception as e:
            logger.error(f"Error during evaluation: {str(e)}")
            raise Exception(f"Evaluation failed: {str(e)}")
    
    async def get_evaluation_summary(self, evaluation: FitEvaluationResponse) -> Dict[str, Any]:
        """Get a summary of the evaluation results"""
        return {
            "candidate_name": "Unknown",  # Could be enhanced to extract from resume
            "fit_score": evaluation.fit_score,
            "fit_percentage": evaluation.fit_percentage,
            "matched_requirements": sum(1 for req in evaluation.comparison_matrix.requirements if req.match),
            "total_requirements": len(evaluation.comparison_matrix.requirements),
            "processing_time": evaluation.processing_time,
            "strengths_count": len(evaluation.strengths),
            "weaknesses_count": len(evaluation.weaknesses)
        } 