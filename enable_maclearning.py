#!/usr/bin/env python3
# Disclaimer: This product is not supported by VMware.
# License: https://github.com/vmware/pyvmomi-community-samples/blob/master/LICENSE

# Purpose:  Enables MAC Learning and Forged Transmit on a given PortGroup


from pyVim.connect import SmartConnect
import ssl
from pyVmomi import vim
import time
import argparse


#Put relevant informations for your environment:
def parseParameters():
    parser = argparse.ArgumentParser(
            description='Arguments to connect to vCenter')
    parser.add_argument('-s', '--sourcevc',
            required = True,
            action = 'store',
            help = 'Vcenter server name or IP')

    parser.add_argument('-u', '--user',
            required=True,
            action='store',
            help='User name to connect to vcenter')
    parser.add_argument('-p', '--password',
            required=True,
            action='store',
            help = 'Password for connection to vcenter')

    parser.add_argument('-pg', '--portgroup',
                        required=True,
                        action='store',
                        help= 'PortGroup (name) on which to set MAC Learning and Forged Transmit')
    args = parser.parse_args()
    return args

def connect_vcenter(sourcevc, user, password):
    context = ssl._create_unverified_context()
    si= SmartConnect(host=str(sourcevc), user=str(user), pwd=password,sslContext=context)
    return si

def get_all_objs(content, vimtype):
    obj = {}
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for managed_object_ref in container.view:
            obj.update({managed_object_ref: managed_object_ref.name})
    return obj

def wait_for_task(task, actionName='job', hideResult=False):
    while task.info.state == vim.TaskInfo.State.running or str(task.info.state) == "queued":
        time.sleep(2)

    if task.info.state == vim.TaskInfo.State.success:
        output = 'Success.\n The task %s completed successfully.' % actionName
        print(output)
    else:
        output = 'The task %s failed and did not complete successfully: %s' % (actionName, task.info.error)
        raise task.info.error
        print(output)

    return task.info.result

def enable_maclearning_forgedtransmit(si, content, portgroup):
    for virtualportgroup in get_all_objs(content, [vim.dvs.DistributedVirtualPortgroup]):
        if virtualportgroup.name == portgroup:
            spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
            spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
            spec.configVersion = virtualportgroup.config.configVersion

            spec.defaultPortConfig.macManagementPolicy= vim.dvs.VmwareDistributedVirtualSwitch.MacManagementPolicy()
            spec.defaultPortConfig.macManagementPolicy.macLearningPolicy= virtualportgroup.config.defaultPortConfig.macManagementPolicy.macLearningPolicy
            spec.defaultPortConfig.macManagementPolicy.inherited = False

            spec.defaultPortConfig.macManagementPolicy.macLearningPolicy.enabled = True
            spec.defaultPortConfig.macManagementPolicy.macLearningPolicy.inherited = False
            spec.defaultPortConfig.macManagementPolicy.macLearningPolicy.limit = 4096
            spec.defaultPortConfig.macManagementPolicy.macLearningPolicy.limitPolicy = "DROP"

            spec.defaultPortConfig.macManagementPolicy.forgedTransmits = True

            task = virtualportgroup.ReconfigureDVPortgroup_Task(spec = spec)
            wait_for_task(task, si)


if __name__ == "__main__":
    #Get user input from CLI
    args = parseParameters()
    print(args.sourcevc, args.user, args.password, args.portgroup)
    #Initiate a session to vCenter
    si = connect_vcenter(args.sourcevc, args.user, args.password)
    content = si.content
    #Enable Mac learning and forged transmit
    enable_maclearning_forgedtransmit(si, content, args.portgroup)
