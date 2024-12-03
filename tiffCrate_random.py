import os
import time
import numpy as np
import rasterio
from rasterio.transform import from_origin

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" テスト用ランダムデータ生成関数
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def generate_random_mesh_data(grid_size):
    data = []
    for row in range(grid_size):
        for col in range(grid_size):
            value = np.random.rand()  # 0～1のランダム値
            data.append({"row": row, "col": col, "value": value})
    return {"test_mesh": data}  # テスト用データ

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

    # 欠損値は0
    grid_data[np.isnan(grid_data)] = 0

    # Transform設定
    transform = from_origin(
        base_longitude,
        base_latitude + grid_size * mesh_size_m * degree_per_meter,
        mesh_size_m * degree_per_meter,
        mesh_size_m * degree_per_meter,
    )

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
def ConvertForTest(codes):
    print("Convert for Test")
    start = time.time()

    # テスト用メッシュコードとTIFF情報
    grid_size = 1000  # 1000x1000グリッドで100万ピクセル
    output_folder = "./output_tiffs"
    os.makedirs(output_folder, exist_ok=True)

    # メッシュコードのリストをループで処理
    for code in codes:
        try:
            print(f"\nProcessing mesh code: {code}")

            # メッシュコードを標準化
            if not isinstance(code, str):
                raise ValueError(f"Mesh code must be a string. Got: {type(code)}")
            mesh_code = code.replace("-", "")

            qid = mesh_code[-2:] if len(mesh_code) > 7 else "00"

            # TIFF情報設定
            cTiffInfo = CTiffInfo(output_folder, "", mesh_code[:7], qid)

            # 緯度・経度計算
            lat, lon = calculate_lat_lon(mesh_code)

            # テストデータ生成
            mesh_data = generate_random_mesh_data(grid_size)

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

    if len(meshCode) > 4:
        # 2次メッシュ用計算
        if len(meshCode) >= 6:
            code_fifth = meshCode[4:5]
            code_sixth = meshCode[5:6]
            code_fifth = int(code_fifth)
            code_sixth = int(code_sixth)
            lat += code_fifth * 2 / 3 / 8
            lon += code_sixth / 8

        # 3次メッシュ用計算
        if len(meshCode) >= 8:
            code_seventh = meshCode[6:7]
            code_eighth = meshCode[7:8]
            code_seventh = int(code_seventh)
            code_eighth = int(code_eighth)
            lat += code_seventh * 2 / 3 / 8 / 10
            lon += code_eighth / 8 / 10

        # 1/2メッシュ用計算
        if len(meshCode) >= 9:
            code_nineth = meshCode[8:9]
            code_nineth = int(code_nineth)
            if code_nineth % 2 == 0:
                lon += 0.01250000 / 2
            if code_nineth > 2:
                lat += 0.00833333 / 2

        # 1/4メッシュ用計算
        if len(meshCode) >= 10:
            code_tenth = meshCode[9:10]
            code_tenth = int(code_tenth)
            if code_tenth % 2 == 0:
                lon += 0.01250000 / 2 / 2
            if code_tenth > 2:
                lat += 0.00833333 / 2 / 2

        # 1/8メッシュ用計算
        if len(meshCode) >= 11:
            code_eleventh = meshCode[10:11]
            code_eleventh = int(code_eleventh)
            if code_eleventh % 2 == 0:
                lon += 0.01250000 / 2 / 2 / 2
            if code_eleventh > 2:
                lat += 0.00833333 / 2 / 2 / 2

    print(f"Latitude: {lat}, Longitude: {lon}")
    # 二次メッシュの場合
    return lat, lon


class CTiffInfo:
    def __init__(self, tifffolder, numtifffolder, degId, qid):
        self.tifffolder = tifffolder
        self.numtifffolder = numtifffolder
        self.degId = degId
        self.qid = qid
        self.file = os.path.join(tifffolder, f"{degId}(random).tiff")


if __name__ == "__main__":
    mesh_codes = ["5236-67"]
    ConvertForTest(mesh_codes)
