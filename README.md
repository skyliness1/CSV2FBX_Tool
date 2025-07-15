# CSV2FBX_Tool
这是一个用于将CSV数据转为FBX数据的小工具

可选导入顶点，法线，切线，顶点色，UV1与UV2

可执行文件位置：Scripts\dist\CSV2FBX_Tool.exe

## 使用说明
### File Path
- CSV File：你的CSV文件路径
- FBX Output：输出Fbx文件的保存路径
### Column Mapping

- Vertex ID Column：你的CSV数据中顶点编号所处于的列（如第0列，则此处填0）
- Position Columns（X,Y,Z）：你的CSV数据中顶点位置X所处于的列（如顶点位置XYZ分别处于第2，3，4列，则此处填2）
- Normal Columns（X,Y,Z）：你的CSV数据中法线数据X所处于的列（如法线数据XYZ分别处于第5，6，7列，则此处填5）
- UV Columns（U,V）：你的CSV数据中UV所处于的列（如UV分别处于第8，9列，则此处填8）
- UV1 Columns（U,V）：你的CSV数据中UV1所处于的列（如UV分别处于第8，9列，则此处填8）
- Tangnet Columns（X,Y,Z）：你的CSV数据中切线数据所处于的列
- Color Columns（R,G,B,A）：你的CSV数据中顶点色数据所处于的列
- UV2 Columns（U,V）：你的CSV数据中UV2所处于的列
