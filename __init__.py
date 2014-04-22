import json
import logging
from .shared import get_program_dict
from .parser import Parser
from .translator import Translator
#from .semantics import Semantics
#from .processor import Processor

import path
syrup = None
def get_syrup():
    global syrup
    if syrup is None:
        syrup = Syrup()
    return syrup

class Syrup(object):
    '''
    load function text at any time. also read functions from file.
    '''
    def __init__(self):
        self.functions = []
        with open('syrup/settings.json') as f:
            self.settings = json.loads(f.read())

    def read(self):
        source_dir = path.path(self.settings['source'])
        output_dir = path.path(self.settings['output'])
        output_dir.makedirs_p() 
        self.read_dir(source_dir, output_dir)

    def read_dir(self, source_dir, output_dir):
        print "source_dir: {} output_dir: {}".format(source_dir, output_dir)
        with open(output_dir / "__init__.py", 'w') as f:
            f.write('\n')

        for source_path in source_dir.files("*.syrup"):
            print source_path
            with open(source_path) as f:
                out_filename = source_path.name.split('.')[0] + '.py'
                self.read_file(f, output_dir / out_filename)
        for subdir in source_dir.dirs():
            self.read_dir(subdir, output_dir / subdir.name)

    def read_file(self, file_descriptor, output_path):
        parser = Parser(file_descriptor)
        logging.debug("parser finished.")
        for function in parser.functions:
            logging.debug('function:\n{}'.format(function))
        translator = Translator(output_path, parser)

    def read_old(self, file_descriptor):
        parser = Parser(file_descriptor)
        logging.debug("parser finished.")
        for function in parser.functions:
            logging.debug('function:\n{}'.format(function))
        semantics = Semantics(parser.functions)
        self.functions = semantics.library.functions

    def run(self, function_name, inputs):
        # look for function name and run it.
        processor = Processor(self.functions)
        try:
            outputs = processor.run_function(function_name, inputs)
            return outputs
        except Exception as e:
            print "{} {}".format(function_name, inputs)
            raise e

    def function_names(self):
        return [function.name for function in self.functions]

    def __str__(self):
        return json.dumps(self.get_dict())

    def get_dict(self):
        return get_program_dict(self)
