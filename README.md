# interceptor
An https intercepting proxy that collects request and response streams, and saves them to s3 for analysis

docker run --rm -it -v ~/.mitmproxy:/home/mitmproxy/.mitmproxy -p 8080:8080 --env-file env sdmitm  mitmdump -s /home/mitmproxy/intercept.py
