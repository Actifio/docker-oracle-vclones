# Mounting Oracle Databases with Docker

This repository provides necessary codes and instructions to create Docker containers with Oracle databases mounted via Actifio. 

*NOTE:* This is a experimental approach and not a direct feature of the product nor a qualified product methodology.

# Where to start?

You can start by cloning this git repository.

```
git clone https://github.com/Actifio/docker-oracle-vclones.git
```

# Pre-requisites

Steps described in this document provides instructions on how to create a Docker Image capable of creating Virtual DB Clones of Oracle databases. However these instructions would expect an existing Docker Image which contains Oracle binaries, or rather container image with Oracle Software installed.

In these examples, I've used an image based on Centos:7 with Oracle Installed. I will link details on how to create such an image at a later stage. 

If you search the Docker Hub, there are several project / images around these images, and Oracle stock image (https://hub.docker.com/_/oracle-database-enterprise-edition?tab=description) might be a good place to start.


# Building the image

From the cloned repository, modify the ```Dockerfile``` to suite your base image. 

```
FROM oracle11204
```

should be changed to 

```
FROM yourimagerepo/oracleimage
```

Inside the git repository, run:

```
[root@kubebossman docker-oracle-vclones]# docker build --tag ora-actifio .
Sending build context to Docker daemon  66.05kB
Step 1/7 : FROM oracle11204
 ---> cc35f92b6ef9
Step 2/7 : RUN yum install epel-release
 ---> Running in c4654413fa2b
Loaded plugins: fastestmirror, ovl
Determining fastest mirrors
 * base: mirror.intergrid.com.au
 * extras: mirror.intergrid.com.au
 * updates: mirror.intergrid.com.au
base                                                     | 3.6 kB     00:00     
extras                                                   | 3.4 kB     00:00     
updates                                                  | 3.4 kB     00:00     
[root@kubebossman docker-oracle-vclones]# docker build --tag ora-actifio .
Sending build context to Docker daemon  70.66kB
Step 1/7 : FROM oracle11204
 ---> cc35f92b6ef9
Step 2/7 : RUN yum install -y epel-release
 ---> Running in 01504fdbc60a
Loaded plugins: fastestmirror, ovl
Determining fastest mirrors
 * base: centos.mirror.serversaustralia.com.au
 * extras: centos.mirror.serversaustralia.com.au
 * updates: centos.mirror.serversaustralia.com.au
base                                                     | 3.6 kB     00:00     
extras                                                   | 3.4 kB     00:00     
updates                                                  | 3.4 kB     00:00     
...
...
...
Installed:
  epel-release.noarch 0:7-11                                                    

Complete!
Removing intermediate container 01504fdbc60a
 ---> be8c83de6e4d
Step 3/7 : RUN yum install -y python python-pip && yum clean all
 ---> Running in 805b96f69d66
Loaded plugins: fastestmirror, ovl
Loading mirror speeds from cached hostfile
epel/x86_64/metalink                                     | 3.8 kB     00:00     
 * base: centos.mirror.serversaustralia.com.au
 * epel: mirror.optus.net
 * extras: centos.mirror.serversaustralia.com.au
 * updates: centos.mirror.serversaustralia.com.au
epel                                                     | 5.3 kB     00:00     
(1/3): epel/x86_64/group_gz                                |  88 kB   00:00     
(2/3): epel/x86_64/updateinfo                              | 974 kB   00:00     
(3/3): epel/x86_64/primary_db                              | 6.7 MB   00:00     
Package python-2.7.5-77.el7_6.x86_64 already installed and latest version
python-setuptools.noarch 0:0.9.8-7.el7                                        
...
...
...
Complete!
Loaded plugins: fastestmirror, ovl
Cleaning repos: base epel extras updates
Cleaning up list of fastest mirrors
Removing intermediate container 805b96f69d66
 ---> 6c34e21076ac
Step 4/7 : RUN pip install Actifio && pip install jinja2
 ---> Running in 84f5aa2a29e1
Collecting Actifio
...
...
...
Successfully installed MarkupSafe-1.1.1 jinja2-2.10.1
Removing intermediate container 84f5aa2a29e1
 ---> 99317cc24c42
Step 5/7 : RUN mkdir /script
 ---> Running in abc1c214774d
Removing intermediate container abc1c214774d
 ---> dfc34f212c21
Step 6/7 : ADD --chown=root:root docker-bootstrap.py /script
 ---> f3d1628591b5
Step 7/7 : ENTRYPOINT ['python', '/script/docker-bootstrap.py']
 ---> Running in 6c66677eb4b5
Removing intermediate container 6c66677eb4b5
 ---> 85b3294edd25
Successfully built 85b3294edd25
Successfully tagged ora-actifio:latest
[root@kubebossman docker-oracle-vclones]#
```

At this stage you should be able to list the newly created Docker Image.

```
[root@kubebossman ~]# docker image ls
REPOSITORY                           TAG                 IMAGE ID            CREATED              SIZE
ora-actifio                          latest              85b3294edd25        About a minute ago   5.61GB
oracle11204                          latest              cc35f92b6ef9        36 hours ago         5.45GB
...
...
...
```

# Start the container

Starting the container is little more complicated than the steps we followed sofar. Docker Container need to be told where to find the Oracle database to be mounted in to the container. These details need to be passed as environment variable from the CLI:

```
-e ACT_APPLIANCE=mysky \
-e ACT_USER=demo \
-e ACT_PASS=demo \
-e ACT_APPNAME=hugedb \
-e ACT_SRCHOST=oraserver \
-e ORACLE_SID=mycopy \
-e ORACLE_HOME=/opt/oracle/app/product/11204/ora_1 \
```

| Envar | Description
|---|---|
| ACT_APPLIANCE | Applaince IP or the host name
| ACT_USER | Actifio user account name, with the Mount Manage privileges
| ACT_PASS | Actifio user password 
| ACT_APPNAME | Actifio Application name, or the name of the Database as it appears in Actifio
| ACT_SRCHOST | Hostname where this database is preotected from
| ORACLE_SID | New Oracle SID to create the virtual clone
| ORACLE_HOME | Oracle Home, as per the Docker Image
| ORACLE_USER | Oracle User, defaults to "oracle" if not specified

## Other requirements

Actifio connector is not qualified to run inside containers and in this case, we're not relying on Containers to communicate with Actifio appliance via a connector. However we're going to use the resources from Actifio connector from the host inside the container. Therefore we would need to bind mount ```/act``` from Docker host to the container. 

For this bind mount we require bind-propagation set to ```shared```. This must be explicitly mentioned, and the default option would not allow mounting Actifio Volumes to the containers.

If you wish to access the database from an external application, you will required to map the port ```1521``` during the container creation.

## Example:

```
$ docker container run -d -e ACT_APPLIANCE=mysky \
-e ACT_USER=demo \
-e ACT_PASS=demo \
-e ACT_APPNAME=hugedb \
-e ACT_SRCHOST=oraserver \
-e ORACLE_SID=mycopy \
-e ORACLE_HOME=/opt/oracle/app/product/11204/ora_1 \
--name my-oracle \
--mount type=bind,source=/act,target=/act,bind-propagation=shared \
--port 1521:1521 \
ora-actifio 
```

Once started you should be able to list the following way:

```
[root@kubebossman docker-oracle-vclones]# docker container ls
CONTAINER ID        IMAGE                  COMMAND                  CREATED             STATUS              PORTS               NAMES
b53667e390d4        ora-actifio            "/bin/sh -c 'python …"   7 minutes ago       Up 7 minutes                            my-oracle
```

# License

MIT License

Copyright (c) 2018 Kosala Atapattu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
