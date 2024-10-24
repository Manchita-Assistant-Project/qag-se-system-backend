# =========================================================== #
# CÓDIGO PARA INICIAR SESIÓN Y OBTENER EL ARCHIVO DE SECRETOS #
# =========================================================== #
#                                                             #
# Ejecutar este código para obtener el archivo credenciales.  #
#                                                             #
# =========================================================== #

# from pydrive2.auth import GoogleAuth

# gauth = GoogleAuth()
# gauth.LocalWebserverAuth()

# =========================================================== #
# CÓDIGO PARA INICIAR SESIÓN Y OBTENER EL ARCHIVO DE SECRETOS #
# =========================================================== #

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import ApiRequestError

"""
This script is used to interact with Google Drive.
"""

gauth = GoogleAuth()
gauth.LoadCredentialsFile("credentials.json")

if gauth.access_token_expired:
    gauth.Refresh()
    gauth.SaveCredentialsFile("credentials.json")
else:
    gauth.Authorize()

drive = GoogleDrive(gauth)

ROOT_FOLDER_ID = '1IMUNjBqkivtipzx476cuz3eY1HPDfn12'

def get_files_recursive(folder_id):
    # Obtener los archivos y carpetas dentro de una carpeta
    file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    all_files = []

    for file in file_list:
        # Si es un archivo, lo agregamos a la lista
        if file['mimeType'] != 'application/vnd.google-apps.folder':
            all_files.append(file)
        else:
            # Si es una carpeta, hacemos una llamada recursiva
            all_files.extend(get_files_recursive(file['id']))

    return all_files

def download_file_from_drive(file, destination_path):
    file_id = file['id']
    try:
        file = drive.CreateFile({'id': file_id})
        file.FetchMetadata()
        file.GetContentFile(destination_path)
        print(f"Archivo {file['title']} descargado correctamente.")
    except Exception as e:
        print(f"Error while downloading {file['title']} - {file_id}: {e}")
