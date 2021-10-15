FROM mitmproxy/mitmproxy
RUN pip3 install boto3 redis
COPY intercept.py /home/mitmproxy

