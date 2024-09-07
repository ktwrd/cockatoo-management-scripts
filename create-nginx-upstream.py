import argparse, util

parser = argparse.ArgumentParser(
    prog='Cockatoo Upstream Config Generator',
    description='Tool for generating an nginx config file which includes upstream servers that point to containers on this instance.')
parser.add_argument('--network',
                    dest='network',
                    default='cockatoo_default',
                    action='store', 
                    help='Network name')
parser.add_argument('--output-location',
                    dest='location',
                    action='store',
                    default='/etc/nginx/conf.d/1_upstream_cockatoo.conf',
                    help='Output Location for the config file that will be generated')
parser.add_argument('--prefix',
                    dest='prefix',
                    action='store',
                    default='cockatoo',
                    help='Prefix for the upstreams')
parser.add_argument('--upstream-web',
                    dest='upstream_web',
                    action='append',
                    required=True,
                    help='Array of containers that are running Cockatoo.Web (can be formatted like `container:port`)')
args = parser.parse_args()

if len(args.upstream_web) < 1:
    print('Argument --upstream-web is required')
    exit()

def generate_upstream_conf(name, container_items, default_source_port):
    print('[generate_upstream_conf] name=%s' % name)
    lines = []
    
    for item in container_items:
        port = None
        container_name = item.split(':')[0]
        # try get port
        if item.find(':') > 0:
            port = int(item[item.find(':')+1:])
        else:
            v = util.get_container_external_port(container_name, default_source_port)
            if v is not None:
                port = int(v)
        
        addr = util.get_container_ip(container_name, args.network)
        
        if port is None:
            lines.append('    server %s;' % addr)
        else:
            lines.append('    server %s:%s;' % (addr, port))
        
    return ['upstream %s {' % name] + lines + ['}']
    

def action():
    file_lines = generate_upstream_conf('%s_web' % args.prefix, args.upstream_web, "8080/tcp")
    print('Writing to %s' % args.location)
    with open(args.location, 'w+') as file:
        file.writelines([x + '\n' for x in file_lines])
    print('Done!')
action()