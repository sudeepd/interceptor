import mitmproxy
import os
import json
import redis 
import boto3
from mitmproxy import http

REDIS_HOST=os.environ.get("REDIS_HOST","localhost")
REDIS_PORT=os.environ.get("REDIS_PORT","6379")
S3_BUCKET=os.environ.get("S3_BUCKET")

r = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), db=0)

def write_data(bucket: str, filename : str, content : bytes):
    if (content):
        client = boto3.client('s3')
        client.put_object(Body=content, Bucket=bucket, Key=filename)

'''
Gets a counter from redis 
'''
def get_counter( redis, key):
    pipeline = redis.pipeline()
    pipeline.incr(key)
    pipeline.expire(key,10)
    results = pipeline.execute()
    counter = results[0]
    return counter

def create_request_preamble( request : mitmproxy.http.Request):
    req = {} 
    req["host"] = request.host
    req["port"] = request.port
    req["method"] = request.method
    req["scheme"] = request.scheme
    req["authority"] = request.authority
    req["path"] = request.path
    req["http_version"] = request.scheme
    req["headers"] = {}
    for key in request.headers.keys():
        req["headers"][key] = request.headers.get_all(key)[0]
    req["path"] = request.path
    req["trailers"] = {}
    if (request.trailers):
        for key in request.trailers.keys():
            req["trailers"][key] = request.trailers.get_all(key)[0]
      
    req["timestamp_start"] = request.timestamp_start
    req["timestamp_end"] = request.timestamp_end
    return json.dumps(req) 

def create_response_preamble(response : mitmproxy.http.Response):
    res = {}
    res["http_version"] = response.http_version
    res["status_code"] = response.status_code
    res["headers"] = {}
    res["trailers"] = {}
    for key in response.headers.keys():
        res["headers"][key] = response.headers.get_all(key)[0]
    if (response.trailers):
        for key in response.trailers.keys():
            res["trailers"][key] = response.trailers.get_all(key)[0]
    res["timestamp_start"] = response.timestamp_start
    res["timestamp_end"] = response.timestamp_end
    res["http_version"] = response.http_version
    return json.dumps(res)


### request header should contain proxy auth
def authenticate(flow):
    return False

def request(flow):
    if (authenticate(flow) is False):
        flow.response = http.Response.make(407,
            "<html><body><h1>Proxy Authentication Required</h1></body></html>",
            {
                "content-type":"text/html",
                "proxy-authenticate" : "Basic"
            }
        )
        

def response(flow):
    req = {}
    res = {}
    connection_id = flow.client_conn.id
    counter = get_counter(r, connection_id)

    request_filename = connection_id + "-" + str(counter) + "-request-preamable.json"
    request_content_filename = connection_id + "-" + str(counter) + "-request-content.bin"
    response_filename = connection_id + "-" + str(counter) + "-response-preamable.json"
    response_content_filename = connection_id + "-" + str(counter) + "-response-content.bin"
   
    request_preamble = create_request_preamble( flow.request)
    request_content = flow.request.content

    response_preamble = create_response_preamble(flow.response)
    response_content = flow.response.content
    write_data(S3_BUCKET, request_filename, bytes(request_preamble,'utf-8'))
    write_data(S3_BUCKET, request_content_filename, request_content)
    write_data(S3_BUCKET, response_filename, bytes(response_preamble,'utf-8'))
    write_data(S3_BUCKET, response_content_filename, response_content)
    return




