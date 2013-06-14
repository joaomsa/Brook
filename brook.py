#!/usr/bin/env python2
import libvirt
import sys
import re
from Brook.snapshot import brookDomainSnapshot

class Brook(object):
    def __init__(self, uri):
        # Open connection and parse domain list
        self.conn = libvirt.open(uri)
        if self.conn == None:
            print("Couldn't open socket")
            sys.exit(1)
        self.domdict = {}
        self._update_active_domains()
        self._update_inactive_domains()

    def _update_inactive_domains(self):
        domlist = self.conn.listDefinedDomains()
        for dom in domlist:
            if dom in self.domdict:
                self.domdict[dom]['active'] = False
            else:
                self.domdict[dom] = {'active': False}
            self.domdict[dom]['chosen'] = self.domdict[dom].get('chosen', False)

    def _update_active_domains(self):
        for id in self.conn.listDomainsID():
            dom = self.conn.lookupByID(id).name()
            if dom in self.domdict:
                self.domdict[dom]['active'] = True
                self.domdict[dom]['id'] = id
            else:
                self.domdict[dom] = {'active': True, 'id': id}
            self.domdict[dom]['chosen'] = self.domdict[dom].get('chosen', False)

    def _addDomain(self, domain):
        # Try to add domain that match string
        try:
            self.domdict[domain]['chosen'] = True
        except KeyError:
            sys.exit("domain '%s' does not exist." % domain)

    def _expandDomain(self, regexp):
        # Try to add all domains that match regexp
        for dom in self.domdict.keys():
            regex = re.compile('^' + regexp + '$')
            if regex.match(dom) is not None:
                self.domdict[dom]['chosen'] = True

    def _parse(self, *args):
        for arg in args:
            if re.match(r'^/.*/$', arg) is not None:
                self._expandDomain(arg[1:-1])
            else:
                self._addDomain(arg)

    def list(self, *args, **kwargs):
        print("Dictionary domains:")
        for name, domain in self.domdict.iteritems():
            print(name, domain)

    def up(self, *args, **kwargs):
        # Change to running all domains from list
        for name, domain in self.domdict.iteritems():
            if not domain['active'] and domain['chosen']:
                print('Starting up %s' % name)
                self.conn.lookupByName(name).create()


    def down(self, force=False, *args, **kwargs):
        if force is True:
            print('Forced')
        # Change to stopped all domains from list
        for name, domain in self.domdict.iteritems():
            if domain['active'] and domain['chosen']:
                dom_object = self.conn.lookupByID(domain['id'])
                if force:
                    print('Forcing off %s' % name)
                    dom_object.destroy()
                else:
                    print('Shutting down %s' % name)
                    dom_object.shutdown()

    def testauth(self):
        # See if it can successfully connect and authenticate with each domain
        # REQUIRE: that in ssh_config file each host have an entry with same
        #   name as virsh domain.
        # REQUIRE: that host public key be installed in all domains along
        #   proxy path
        for domain in self.domdict:
            if self.domdict[domain]['chosen']:
                if not self.domdict[domain]['active']:
                    sys.exit("%s is not running" % domain)
                cmd = 'uname'
                process = subprocess.Popen("ssh -o BatchMode=yes %s %s" % (domain, cmd),
                        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                output = process.communicate()
                status = process.poll()
                if status is not 0:
                    sys.exit("%s: %s" % (domain, output))
        return True

    def execute(self, cmd, *args, **kwargs):
        # Execute command remotely, output the command output, and exit with
        # return code.
        import shlex
        from subprocess import Popen, PIPE, STDOUT
        import subprocess
        for domain in self.domdict:
            if self.domdict[domain]['chosen']:
                print('Deep shit')
                if not self.domdict[domain]['active']:
                    sys.exit("%s is not running" % domain)

                args = shlex.split("ssh -o BatchMode=yes %s '%s'" % (domain, cmd))
                process = Popen(args, stdout=PIPE, stderr=STDOUT)
                output, _ = process.communicate(None)
                status = process.poll()

                print("Execution on domain %s returned %i" % (domain, status))
                print(output)

    def snaplist(self, *args, **kwargs):
        for domain in self.domdict:
            if self.domdict[domain]['chosen']:
                dom = self.conn.lookupByName(domain)
                print(domain)
                print('-'*80)
                print('Name\tCreation Time\tState')
                print('-'*80)
                for snap in dom.listAllSnapshots():
                    snap = brookDomainSnapshot(snap)
                    print("%s\t%s\t%s" % (snap.getName(), snap.getDate(), snap.getState()))

    def snapcreate(self, name=None, *args, **kwargs):
        # Try to create, snapshot
        # if no name then use default datestring.
        for domain in self.domdict:
            dom = self.conn.lookupByName(domain)
            # TODO: Implement XML creation in brookDomainSnapshot
            #dom.snapshotCreateXML()

    def snaprestore(self, name=None, force=False, *args, **kwargs):
        # Restore all machines to state from 'snapshot'
        # (fail if any in list don't have that snapshot)
        for domain in self.domdict:
            if self.domdict[domain]['chosen']:
                dom = self.conn.lookupByName(domain)
                try:
                    # Get current snapshot and try to restore it
                    if not name:
                        snap = dom.snapshotCurrent()
                    else:
                        snap = dom.snapshotLookupByName(name)
                    snap = brookDomainSnapshot(snap)
                    print("Restoring %s to snapshot '%s' from %i" %
                            (domain, snap.getName(), snap.getDate()))
                    flags = 0
                    if force:
                        flags |= libvirt.VIR_DOMAIN_SNAPSHOT_REVERT_FORCE
                    dom.revertToSnapshot(snap, flags=flags)
                except libvirt.libvirtError as e:
                    print(e.message)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='Virtual machine cluster manager and test runner aid')

    # Default parser to select domains.
    select = argparse.ArgumentParser(add_help=False)
    select.add_argument('-c', '--conn', default='qemu:///system',
            help="""Connect to the specified URI, instead of the default
            connection to 'qemu:///system'""")
    select.add_argument('-d', '--dom', action='append', default=[],
            help="""Select domain to act upon. Can select multiple domains
            specifying the flag multiple times or as a regular expression
            between two '/'. Ex: -d /debian.*/""")

    subparsers = parser.add_subparsers(title='Commands', dest='func')
    parser_list = subparsers.add_parser('list', parents=[select],
            help='Print status of all domains.')

    parser_up = subparsers.add_parser('up', parents=[select],
            help='Start selected domain.')

    parser_down = subparsers.add_parser('down', parents=[select],
            help='Shutdown selected domain.')
    parser_down.add_argument('-f', '--force', action='store_true',
            help='Force immediate shutdown.')

    parser_execute = subparsers.add_parser('execute', parents=[select],
            help='Executes command over ssh.')
    parser_execute.add_argument('cmd',
            help='The command to execute remotely')

    parser_snaplist = subparsers.add_parser('snaplist', parents=[select],
            help='Print list of snapshots for selected domains')

    parser_snaprestore = subparsers.add_parser('snaprestore', parents=[select],
            help='Revert domain back to a spanshot')
    parser_snaprestore.add_argument('name', nargs='?',
            help='Snapshot to revert to')
    parser_snaprestore.add_argument('-f', '--force', action='store_true',
            help='Allows risky reverts in case of metadata incompatibility')


    args = parser.parse_args()

    brook = Brook(args.conn)
    brook._parse(*args.dom)
    getattr(brook, args.func)(**vars(args))
