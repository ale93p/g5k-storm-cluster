import subprocess
from os import environ
from sys import stdout, stderr
from configparser import ConfigParser
from shlex import split as commandSplit
from shutil import copyfile
from time import sleep


### Read configuration file ###

config = ConfigParser()
config.read('cluster.conf')

g5kConfig = config['g5k']
deployImg = str(g5kConfig['deploy.image.name'])
nodeMemory = str(g5kConfig['node.memory.mb'])
nodeCpus = int(g5kConfig['node.cpu.units'])
userName = str(g5kConfig['user.name'])
oarFile = str(g5kConfig['oar.file.location'])
multiCluster = str(g5kConfig['multi.cluster']) in "yes"

stormConfig = config['storm']
zookeperVersion = str(stormConfig['zookeeper.version'])
stormVersion = str(stormConfig['storm.version'])
nimbusNodes = int(stormConfig['nimbus.nodes'])
csvLogDir = str(stormConfig['csv.log.dir'])
csvFilterExpression = str(stormConfig['csv.filter.expression'])
workerPerNode = int(stormConfig['workers.per.node'])
workerFirstSlot = int(stormConfig['workers.starting.slot'])
workerMaxHeapSize = str(stormConfig['worker.max.heap.size.mb'])
workerHeapMemory = str(stormConfig['worker.heap.memory.mb'])
stormScheduler = str(stormConfig['storm.scheduler'])

ansibleConfig = config['ansible']
inventoryPath = str(ansibleConfig['inventory.file.path'])
playbookPath = str(ansibleConfig['playbook.file.path'])

### Variables ###

nimbusConfYaml = 'storm_nimbus.yaml'
supervisorConfYaml = 'storm_supervisor.yaml'
workerLog4jFile = 'worker.xml'
### Obtain cluster's nodes list ###
print("OARFILE:",oarFile)
if oarFile == 'default':
    try:
        oarFile = environ.get('OAR_NODE_FILE')
    except KeyError:
        print("ERROR: nodefile not found")
        exit()
else:
    oarFile = oarFile.replace('~', environ.get('HOME'))

print("OARFILE:",oarFile)
with open(oarFile) as file:
    clusterNodes = [line.strip() for line in file]

clusterNodes = list(set(clusterNodes))
nodesNbr = len(clusterNodes)


print("Your cluster is composed by {} nodes: {}".format(nodesNbr, clusterNodes))

### Deploy image through kadeploy in g5k ###


kadeployCommad = 'kadeploy3 -f {} -a {}.env -k'.format(oarFile, deployImg)
if multiCluster:
    kadeployCommad = kadeployCommad + " --multi-server"
print(kadeployCommad)
kadeployArgs = commandSplit(kadeployCommad)
kadeployProcess = subprocess.Popen(kadeployArgs, stderr=stderr, stdout=stdout)
kadeployProcess.communicate()

### Create ansible host file ###

with open(inventoryPath, 'w') as inventoryFile:
    inventoryFile.write('[all:vars]\n')
    inventoryFile.write('zookeeper_bin_dir="~/zookeeper-{}/bin/"\n'.format(zookeperVersion))
    inventoryFile.write('zookeeper_conf_dir="~/zookeeper-{}/conf/"\n'.format(zookeperVersion))
    inventoryFile.write('storm_bin_dir="~/apache-storm-{}/bin/"\n'.format(stormVersion))
    inventoryFile.write('storm_conf_dir="~/apache-storm-{}/conf/"\n'.format(stormVersion))
    inventoryFile.write('storm_log4j_dir="~/apache-storm-{}/log4j2/"\n'.format(stormVersion))
    inventoryFile.write('\n')
    inventoryFile.write('[nimbus]\n')
    for i in range(0, nimbusNodes):
        inventoryFile.write(str(clusterNodes[i]) + '\n')
    inventoryFile.write('\n')
    inventoryFile.write('[supervisor]\n')
    for i in range(nimbusNodes, nodesNbr):
        inventoryFile.write(str(clusterNodes[i]) + '\n')

### Create storm configuration files to deployed hosts ###

with open(nimbusConfYaml, 'w') as stormNimbus:
    stormNimbus.write('storm.zookeeper.servers:\n')
    stormNimbus.write('  - "{}"\n'.format(clusterNodes[0])) #TODO: multiple zookeeper servers
    stormNimbus.write('storm.local.dir: "local-dir"\n')
    stormNimbus.write('nimbus.seeds: [')
    for i in range(0, nimbusNodes):
        if i > 0: stormNimbus.write(', ')
        stormNimbus.write('"{}"'.format(clusterNodes[i]))
    stormNimbus.write(']\n')

    stormNimbus.write('storm.metrics.reporters:\n')
    stormNimbus.write('  - class: "org.apache.storm.metrics2.reporters.CsvStormReporter"\n')
    stormNimbus.write('    daemons:\n')
    stormNimbus.write('        - "worker"\n')
    stormNimbus.write('    csv.log.dir: \"{}\"\n'.format(csvLogDir))
    stormNimbus.write('    report.period: 10\n')
    stormNimbus.write('    report.period.units: "SECONDS"\n')
    stormNimbus.write('    filter:\n')
    stormNimbus.write('       class: "org.apache.storm.metrics2.filters.RegexFilter"\n')
    stormNimbus.write('       expression: "{}"\n'.format(csvFilterExpression))

copyfile(nimbusConfYaml,'storm_supervisor.yaml') # copy in another file to keep common values

with open(nimbusConfYaml,'a') as stormNimbus:
    stormNimbus.write('storm.scheduler: "{}"\n'.format(stormScheduler))
    stormNimbus.write('topology.worker.max.heap.size.mb: {}\n'.format(workerMaxHeapSize))
    stormNimbus.write('worker.heap.memory.mb: {}\n'.format(workerHeapMemory))


with open(supervisorConfYaml,'a') as stormSupervisor:
    stormSupervisor.write('supervisor.slots.ports:\n')
    for i in range(0,workerPerNode):
        stormSupervisor.write('  - {}\n'.format(str(workerFirstSlot + i)))
    stormSupervisor.write('supervisor.memory.capacity.mb: {}\n'.format(nodeMemory))
    stormSupervisor.write('supervisor.cpu.capacity: {}.0\n'.format(str(nodeCpus*100)))

### Run ansible playbook ###

ansibleCommand = environ.get('HOME') + '/.local/bin/ansible-playbook -i {} {} --extra-vars "nimbus_yaml={} supervisor_yaml={}"'.format(inventoryPath, playbookPath, nimbusConfYaml, supervisorConfYaml)

print(ansibleCommand)
ansibleArgs = commandSplit(ansibleCommand)
ansibleProcess = subprocess.Popen(ansibleArgs, stderr=stderr, stdout=stdout)
ansibleProcess.communicate()

### Check if everything's running ###
print('Waiting startup...')
sleep(15)
stormApiCommand = "curl 'http://{}:8080/api/v1/supervisor/summary'".format(clusterNodes[0])
print(stormApiCommand)
stormApiArgs = commandSplit(stormApiCommand)
subprocess.run(stormApiArgs)

### Copy nimbus configurations locally ###

copyfile(nimbusConfYaml, environ.get('HOME') + '/apache-storm-{}/conf/storm.yaml'.format(stormVersion)) # this will allow deploying topologies from g5k frontend

### Print ssh tunnel to run on host
print()
print()
print("**** ssh tunnel ***")
print("ssh {}@access.grid5000.fr -L8080:{}:8080".format(userName ,clusterNodes[0]))
