#!/usr/bin/env python3
"""
CLI tool for testing the AI Candidate Fit Evaluator
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.services.candidate_evaluator import CandidateEvaluator
from src.models.response_models import FitEvaluationResponse
import json

class MockUploadFile:
    """Mock UploadFile for CLI usage"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
    
    async def read(self):
        with open(self.file_path, 'rb') as f:
            return f.read()

async def evaluate_candidate_cli(resume_path: str, job_description_path: str, 
                               candidate_name: Optional[str] = None) -> FitEvaluationResponse:
    """Evaluate candidate fit using CLI"""
    
    # Validate file paths
    if not os.path.exists(resume_path):
        raise FileNotFoundError(f"Resume file not found: {resume_path}")
    
    if not os.path.exists(job_description_path):
        raise FileNotFoundError(f"Job description file not found: {job_description_path}")
    
    # Create mock upload files
    resume_file = MockUploadFile(resume_path)
    job_description_file = MockUploadFile(job_description_path)
    
    # Initialize evaluator
    evaluator = CandidateEvaluator()
    
    # Perform evaluation
    result = await evaluator.evaluate_fit(
        resume_file=resume_file,
        job_description_file=job_description_file,
        candidate_name=candidate_name
    )
    
    return result

def print_evaluation_results(evaluation: FitEvaluationResponse):
    """Print evaluation results in a formatted way"""
    print("\n" + "="*60)
    print("AI CANDIDATE FIT EVALUATION RESULTS")
    print("="*60)
    
    # Overall fit score
    print(f"\n🎯 FIT SCORE: {evaluation.fit_score}")
    print(f"📊 FIT PERCENTAGE: {evaluation.fit_percentage:.1f}%")
    print(f"⏱️  PROCESSING TIME: {evaluation.processing_time:.2f} seconds")
    
    # Candidate profile
    print(f"\n👤 CANDIDATE PROFILE:")
    if evaluation.candidate_profile.education:
        print(f"   📚 Education: {', '.join(evaluation.candidate_profile.education[:3])}")
    if evaluation.candidate_profile.skills:
        print(f"   💻 Skills: {', '.join(evaluation.candidate_profile.skills[:5])}")
    if evaluation.candidate_profile.experience:
        print(f"   💼 Experience: {', '.join(evaluation.candidate_profile.experience[:3])}")
    
    # Requirement matches
    print(f"\n📋 REQUIREMENT MATCHES:")
    for i, req in enumerate(evaluation.comparison_matrix.requirements, 1):
        status = "✅" if req.match else "❌"
        print(f"   {i}. {status} {req.requirement[:50]}...")
        print(f"      Confidence: {req.confidence:.2f}")
        print(f"      Explanation: {req.explanation[:100]}...")
    
    # Strengths and weaknesses
    if evaluation.strengths:
        print(f"\n✅ STRENGTHS:")
        for strength in evaluation.strengths:
            print(f"   • {strength}")
    
    if evaluation.weaknesses:
        print(f"\n❌ WEAKNESSES:")
        for weakness in evaluation.weaknesses:
            print(f"   • {weakness}")
    
    # Recommendations
    if evaluation.recommendations:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in evaluation.recommendations:
            print(f"   • {rec}")
    
    # Explanation
    print(f"\n📝 EXPLANATION:")
    print(f"   {evaluation.explanation}")
    
    print("\n" + "="*60)

def save_results_to_json(evaluation: FitEvaluationResponse, output_path: str):
    """Save evaluation results to JSON file"""
    with open(output_path, 'w') as f:
        json.dump(evaluation.dict(), f, indent=2, default=str)
    print(f"\n💾 Results saved to: {output_path}")

async def main():
    parser = argparse.ArgumentParser(description="AI Candidate Fit Evaluator CLI")
    parser.add_argument("resume", help="Path to resume file (PDF or DOCX)")
    parser.add_argument("job_description", help="Path to job description file (PDF, DOCX, or TXT)")
    parser.add_argument("--candidate-name", "-n", help="Candidate name (optional)")
    parser.add_argument("--output", "-o", help="Output JSON file path (optional)")
    parser.add_argument("--json-only", action="store_true", help="Output only JSON (no formatted text)")
    
    args = parser.parse_args()
    
    try:
        print("🤖 AI Candidate Fit Evaluator")
        print("="*40)
        print(f"📄 Resume: {args.resume}")
        print(f"📋 Job Description: {args.job_description}")
        if args.candidate_name:
            print(f"👤 Candidate: {args.candidate_name}")
        print("\n🔄 Processing...")
        
        # Perform evaluation
        result = await evaluate_candidate_cli(
            resume_path=args.resume,
            job_description_path=args.job_description,
            candidate_name=args.candidate_name
        )
        
        # Output results
        if args.json_only:
            print(json.dumps(result.dict(), indent=2, default=str))
        else:
            print_evaluation_results(result)
        
        # Save to file if requested
        if args.output:
            save_results_to_json(result, args.output)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 