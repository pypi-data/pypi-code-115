import os

def readme(ruta):
    try:
        readme_check = open(str(ruta) + '/README.md', 'r').read()
    except FileNotFoundError:
        print('[tota_README] - Error 404. Archivo no encontrado')
    else:
        if not '<h1 align="center">' in str(readme_check):
            readme = open(str(ruta) + '/README.md', 'w')
            file = str(os.path.basename(os.path.normpath(ruta)))
            ejercicios_array = []
            ejercicios = int(input('Introduce el numero de ejercicios: '))
            for i in range(ejercicios):
                nombre = str(input('Nombre del ejercicio ' + str(i + 1) + ': '))
                enunciado = str(input('Enunciado del ejercicio ' + str(i + 1) + ': '))
                path_ej = str(input('Introduce el path del ejercicio ' + str(i + 1) + ' (incluyendo el nombre del fichero): '))
                ejercicios_array.append([nombre, enunciado, path_ej])
            readme.write('<h1 align="center">' + file.upper() + '</h1>\n' + '\nEn este [repositorio](https://github.com/mat0ta/' + file + ') quedan resueltos los ejercicios la tarea de esta semana. Puedes encontrar otros proyectos y tareas en mi perfil de GitHub: [mat0ta](https://github.com/mat0ta).\n\n')
            readme.close()
            readme_ejercicios = open(str(ruta) + '/README.md', 'a')
            for j in range(len(ejercicios_array)):
                readme_ejercicios.write('<h2>' + ejercicios_array[j][0] + '</h2>\n\n' + ejercicios_array[j][1] + '\n\nLa función empleada para crear dicho algoritmo es la siguiente:\n\n```py\n\n' + open(str(ruta) + ejercicios_array[j][2], 'r').read() + '\n\n```\n\n')
            print('[tota_README] - Readme terminado.')
        else:
            print('[tota_README] - El readme ya está hecho. Para poder volver a hacerlo deberás borrar su contenido.')

# readme('C:/Users/marti/Documents/GitHub/parcial-poo')