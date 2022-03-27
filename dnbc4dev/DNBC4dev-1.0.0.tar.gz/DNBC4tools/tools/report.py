import os
from .utils import str_mkdir,logging_call,change_path,python_path
from DNBC4tools.__init__ import _root_dir

class Report:
    def __init__(self,args):
        self.name = args.name
        self.species = args.species
        self.need_bam = args.need_bam
        self.outdir = os.path.join(args.outdir,args.name)
    def run(self):
        str_mkdir('%s/04.report'%self.outdir)
        str_mkdir('%s/log'%self.outdir)
        change_path()
        new_python = python_path()
        pre_cmd = '%s %s/rna/pre_process.py --outPath %s'\
            %(new_python,_root_dir,self.outdir)
        generate_report_cmd = '%s %s/rna/generate_report.py --outPath %s --htmlTemplate %s/template/template.html --name %s --species %s' \
            %(new_python,_root_dir,self.outdir,_root_dir,self.name,self.species)
        generate_output_cmd = ['%s %s/rna/report_output.py --indir %s'%(new_python,_root_dir,self.outdir)]
        if self.need_bam:
            generate_output_cmd += ['--need_bam']
        generate_output_cmd = ' '.join(generate_output_cmd)
        
        logging_call(pre_cmd,'report',self.outdir)
        logging_call(generate_report_cmd,'report',self.outdir)
        logging_call(generate_output_cmd,'report',self.outdir)

def report(args):
    Report(args).run()

def parse_report(parser):
    parser.add_argument(
        '--name',
        required=True,
        help='Sample name'
    )
    parser.add_argument(
        '--species',
        type=str,
        default='NA',
        help='select species for cell annotation, only human and mouse can do auto annotation.'
    )
    parser.add_argument(
        '--outdir',
        help='output dir, default is current directory.',
        default=os.getcwd()
    )
    parser.add_argument(
        '--need_bam', 
        action='store_true',
        help='Generate a bam file in output dir.'
        )
    return parser
