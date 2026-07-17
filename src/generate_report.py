import json
import os
import boto3
from datetime import datetime

s3 = boto3.client('s3')
sns = boto3.client('sns')

REPORT_BUCKET = os.environ.get('REPORT_BUCKET', 'agentci-eval-reports')
SNS_TOPIC_ARN = os.environ.get('ALERT_TOPIC_ARN')
PASS_THRESHOLD = int(os.environ.get('PASS_THRESHOLD', '90'))

def lambda_handler(event: list, context: Any) -> dict:
    """
    AgentCI Reporter: Aggregates all eval results, generates a Markdown report,
    saves it to S3, and fires an SNS alert if behavioral regression is detected.
    """
    try:
        # Event is a list of results from the Step Functions Map state
        total_tests = len(event)
        passed_tests = sum(1 for r in event if r.get('pass', False))
        average_score = sum(r.get('score', 0) for r in event) / total_tests if total_tests > 0 else 0
        
        passed_pipeline = average_score >= PASS_THRESHOLD and passed_tests == total_tests
        
        # Generate Markdown Report
        report_md = f"# AgentCI Evaluation Report\n\n"
        report_md += f"**Date:** {datetime.utcnow().isoformat()}Z\n"
        report_md += f"**Pipeline Status:** {'✅ PASSED' if passed_pipeline else '❌ FAILED (Behavioral Regression)'}\n"
        report_md += f"**Average Score:** {average_score:.1f}/100\n"
        report_md += f"**Tests Passed:** {passed_tests}/{total_tests}\n\n"
        
        report_md += "## Detailed Results\n\n"
        for idx, result in enumerate(event, 1):
            status_icon = "✅" if result.get('pass') else "❌"
            report_md += f"### Test {idx}: {status_icon} Score: {result.get('score')}/100\n"
            report_md += f"**Scenario:** {result.get('scenario')}\n"
            report_md += f"**Reason:** {result.get('reason')}\n\n"
            
        # Save to S3
        report_key = f"reports/{datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')}-eval.md"
        s3.put_object(
            Bucket=REPORT_BUCKET,
            Key=report_key,
            Body=report_md.encode('utf-8'),
            ContentType='text/markdown'
        )
        
        # Alert on failure
        if not passed_pipeline and SNS_TOPIC_ARN:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="🚨 AgentCI Pipeline Failed: Behavioral Regression Detected",
                Message=f"Agent evaluation failed.\nScore: {average_score:.1f}/100\nPassed: {passed_tests}/{total_tests}\nReport: s3://{REPORT_BUCKET}/{report_key}"
            )
            
        return {
            'status': 'SUCCESS' if passed_pipeline else 'FAILED',
            'report_s3_uri': f"s3://{REPORT_BUCKET}/{report_key}",
            'average_score': average_score
        }

    except Exception as e:
        print(f"Error generating report: {str(e)}")
        raise e
