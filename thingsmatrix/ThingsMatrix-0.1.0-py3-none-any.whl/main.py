import typer
from typer import Option
from typing import Optional
from thingsmatrix import apis
from rich.console import Console
app = typer.Typer()
api = apis.ThingsMatrix()
console = Console()

@app.command()
def reports(
    sn:Optional[str]=typer.Argument(...,help='imei'),
    starttime:Optional[str]=typer.Option(None,help='Format as YYYY-mm-dd HH:mm:ss'),
    endtime:Optional[str]=typer.Option(None,help='Format as YYYY-mm-dd HH:mm:ss')):
    '''
    Filter reports by imei and datetime
    '''
    response,reports = api.get_devices_reports(sn=sn,startTime=starttime,endTime=endtime)
    if response != None or reports != None:
        console.print(response.json()['data']['content'])

# @app.command()
# def devices(sn:Optional[str],model:Optional[str],group:Optional[str],status:Optional[str]):
#     api.get_devices()
    
@app.command()
def device(sn:str,check_status:bool = Option(False,"--status","-s",help="check status",)):
    '''
    Get device by serial number
    '''
    device = api.get_device(sn)
    if device:
        if check_status:
            console.print(device.status.name)
        else:
            device.printJson()
            
def run():
    try:
        app()
        typer.Exit(0)
    except Exception as e:
        print(e)
        typer.Exit(-1)

if __name__ == "__main__":
    run()
        