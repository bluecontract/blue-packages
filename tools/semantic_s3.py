"""S3 transport for cards addressed by exact BlueId; no model calls."""
import json

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from release import require, wire

MAX_CARD_BYTES = 100_000


def card_key(blue_id):
    return blue_id + '.json'


class Store:
    def __init__(self, bucket, client=None):
        self.bucket = bucket
        self.client = client or boto3.client('s3', config=Config(
            retries={'mode': 'standard', 'total_max_attempts': 4}, connect_timeout=10, read_timeout=30))

    def keys(self):
        return {item['Key']
                for page in self.client.get_paginator('list_objects_v2').paginate(Bucket=self.bucket)
                for item in page.get('Contents', [])}

    def read(self, key):
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
        except ClientError as error:
            if error.response['Error']['Code'] in {'NoSuchKey', '404'}:
                return None, None
            raise
        with response['Body'] as stream:
            data = stream.read(MAX_CARD_BYTES + 1)
        require(len(data) <= MAX_CARD_BYTES, 'Oversized semantic object: ' + key)
        card = json.loads(data)
        require(isinstance(card, dict), 'Invalid semantic object: ' + key)
        return card, response['ETag']

    def restore(self, blue_id, keys):
        key = card_key(blue_id)
        card, _ = self.read(key) if key in keys else (None, None)
        return card

    def publish(self, blue_id, card, keys, *, promote=False):
        key = card_key(blue_id)
        current, etag = self.read(key) if key in keys else (None, None)
        if current == card or current is not None and not promote:
            return dict(uploaded=False, correctionPending=current != card)
        condition = {'IfMatch': etag} if etag else {'IfNoneMatch': '*'}
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=wire(card),
                                   ContentType='application/json', CacheControl='no-cache', **condition)
        except ClientError as error:
            if error.response['Error']['Code'] not in {'PreconditionFailed', '412'}:
                raise
            existing, _ = self.read(key)
            require(existing == card, 'Conflicting semantic card; rerun publication from current main: ' + blue_id)
            return dict(uploaded=False, correctionPending=False)
        return dict(uploaded=True, correctionPending=False)
