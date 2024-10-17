import os

import app.generator.utils as utils
import app.generator.gdrive as gdrive
import app.database.chroma_utils as chroma_utils

def main_load():
    """
    Main function to load the data into the Chroma database.
    """
    documents = chroma_utils.load_documents()
    print(f"📚 Loaded {len(documents)} pages")
    chunks = chroma_utils.split_documents(documents)
    print(f"🔪 Split into {len(chunks)} chunks")
    chroma_utils.add_to_chroma(chunks)
    print("🚀 Data loaded successfully!")

if __name__ == "__main__":
    print("🚀 Starting the load process!")
    print("🔍 Searching for files in Google Drive")
    files_in_gdrive = gdrive.get_files_recursive(gdrive.ROOT_FOLDER_ID)
    # for file in files_in_gdrive:
    #     print(f"📄 {file['title']}")
    print(f"🔍 Found {len(files_in_gdrive)} files in Google Drive")
    
    target_file_name = "semilleros_investigacion_2023-1.pdf"
    # target_file_name = "Requisitos PASANTIA para empresas.docx"
    # target_file_name = "NO"

    # encuentra el índice del archivo con el nombre específico
    index_specific_file = next((i for i, file in enumerate(files_in_gdrive) if file['title'] == target_file_name), None)

    if index_specific_file is None:
        print(f"❌ File '{target_file_name}' not found in Google Drive.")
    else:
        print(f"📂 Starting from file: {files_in_gdrive[index_specific_file]['title']}, index: {index_specific_file}")

        # inicia el loop desde el archivo encontrado
        for each_file in files_in_gdrive[index_specific_file:]:
            download_path = os.path.join(chroma_utils.FILES_PATH, each_file['title'])
            gdrive.download_file_from_drive(each_file, download_path)
            try:
                print("🗄️ Loading data into Chroma")
                main_load()  # proceso de recorte de chunks y guardado en la base de datos
                utils.delete_local_file(os.path.join(chroma_utils.FILES_PATH, each_file['title']))
            except Exception as e:
                print(f"Error al cargar el archivo {each_file['title']}: {e}")
                utils.delete_local_file(os.path.join(chroma_utils.FILES_PATH, each_file['title']))
                continue
