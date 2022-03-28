from ..frame.dsw_sql_result import DswSqlResult
from odps.ipython.magics import ODPSSql
from IPython.core.magic import Magics, magics_class, line_cell_magic
from IPython.display import display

STEP = 0
   
@magics_class
class DswOdpsMagics(ODPSSql):
    @line_cell_magic
    def dsw_sql(self, line, cell=''):
        global STEP
        result = self.execute(line, cell)
        STEP+=1        
        v_name = 'df{}'.format(STEP) 
        self.shell.user_ns[v_name] = result;
        print('Execution result in the variable:' + v_name)
        res = DswSqlResult(result.values.values.tolist(),
                           schema=result, index=1)
                           
        display(res)

    @line_cell_magic
    def dsw_profile(self, line):
        dataFrame = self.shell.user_ns[line]
        dataFrame.to_pandas().describe()


def load_ipython_extension(ip):
    ip.register_magics(DswOdpsMagics)
