#!/usr/bin/python
# -*- coding:utf-8 -*-

#############################################
# Flask & werkzeug HTTP Proxy Sample code.
# - Adapted from Code by Jioh L. Jung (ziozzang@gmail.com)
#############################################
import httplib
import re
import urllib
import urlparse
import json
import os
import sys
import socket
import time
import kbservices

from flask import Flask, Blueprint, request, Response, url_for, jsonify
from werkzeug.datastructures import Headers
from werkzeug.exceptions import NotFound


app = Flask(__name__)
app.debug_log_format= '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'

# Default Configuration
DEBUG_FLAG = True
LISTEN_PORT = 5000

CONFIG='cluster.ini'
if 'DOCKER_HOST' in os.environ:
  IP=os.environ['DOCKER_HOST'].replace('tcp://','').split(':')[0]
else:
  IP=''

router = Blueprint('router', __name__)

# You can insert Authentication here.
#router.before_request(check_login)


# Filters.
HTML_REGEX = re.compile(r'((?:src|action|href)=["\'])/')
JQUERY_REGEX = re.compile(r'(\$\.(?:get|post)\(["\'])/')
JS_LOCATION_REGEX = re.compile(r'((?:window|document)\.location.*=.*["\'])/')
CSS_REGEX = re.compile(r'(url\(["\']?)/')

REGEXES = [HTML_REGEX, JQUERY_REGEX, JS_LOCATION_REGEX, CSS_REGEX]

def iterform(multidict):
    for key in multidict.keys():
        for value in multidict.getlist(key):
            yield (key.encode("utf8"), value.encode("utf8"))

@router.errorhandler(404)
def not_found(error=None):
    app.logger.warning("404 return")
    message = {
            'status': 404,
            'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp

# For RESTful Service
@router.route('/services/', methods=["GET"])
def router_list():
  app.logger.debug("listing services")
  list="<ul>\n"
  for s in services.get_list():
    list+='<li><a href="/services/%s/">%s</a>\n'%(s,s)
  list+="</ul>"
  return list

@router.route('/kill/<service>', methods=["DELETE"])
def router_kill(service):
  app.logger.debug("killing: '%s'" % (service))
  services.kill_service(service)
  return service

@router.route('/services/<service>/', methods=["OPTIONS", "GET", "POST", "PUT", "DELETE"], strict_slashes=False)
@router.route('/services/<service>/<path:file>', methods=["OPTIONS", "GET", "POST", "PUT", "DELETE"], strict_slashes=False)
def router_request(service, file=""):
    app.logger.debug("S: '%s'" % (service))

    if services.isaservice(service) is False:
      app.logger.debug("invalid service '%s'" % (service))
      return not_found()

    if services.isstarted(service)!=True:
      app.logger.info("starting: '%s'" % (service))
      services.start_service(service)
      time.sleep(1)
    (hostname,port)=services.get_hostport(service)
      
    # Whitelist a few headers to pass on
    request_headers = {}
    for h in request.headers.keys():
        if h.lower() not in ["content-length"]:
            request_headers[h] = request.headers[h]

    if request.query_string:
        path = "/%s?%s" % (file, request.query_string)
    elif file=='':
        path=''
    else:
        path = "/" + file

    if request.method == "POST" or request.method == "PUT":
        form_data = request.get_data()
        request_headers["Content-Length"] = len(form_data)
    else:
        form_data = None
    conn = httplib.HTTPConnection(hostname, port)
    try:
      r=conn.request(request.method, path, body=form_data, headers=request_headers)
      resp = conn.getresponse()
    except socket.error, e:
      app.logger.error("Request %s failed to %s on %s:%d/%s"%(request.method,service,hostname,port,path))
      services.update_services()
      return not_found() 
    except:
      e = sys.exc_info()[0]
      app.logger.error("Bad response to %s on %s:%d"%(service,hostname,port))
      return not_found()

    # Clean up response headers for forwarding
    d = {}
    response_headers = Headers()
    for key, value in resp.getheaders():
        d[key.lower()] = value
        if key.lower() in ["content-length", "connection", "content-type","transfer-encoding"]:
            continue

        if key == "set-cookie":
            cookies = value.split(",")
            [response_headers.add(key, c) for c in cookies]
        else:
            response_headers.add(key, value)

    # If this is a redirect, munge the Location URL
    if "location" in response_headers:
        redirect = response_headers["location"]
        parsed = urlparse.urlparse(request.url)
        redirect_parsed = urlparse.urlparse(redirect)

        redirect_host = redirect_parsed.netloc
        if not redirect_host:
            redirect_host = "%s:%d" % (hostname, port)

        redirect_path = redirect_parsed.path
        if redirect_parsed.query:
            redirect_path += "?" + redirect_parsed.query

        munged_path = url_for(".router_request",
                              host=redirect_host,
                              file=redirect_path[1:])

        url = "%s://%s%s" % (parsed.scheme, parsed.netloc, munged_path)
        response_headers["location"] = url

    # Rewrite URLs in the content to point to our URL schemt.method == " instead.
    # Ugly, but seems to mostly work.
    #root = url_for(".router_request")
    contents = resp.read()

    flask_response = Response(response=contents,
                              status=resp.status,
                              headers=response_headers,
                              content_type=resp.getheader('content-type'))
    return flask_response


app.config.update(dict(DEBUG=DEBUG_FLAG))
services=kbservices.kbservices()
app.register_blueprint(router)

if __name__ == '__main__':
  app.run(debug=DEBUG_FLAG, host='0.0.0.0', port=LISTEN_PORT, threaded=True)
