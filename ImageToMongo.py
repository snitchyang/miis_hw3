import os
from pymongo import MongoClient

# usage:传入保存到的数据库和collection以及要写入的文件位置
# 如imagetomongo = ImageToMongoDB("image", "image_data","./dataset/a")
class ImageToMongoDB:
    def __init__(self, db_name, collection_name):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def insert_images(self, folder_path):
        success_count = 0
        failed_files = []

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.jpg'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'rb') as f:
                            image_data = f.read()
                            image_doc = {'file_name': file, 'data': image_data}
                            self.collection.insert_one(image_doc)
                            success_count += 1
                    except Exception as e:
                        failed_files.append(file)

        total_processed = success_count + len(failed_files)
        print(f"Total files processed: {total_processed}")
        print(f"Successfully inserted {success_count} files into MongoDB.")
        if failed_files:
            print(f"Failed to insert {len(failed_files)} files into MongoDB: {failed_files}")

# Example usage:
if __name__ == "__main__":
    image_manager = ImageToMongoDB('image', 'image_data')
    folder_path = './dataset/a'  # Replace with your folder path
    image_manager.insert_images(folder_path)
