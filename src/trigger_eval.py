import json
import os
import boto3
import uuid
from typing import Dict, Any

sfn = boto3.client('stepfunctions')
dynamodb = boto3.client('dynamodb')

STATE_MACHINE_ARN = os.environ.get('EVAL_STATE_MACHINE_ARN')
TEST_SUITE_TABLE = os.environ.get('TEST_SUITE_TABLE', 'AgentCITestSuites')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AgentCI Trigger: Listens for S3 upload events (new agent deployment) 
    or API calls and triggers the Step Functions evaluation pipeline.
    """
    try:
        # Handle S3 Event (deployment trigger)
        if 'Records' in event and event['Records'][0].get('eventSource') == 'aws:s3':
            s3_record = event['Records'][0]['s3']
            agent_version = s3_record['object']['key']
            agent_id = agent_version.split('/')[0] # Assuming prefix is agent_id
        # Handle API Gateway Event (manual trigger)
        else:
            body = json.loads(event.get('body', '{}'))
            agent_id = body.get('agent_id')
            agent_version = body.get('agent_version', 'latest')
            
        if not agent_id:
            return {'statusCode': 400, 'body': 'Missing agent_id'}

        # Fetch the active test suite for this agent
        response = dynamodb.get_item(
            TableName=TEST_SUITE_TABLE,
            Key={'AgentId': {'S': agent_id}}
        )
        
        if 'Item' not in response:
            return {'statusCode': 404, 'body': f'No test suite found for agent {agent_id}'}
            
        test_suite = response['Item']['Tests']['L']
        
        # Start the Step Functions execution
        execution_id = f"eval-{agent_id}-{uuid.uuid4().hex[:8]}"
        
        sfn.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=execution_id,
            input=json.dumps({
                'agent_id': agent_id,
                'agent_version': agent_version,
                'test_suite': [{'scenario': t['M']['scenario']['S'], 'expected': t['M']['expected']['S']} for t in test_suite],
                'execution_id': execution_id
            })
        )
        
        return {
            'statusCode': 202,
            'body': json.dumps({
                'message': 'Evaluation pipeline triggered',
                'execution_id': execution_id,
                'agent_version': agent_version
            })
        }

    except Exception as e:
        print(f"Error triggering eval: {str(e)}")
        return {'statusCode': 500, 'body': 'Internal server error'}
