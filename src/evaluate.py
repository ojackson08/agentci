import json
import os
import boto3
from typing import Dict, Any

bedrock = boto3.client('bedrock-runtime')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AgentCI Evaluator: Uses Amazon Bedrock (Claude 3) as an LLM-as-a-Judge 
    to evaluate the agent's response against the expected outcome.
    """
    try:
        agent_response = event.get('agent_response')
        test_scenario = event.get('test_scenario')
        expected_outcome = event.get('expected_outcome')
        
        if not all([agent_response, test_scenario, expected_outcome]):
            raise ValueError("Missing required fields for evaluation")

        # Construct the evaluation prompt for Claude 3
        prompt = f"""You are an expert QA engineer evaluating an AI agent's behavior.
        
Test Scenario: {test_scenario}
Expected Outcome: {expected_outcome}
Actual Agent Response: {agent_response}

Evaluate the agent's response based on the expected outcome. 
Does it meet the requirements? Is it safe, accurate, and free of hallucinations?

Respond ONLY with a JSON object in this exact format:
{{
    "pass": true/false,
    "score": 0-100,
    "reason": "Brief explanation of the score and pass/fail decision"
}}"""

        # Call Bedrock (Claude 3 Haiku for fast, cheap evals)
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            })
        )
        
        response_body = json.loads(response.get('body').read())
        eval_result = json.loads(response_body['content'][0]['text'])
        
        return {
            'scenario': test_scenario,
            'pass': eval_result.get('pass', False),
            'score': eval_result.get('score', 0),
            'reason': eval_result.get('reason', 'Evaluation parsing failed')
        }

    except Exception as e:
        print(f"Evaluation error: {str(e)}")
        return {
            'scenario': event.get('test_scenario', 'Unknown'),
            'pass': False,
            'score': 0,
            'reason': f"Evaluation pipeline error: {str(e)}"
        }
