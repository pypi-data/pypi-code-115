from cuboid_sphere.process_depth_map import process_hdf5
from cuboid_sphere.process_image import process_2d_image
import requests
from fastapi import FastAPI, File
from fastapi import UploadFile
import uuid
import cv2
import os
import aiofiles

os.makedirs("/tmp/", exist_ok=True)
# import aiofiles module

app = FastAPI()

@app.post("/hdf5")
async def post_endpoint_hdf5(in_file: UploadFile=File(...), X: float=0.5, Y: float=0.5, Z: float=1, scale: float=2.5):
    print("*"*80)
    filename = os.path.join('/tmp/', str(uuid.uuid4()) + '.hdf5')
    async with aiofiles.open(filename, 'wb') as out_file:
        content = await in_file.read()  # async read
        await out_file.write(content)  # async write
    
    results, point_cloud, disparity_map = process_hdf5(filename, X=X, Y=Y, Z=Z, scale=scale)
    
    return {"results": results, "point_cloud": point_cloud, "disparity_map": disparity_map}


@app.post("/image")
async def post_endpoint_image(in_file: UploadFile=File(...), cx: int=200, cy: int=200, fx: int=60, fy: int=40):
    filename = os.path.join('/tmp/', str(uuid.uuid4()) + '.png')
    async with aiofiles.open(filename, 'wb') as out_file:
        content = await in_file.read()
        await out_file.write(content)
    
    image = cv2.imread(filename)
    results = process_2d_image(image)
    return results


if __name__ == "__main__":
    import uvicorn
    app_port = os.getenv('APP_PORT')
    if app_port is None:
        app_port = '6500'
    uvicorn.run(app, host="0.0.0.0", port=int(app_port))