Brook
=====

Virtual machine cluster manager and remote runner aid.
------------------------------------------------------

When managing a large cluster of virtual machines it can often be a chore to do simple tasks such as starting up and or executing simple commands remotely in each individual VM. Brook aims to complement basic tools such as virsh and ssh when operating on many guest domains simultaneously.

Brook is most effective for managing domains with regular naming structures since it allows you to specify guests to act on using regular expressions. For example in a cluster to turn off a subset of VMs acting as load balancers and a backup machine you could do:

    brook down -d /loadbal[2-5]/ -d backup1

which would be equivalent to doing in virsh:

    virsh shutdown loadbal2
    virsh shutdown loadbal3
    virsh shutdown loadbal4
    virsh shutdown loadbal5
    virsh shutdown backup1

Brook uses the qemu:///system hypervisor by default but you can specify any supported by libvirt (So far it's only been really tested using local and remote qemu instances) using the -c flag:

    brook list -c qemu+ssh://kakiray@remotevmhost/system

Currently Brook supports only basic tasks such as listing the status of all domains managed by a hypervisor, starting up and shutting down, or executing commands on VMs using ssh. You can access the help for Brook or for each subcommand using -h

    brook -h
    brook execute -h

TODO
----

* Executing actions in parallel to speed up.
* Implement support for creating, and reverting snapshots through brook.
* Implement support for viewing snapshot tree similar to 'git log --graph'
* Support executing ssh commands on machines whose hostnames differ from vm name
* Support executing commands using serial connection to test situations of no connectivity.
