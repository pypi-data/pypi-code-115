import random
import string

class Executor():
    def __init__(self):
        self.__result = ''
        self.__type = ''
        self.__subtype = ''
        self.__command = ''
        self.__args = ''
        self.__run = None
        self.__bins = []
        self.__numberOfTasks = 1
        self.__indexes = ''
        self.__salsa_default = {
            'host': 'tcp://localhost:41000'
        }

    def execute(self, body):
        self.__result = ""
        self.parse(body)
        if self.__run is not None:
            # TODO add run type 'container' podman/docker (let user choose executable)
            # TODO change kubectl to oc (let user choose executable)
            if self.__run.type == 'k8s-cmd': 
                self.build_k8s_cmd()
            if self.__run.type == 'k8s':
                self.replace_template()
                self.__result = "kubectl delete -f " + self.__run.pod.name + '.yaml' + " && kubectl apply -f " + self.__run.pod.name + '.yaml'
                # TODO urob priecinok
                return self.__result
        if self.__type == 'salsa':
            if self.__subtype == 'feeder':
                self.__result += 'salsa-feeder '
            if self.__subtype == 'ndm':
                self.__result += 'salsa-ndm '
            if self.__run is not None and self.__run.type == 'k8s-cmd':
                self.__result += "-- "
                self.__result += '-s tcp://sls-submitter-service:41000'
            else: 
                self.__result += '-s "' + (body.salsa.host if body.salsa is not None and body.salsa.host != "" else self.__salsa_default['host']) + '"'
            if body.salsa is not None and body.salsa.job_type == 'command':
                self.__result += ' -c "' + self.__command
                if self.__args != '':
                     self.__result += ':' + self.__args
                self.__result += '"'
            if body.salsa is not None and body.salsa.job_type == 'template':
                self.__result += ' -t "' + self.__command + ' ' + self.__args + ':' + str(self.__numberOfTasks) + '" --batch'
        elif self.__type == 'slurm':
            if self.__command == 'scancel':
                self.__result += self.__command + ' ' + self.__args
            else:
                filename = 'sbatch-' + self.generate_random_string() + '.sh'
                with open(filename, 'w') as f:
                    f.write('#!/bin/bash\n')
                    f.write(self.__command + " " + self.__args + '\n')
                self.__result += 'sbatch ' + (('-a ' + self.__indexes + ' ') if (self.__indexes is not None and self.__indexes != '') else '') + filename
        if self.__bins is not None and len(self.__bins) > 0:
            strings = list(map(lambda bin: self.replace_cmd_args_template(bin, self.__result), self.__bins))
            return strings

        return self.__result

    def parse(self, body):
        self.__type = body.type
        self.__subtype = body.subtype
        self.__command = body.command
        self.__args = body.args
        self.__run = body.run
        self.__bins = body.bins
        self.__numberOfTasks = body.numberOfTasks
        self.__indexes = body.indexes

    def replace_cmd_args_template(self, bin, command_str):
        new_str = command_str
        for key in bin:
            new_str = new_str.replace('${'+ key + '}', str(bin[key]))
        return new_str

    def replace_template(self):
        filename = self.__run.pod.name + '.yaml'
        filedata = ""
        with open('template.yaml', 'r') as file:
            filedata = file.read()
            filedata = filedata.replace("{NAME}", self.__run.pod.name)
            filedata = filedata.replace("{TYPE}", self.__type)
            filedata = filedata.replace("{SUBTYPE}", self.__subtype)
            filedata = filedata.replace("{COMMAND}", self.__command)
            filedata = filedata.replace("{ARGS}", self.__args)
            filedata = filedata.replace("{IMAGE}", self.__run.pod.image)
        with open(filename, 'w') as file:
            file.write(filedata)

    def build_k8s_cmd(self):
        self.__result += "kubectl run -it --rm " 
        self.__result += self.__run.pod.name
        self.__result += " --labels="
        self.__result += self.__run.pod.labels
        self.__result += " --image "
        self.__result += self.__run.pod.image
        self.__result += " --restart=Never --command "

    def generate_random_string(self, length = 5):
        options = string.ascii_lowercase + string.digits
        random_str = (''.join(random.choice(options) for i in range(length)))
        return random_str