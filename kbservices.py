#!/usr/bin/python
# -*- coding:utf-8 -*-
 
#############################################
# Flask & werkzeug HTTP Proxy Sample code.
# - Code by Jioh L. Jung (ziozzang@gmail.com)
#############################################
import ConfigParser
import os
import docker
from docker.utils import kwargs_from_env
import time
import sys

STARTED='started'
STOPPED='stopped'
STATUS='status'

class kbservices:
  PREFIX='proxy_'
  CONFIGFILE='cluster.ini'
  DEFAULTIMAGE='canon/fakeserv:1.0'
  RETRY=40
  POLL_TIME=0.1

  def __init__(self):
      self.services=self.read_config()
      self.client=self.init_docker()
      self.update_services()

  def get_item(self,section,item,default):
      value=default
      if self.Config.has_option('defaults',item):
        value=self.Config.get('defaults',item)
      if self.Config.has_option(section,item):
        value=self.Config.get(section,item)
      return value


  def read_config(self):
      services=dict()
      self.Config = ConfigParser.ConfigParser()
      self.Config.default_section='defaults'
      self.Config.read(self.CONFIGFILE)
      for section in self.Config.sections():
        if section=='global':
          continue
        if section=='defaults':
          continue
        type=self.get_item(section,'type','service')
        if type!='service':
          continue
        pt=self.get_item(section,'proxytype','proxy')
        if pt=='skip':
          continue
        service=self.get_item(section,'urlname',section)
        services[service]=dict()
        services[service][STATUS]=STOPPED
        services[service]['ip']=''
        services[service]['port']=0
        services[service]['service-port']=int(self.get_item(section,'service-port',0))
        services[service]['image']=self.get_item(section,'docker-image',self.DEFAULTIMAGE)
        volumes=[]
        binds=[]
        for item in self.get_item(section,'docker-volumes','').split(','):
          if item!='':
            (volume,alias)=item.split(':')
            volumes.append(volume)
            binds.append(volume+':'+alias)
        services[service]['volumes']=volumes
        services[service]['binds']=binds
        links=dict()
        for item in self.get_item(section,'docker-links','').split(','):
          if item!='':
            (link,alias)=item.split(':')
            links[link]=alias
        services[service]['links']=links
        services[service]['section']=section
        services[service]['name']=service
        services[service]['container']=''
      return services
  
  
  def init_docker(self):
    if 'DOCKER_HOST' in os.environ:
      self.IP=os.environ['DOCKER_HOST'].replace('tcp://','').split(':')[0]
    else:
      self.IP=''
    kwargs = kwargs_from_env()
    if 'tls' in kwargs:
      kwargs['tls'].assert_hostname = False
    client = docker.Client(**kwargs)
    return client

  def isaservice(self,service):
    if service in self.services:
      return True
    else:
      return False

  def isstarted(self,service):
    if service in self.services and self.services[service][STATUS]==STARTED:
      return True
    else:
      return False

  def get_list(self):
    return self.services.keys()

  def get_hostport(self,service):
    if service in self.services:
      sr=self.services[service]
      if sr[STATUS]==STOPPED:
        start_service(service)
      return (sr['ip'],sr['port'])
    else:
      return (None,None)
  
  def update_service(self,service,id):
    self.services[service]['container']=id
    ct=self.client.inspect_container(id)
    if ct['State']['Running']==False:
      self.client.remove_container(id)
      self.services[service][STATUS]=STOPPED
      return self.services[service][STATUS]
    if self.IP == '':
      self.services[service]['ip']=ct['NetworkSettings']['IPAddress']
      self.services[service]['port']=self.services[service]['service-port']
    else:
      self.services[service]['ip']=self.IP
      self.services[service]['port']=self.services[service]['service-port']
    self.services[service][STATUS]=STARTED
    return self.services[service][STATUS]
  
  
  def update_services(self):
    for cont in self.client.containers(all=True):
      for name in cont['Names']:
        service=name.replace('/'+self.PREFIX,'')
        if service in self.services:
          self.update_service(service,cont['Id'])
     
  
  def start_service(self,service):
    self.update_services()
    if service not in self.services:
      return False
    
    sr=self.services[service]
    if sr[STATUS]==STARTED:
      return True
    image=sr['image']
    port=sr['service-port']
    host_config=docker.utils.create_host_config(port_bindings={port:port},
	links=sr['links'],
	binds=sr['binds'])
    container = self.client.create_container( image=image,
		name=self.PREFIX+sr['name'],
		detach=True,
		ports=[port],
		volumes=sr['volumes'],
		environment=dict(PORT=port,MYSERVICES=sr['section']),
		host_config=host_config)
    id=container.get('Id')
    response = self.client.start(container=id)
    retry=self.RETRY
    while retry>0:
      retry-=1
      self.update_service(service,id)
      if sr[STATUS]==STARTED:
        return True
      time.sleep(self.POLL_TIMESLEEP)

    return False
     
  def kill_service(self,service):
    self.update_services()
    if service in self.services:
      sr=self.services[service]
      id=sr['container']
      if sr[STATUS]!=STOPPED:
        self.client.kill(id)
        retry=self.RETRY
        while retry>0:
          retry-=1
          self.update_service(service,id)
          if sr[STATUS]==STOPPED:
            return True
          time.sleep(self.POLL_TIME)
    return False
      

  
if __name__ == '__main__':
    kbs=kbservices()
    if len(sys.argv)==3 and sys.argv[1]=='start':
      service=sys.argv[2]
      print "Starting "+service
      kbs.start_service(service)
    elif len(sys.argv)==3 and sys.argv[1]=='stop':
      service=sys.argv[2]
      print "Stop "+service
      if service=='all':
        for s in kbs.get_list():
          kbs.kill_service(s)
      else:
        kbs.kill_service(service)
    elif len(sys.argv)==2 and sys.argv[1]=='status':
      print 
      print '%-30s %5s  %-25s'%('Service','Status','Host:Port')
      print '==========================================================='
      for s in kbs.get_list():
         status=kbs.isstarted(s)
         hp=''
         if status==True:
           (h,p)=kbs.get_hostport(s)
           hp='%s:%d'%(h,p)
         print '%-30s %5s  %-25s'%(s,status,hp)
    else:
      print "Usage: kbservices <start,stop,stautus> [service]"
