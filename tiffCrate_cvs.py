import os
import time
import numpy as np
import rasterio
from rasterio.transform import from_origin
import csv

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" CSVファイルからデータを読み込む関数
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def generate_mesh_data_from_csv(csv_file):
    data = []
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row_idx, row in enumerate(reader):  # 各行を読み込む
            for col_idx, value in enumerate(row):  # 各列を読み込む
                try:
                    value = float(value)  # 値をfloatに変換
                    data.append({"row": row_idx, "col": col_idx, "value": value})
                except ValueError:
                    print(f"Invalid value at row {row_idx}, col {col_idx}: {value}")
                    continue
    return {"test_mesh": data}

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" メッシュデータを基にTIFFファイルを作成
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def process_mesh_data(mesh_data, cTiffInfo, grid_size, base_latitude, base_longitude, mesh_size_m, degree_per_meter):
    # データ初期化
    grid_data = np.zeros((grid_size, grid_size), dtype=np.float32)
    for filename, records in mesh_data.items():
        for record in records:
            row = record["row"]  # 行番号
            col = record["col"]  # 列番号
            value = record["value"]  # 走りにくさ
            grid_data[row, col] = value

    # データを上下反転して (0, 0) を左下に対応
    grid_data = np.flipud(grid_data)

    grid_data *= 255  # 0～255にスケール変換
    grid_data = grid_data.astype("uint8")  # uint8形式に変換

    print(f"Processed Min Value: {grid_data.min()}, Max Value: {grid_data.max()}")

    # 欠損値は0
    grid_data = np.nan_to_num(grid_data, nan=0)

    # Transform設定
    transform = from_origin(
        base_longitude,
        base_latitude + grid_size * mesh_size_m * degree_per_meter,
        mesh_size_m * degree_per_meter,
        mesh_size_m * degree_per_meter,
    )

    print(f"grid_data.shape[0] = {grid_data.shape[0]}")
    print(f"grid_data.shape[1] = {grid_data.shape[1]}")

    # TIFFファイルの生成
    with rasterio.open(cTiffInfo.file, "w", driver="GTiff",
                        height=grid_data.shape[0], width=grid_data.shape[1],
                        count=1, dtype="float32", crs="EPSG:4326",
                        transform=transform) as dst:
        dst.write(grid_data, 1)
    print(f"Generated TIFF file: {cTiffInfo.file}")

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" メイン処理
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def ConvertForTest(codes, csv_file):
    print("Convert for Test")
    start = time.time()

    # テスト用メッシュコードとTIFF情報
    grid_size = 1000
    output_folder = "./output_tiffs"
    os.makedirs(output_folder, exist_ok=True)

    # CSVファイルを基にデータ生成
    mesh_data = generate_mesh_data_from_csv(csv_file)

    # メッシュコードのリストをループで処理
    for code in codes:
        try:
            print(f"\nProcessing mesh code: {code}")

            # メッシュコードを標準化
            if not isinstance(code, str):
                raise ValueError(f"Mesh code must be a string. Got: {type(code)}")
            mesh_code = code.replace("-", "")

            # TIFF情報設定
            cTiffInfo = CTiffInfo(output_folder, "", code)

            # 緯度・経度計算
            lat, lon = calculate_lat_lon(mesh_code)

            # メッシュデータの処理
            process_mesh_data(
                mesh_data, cTiffInfo, grid_size=grid_size, base_latitude=lat,
                base_longitude=lon, mesh_size_m=10, degree_per_meter=1 / 111000
            )

            print(f"Completed processing for mesh code: {code}")
        except Exception as e:
            print(f"Error processing mesh code {code}: {e}")

    time_diff = time.time() - start
    print(f"\nConvert for Test Complete. Total Processing Time: {time_diff:.2f} seconds")


def calculate_lat_lon(mesh_code):

    # 文字列に変換
    meshCode = str(mesh_code)

    # 1次メッシュ用計算
    code_first_two = meshCode[0:2]
    code_last_two = meshCode[2:4]
    code_first_two = int(code_first_two)
    code_last_two = int(code_last_two)
    lat  = code_first_two * 2 / 3
    lon = code_last_two + 100

    print(f"meshCode = {meshCode}")
    print(f"code_first_two = {code_first_two}")
    print(f"code_last_two = {code_last_two}")
    print(f"lat = {lat}")
    print(f"lon = {lon}")
    print(f"len(meshCode) = {len(meshCode)}")


    if len(meshCode) > 4:
        # 2次メッシュ用計算
        if len(meshCode) >= 6:
            code_fifth = meshCode[4:5]
            code_sixth = meshCode[5:6]
            code_fifth = int(code_fifth)
            code_sixth = int(code_sixth)
            lat += code_fifth * 2 / 3 / 8
            lon += code_sixth / 8

    print(f"Latitude: {lat}, Longitude: {lon}")
    # 二次メッシュの場合
    return lat, lon

class CTiffInfo:
    def __init__(self, tifffolder, numtifffolder, degId):
        self.tifffolder = tifffolder
        self.numtifffolder = numtifffolder
        self.degId = degId
        self.file = os.path.join(tifffolder, f"{degId}.tiff")


if __name__ == "__main__":
    mesh_codes = ["5236-77","5236-67","5237-70"]
    # CSVファイルのパスを指定
    csv_file = "forTiff 4 1.csv"
    ConvertForTest(mesh_codes, csv_file)