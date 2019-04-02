# Grid’5000 Apache Storm Cluster 

This script will deploy a basic Apache Storm Cluster in our reserved nodes in Grid’5000. Hope to improve it in the future, any help is welcomed.

## Dependencies ##

* Python 3.x
* Ansible (tested with version 2.5)

To install ansible from the frontend:
```shell
export PATH=$HOME/.local/bin:$PATH
easy_install --user ansible netaddr
```

## How to run it ##

First of all we have to clone this repository in the frontend node in Grid’5000.

> **Download the disk image and the env file from [here](http://i3s.unice.fr/~pagliari/downloads/g5k-images/#storm), then move them inside the repository folder.**

### Reserve resources ###

To reserve nodes in Grid’5000 you just have to run the following command (adapted to your situation):
```shell
frontend > oarsub -t deploy -p "cluster='suno'" -I -l nodes=4,walltime=2
```
In this example we are in the Sophia region, we’re requesting _4_ nodes for _2_ hours in the cluster named _”suno”_.

For further and more specific information follow the Grid’5000’s [Getting Started tutorial](https://www.grid5000.fr/mediawiki/index.php/Getting_Started).

### Pre-tasks ###

#### Prepare the config file ####

Open the file `cluster.conf` and modify the parameters to comply your system configuration (g5k, storm and folders).
Be sure to change the username with your grid5000 username, and to specify the correct grid5000 image name.
(check also other possible configurations that I may have changed during testing)

#### Install Storm in your frontend ####

Download a binary of Storm ([link to download page for Apache Storm 1.2.1](https://www.apache.org/dyn/closer.lua/storm/apache-storm-1.2.1/apache-storm-1.2.1.tar.gz)) and extract it directly in your frontend home.
It will be needed to copy the configuration for your cluster, so you will be able to submit topologies directly from the frontend.

It should result in something like ```/home/{{username}}/apache-storm-1.2.1```.

### Run it ###

```shell
frontend > python3 deploy.py
```

To access your nodes use:
```shell
ssh root@node-name
```

That’s all. Simple, no?

## Post-Run ##

### Connect to Storm UI ###

To connect to the Web UI, we need to open an ssh tunnel to the web service port:

```shell
localhost > ssh {{ g5k.username }}@access.grid5000.fr -N -L8080:{{ nimbus_node_address }}:8080

```

Now the Web Server should be reached through `localhost:8080`

## Multi-Cluster Run ##

The script is able to deploy storm also in a multi-cluster environment. To make the reservation use:

```shell
frontend > oargridsub -t deploy -w '0:59:00' suno:rdef="/nodes=6",parapide:rdef="/nodes=6"
```

In this case, we don't enter in the job shell, so we don't have the `OAR_NODE_FILE` systemvariable. We can retrieve the list of the reserved machines using:

```shell
frontend > oargridstat -w -l {{ GRID_RESERVATION_ID  }} | sed '/^$/d' > ~/machines
```

Finally, change the configuration file specifying the location of the file just created (`oar.file.location=~/machines`) and write "yes" in the multi cluster option (`multi.cluster=yes`).

For more informations visit the Grid'5000's [Multi-site jobs](https://www.grid5000.fr/mediawiki/index.php/Advanced_OAR#Multi-site_jobs_with_OARGrid) tutorial.
