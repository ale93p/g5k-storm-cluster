# Grid’5000 Apache Storm Cluster # 

This script will deploy a basic Apache Storm Cluster in our reserved nodes in Grid’5000. Hope to improve it in the future, any help is welcomed.

## Dependencies ##

* Python 3.x
* Ansible (tested with version 2.5)

## How to run it ##

First of all we have to clone this repository in the frontend node in Grid’5000.

Download the disk image from [here](http://i3s.unice.fr/~pagliari/downloads/g5k-storm-image), then move it inside the repository folder.

### Reserve resources ###

To reserve nodes in Grid’5000 you just have to run the following command (adapted to your situation):
```shell
frontend > oarsub -t deploy -p "cluster='suno'" -I -l nodes=4,walltime=2 -k
```
In this example we are in the Sophia region, we’re requesting _4_ nodes for _2_ hours in the cluster named _”suno”_.

For further and more specific information follow the Grid’5000’s [Getting Started tutorial](https://www.grid5000.fr/mediawiki/index.php/Getting_Started).

### Pre-task: customize the config file ###

Open the file `cluster.conf` and modify the parameters to comply your system configuration (g5k, storm and folders).

### Run it ###

```shell
frontend > python3 deploy.py
```

That’s all. Simple, no?

## Post-Run ##

### Connect to Storm UI ###

To connect to the Web UI, we need to open an ssh tunnel to the web service port:

```shell
localhost > ssh {{ g5k.username }}@access.grid5000.fr -L8080:{{ nimbus_node_address }}:8080

```

Now the Web Server should be reached through `localhost:8080`
