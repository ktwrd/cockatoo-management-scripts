import os, subprocess, urllib, json
def envkey_exists(key):
    value = os.environ.get(key, '')
    return value is not None and len(value) > 0
def run_program(cmd):
    print('[run_program] %s' % cmd)
    output = subprocess.check_output(cmd, shell=True, text=True)
    return output

def get_container_ip(container, network=None):
    cmd = 'docker inspect %s' % container
    stdout = run_program(cmd)
    if not stdout.startswith('['):
        raise RuntimeError('Assumed failure for command %s since stdout isn\'t an array' % cmd)
    data = json.loads(stdout)
    if len(data) < 1:
        return None
    if network is None:
        keys = data[0]['NetworkSettings']['Networks'].keys()
        if len(keys) < 1:
            raise RuntimeError('No networks are associated with the container %s\n%s' % (container, stdout))
        return data[0]['NetworkSettings']['Networks'][keys[0]]['IPAddress']
    return data[0]['NetworkSettings']['Networks'][network]['IPAddress']

def get_container_external_port(container_name, internal_port):
    cmd = 'docker inspect %s' % container_name
    stdout = run_program(cmd)
    if not stdout.startswith('['):
        raise RuntimeError('Assumed failure for command %s since stdout isn\'t an array' % cmd)
    data = json.loads(stdout)
    if len(data) < 1:
        return None
    port_info = data[0]['NetworkSettings']['Ports'].get(internal_port, None)
    if port_info is None:
        return None
    if len(port_info) < 1:
        return None
    for x in port_info:
        if x.get('HostIp', None) == '0.0.0.0':
            v = x.get('HostPort', None)
            if v is not None:
                return v
    return None

def create_mongo_url(data):
    result = 'mongodb://'
    if 'username' or 'password' in data:
        if data['username'] is not None:
            result += data['username']
            if data['password'] is not None:
                result += ':%s@' % data['password']
            else:
                result += '@'
    if len(data['nodelist']) > 0:
        result += ','.join(['%s:%s' % (x[0], x[1]) for x in data['nodelist']])
    if data['database'] is not None:
        result += '/%s' % data['database']
    if data['options'] is not None and len(data['options'].keys()) > 0:
        result += '%s' % urllib.parse.urlencode(data['options'])
    if result == 'mongodb://':
        return None
    return result
    
    
class EnvironmentFile:
    def __init__(self, location):
        self.location = location
        self.data_raw = []
        self.data = {}
    def read(self):
        data_raw = []
        with open(self.location) as file:
            lines = [line.rstrip() for line in file]
            for i in range(len(lines)):
                line = lines[i]
                item = EnvironmentFileLine(self, line, i)
                data_raw.append(item)
                if item.key is not None:
                    self.data[item.key] = item.value
        self.data_raw = data_raw
    def write(self):
        # update values in self.data_raw so it matches self.data
        for key in self.data.keys():
            for item in self.data_raw:
                if item.key is not None and key == item.key:
                    item.value = self.data[key]
        with open(self.location, 'w') as file:
            file.writelines([item.to_string() + '\n' for item in self.data_raw])

class EnvironmentFileLine:
    def __init__(self, parent, content, index):
        self.parent = parent
        self.content = content
        self.index = index
        self.key = None
        self.value = None
        self.comment = None
        self.parse()
    def parse(self):
        eq_idx = self.content.find('=')
        comment_escape_idx = self.content.find('\\#')
        comment_idx = self.content.find('#')
        
        # set comment_idx to the next one (if it's not escaped, then no comments!)
        if comment_idx >= 0 and comment_escape_idx >= 0:
            if (comment_escape_idx + 1) == comment_idx:
                n = self.content[comment_idx+1:].find('#')
                if n >= 0:
                    comment_idx = comment_idx+n+1
                else:
                    comment_idx = -1
        # set key/value when there is a key
        if eq_idx >= 0:
            if comment_idx < 0 or eq_idx < comment_idx:
                self.key = self.content[0:eq_idx]
            # set value length to index of comment delimiter (when there is one)
            _end = len(self.content)
            if comment_idx >= 0:
                _end = comment_idx
            self.value = self.content[eq_idx + 1:_end]
        if comment_idx >= 0:
            self.comment = self.content[comment_idx+1:]

    def to_string(self):
        content = ''
        if self.key is not None:
            content += '%s=' % self.key
            if self.value is not None:
                content += str(self.value)
        if self.comment is not None:
            if self.key is not None and self.value is not None:
                content += ' '
            content += '# %s' % self.comment
        return content
    def to_dict(self):
        return {
            'content': self.content,
            'index': self.index,
            'key': self.key,
            'value': self.value,
            'comment': self.comment
        }