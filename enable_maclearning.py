#!/usr/bin/env python3
# Disclaimer: This product is not supported by VMware.
# License: https://github.com/vmware/pyvmomi-community-samples/blob/master/LICENSE

# Purpose:  Enables MAC Learning and Forged Transmit on a given PortGroup 


from pyVim.connect import SmartConnect
import ssl
from pyVmomi import vim
import time

#Put relevant informations for your environment:
vcenter_ip = "VCENTER IP/FQDN"
vcenter_user = "USER"
vcenter_password = "VCENTER PASSWORD"
portgroup_name = "PORTGROUP NAME"

def connect_vcenter(vcenter_ip, vcenter_user, vcenter_password):
    context = ssl._create_unverified_context()
    si= SmartConnect(host=str(vcenter_ip), user=str(vcenter_user), pwd=vcenter_password,sslContext=context)
    return si

def get_all_objs(content, vimtype):
    obj = {}
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for managed_object_ref in container.view:
            obj.update({managed_object_ref: managed_object_ref.name})
    return obj

def wait_for_task(task, actionName='job', hideResult=False):
    while task.info.state == vim.TaskInfo.State.running:
        time.sleep(2)

    if task.info.state == vim.TaskInfo.State.success:
        if task.info.result is not None and not hideResult:
            output = '%s completed successfully, result: %s' % (actionName, task.info.result)
            print(output)
        else:
            output = '%s completed successfully.' % actionName
            print(output)
    else:
        output = '%s failed and did not complete successfully: %s' % (actionName, task.info.error)
        raise task.info.error
        print(output)

    return task.info.result

def enable_maclearning_forgedtransmit(si, content, portgroup_name):
    for portgroup in get_all_objs(content, [vim.dvs.DistributedVirtualPortgroup]):
        if portgroup.name == portgroup_name:
            spec = vim.dvs.DistributedVirtualPortgroup.ConfigSpec()
            spec.defaultPortConfig = vim.dvs.VmwareDistributedVirtualSwitch.VmwarePortConfigPolicy()
            spec.configVersion = portgroup.config.configVersion

            spec.defaultPortConfig.macManagementPolicy= vim.dvs.VmwareDistributedVirtualSwitch.MacManagementPolicy()
            spec.defaultPortConfig.macManagementPolicy.macLearningPolicy= portgroup.config.defaultPortConfig.macManagementPolicy.macLearningPolicy
            spec.defaultPortConfig.macManagementPolicy.inherited = False

            spec.defaultPortConfig.macManagementPolicy.macLearningPolicy.enabled = True
            spec.defaultPortConfig.macManagementPolicy.macLearningPolicy.inherited = False
            spec.defaultPortConfig.macManagementPolicy.macLearningPolicy.limit = 4096
            spec.defaultPortConfig.macManagementPolicy.macLearningPolicy.limitPolicy = "DROP"

            spec.defaultPortConfig.macManagementPolicy.forgedTransmits = True

            task = portgroup.ReconfigureDVPortgroup_Task(spec = spec)
            wait_for_task(task, si)


if __name__ == "__main__":
    #Initiate a session to vCenter
    si = connect_vcenter(vcenter_ip, vcenter_user, vcenter_password)
    content = si.content
    #Enable Mac learning and forged transmit
    enable_maclearning_forgedtransmit(si, content, portgroup_name)
