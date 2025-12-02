# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()

import boto3
import os
import json
import logging
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb_client = boto3.client("dynamodb")


def handler(event, context):
    table = os.environ.get("TABLE_NAME")
    request_context = event.get("requestContext", {})
    
    # Log security context
    logger.info(json.dumps({
        "event": "api_request",
        "request_id": request_context.get("requestId"),
        "source_ip": request_context.get("identity", {}).get("sourceIp"),
        "user_agent": request_context.get("identity", {}).get("userAgent"),
        "http_method": request_context.get("httpMethod"),
        "resource_path": request_context.get("resourcePath"),
    }))
    
    try:
        if event["body"]:
            item = json.loads(event["body"])
            year = str(item["year"])
            title = str(item["title"])
            id = str(item["id"])
            
            logger.info(json.dumps({
                "event": "dynamodb_write",
                "table": table,
                "item_id": id,
                "operation": "put_item",
            }))
            
            dynamodb_client.put_item(
                TableName=table,
                Item={"year": {"N": year}, "title": {"S": title}, "id": {"S": id}},
            )
            message = "Successfully inserted data!"
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": message}),
            }
        else:
            item_id = str(uuid.uuid4())
            
            logger.info(json.dumps({
                "event": "dynamodb_write",
                "table": table,
                "item_id": item_id,
                "operation": "put_item",
                "note": "default_data",
            }))
            
            dynamodb_client.put_item(
                TableName=table,
                Item={
                    "year": {"N": "2012"},
                    "title": {"S": "The Amazing Spider-Man 2"},
                    "id": {"S": item_id},
                },
            )
            message = "Successfully inserted data!"
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": message}),
            }
    except Exception as e:
        logger.error(json.dumps({
            "event": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "request_id": request_context.get("requestId"),
        }))
        raise
