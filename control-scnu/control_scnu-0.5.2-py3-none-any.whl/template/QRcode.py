from control import shijue1

a = None


a=shijue1.Img()
a.camera(0)
while True:
  a.get_img()
  a.erweima_detect()
  a.name_windows('img')
  a.show_image('img')
  a.delay(1)
  print(a.QR_code_data)