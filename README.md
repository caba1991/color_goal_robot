# Gemini APIとROS 2・Gazeboを連携した差動二輪ロボット

## 概要
Physical AI講座 2026 応用編1の最終課題として、Gemini API、ROS 2、Gazeboを連携した差動二輪ロボットを実装しました。
ユーザーが自然言語で目的地を指示すると、Gemini APIが指示を `red`、`blue`、`green` のいずれかに分類します。
分類結果はROS 2トピック `/target_color` で移動制御ノードに渡され、Gazebo上のロボットが対応する座標へ移動します。

## システム構成
```text
自然言語
  ↓ Gemini API
red / blue / green
  ↓ /target_color
move_to_goal.py
  ↓ /cmd_vel
Gazebo上の差動二輪ロボット
```

## 使用技術
- Ubuntu
- ROS 2 Humble
- Gazebo Classic
- Python
- URDF / Xacro
- Gemini API

## ディレクトリ構成
```text
color_goal_robot/
├── CMakeLists.txt
├── package.xml
├── launch/
│   └── robot.launch.py
├── scripts/
│   ├── move_to_goal.py
│   └── command_gemini_node.py
├── urdf/
│   └── color_goal_robot.urdf.xacro
├── worlds/
├── README.md
├── LICENSE
└── .gitignore
```

## 前提環境
- Ubuntu
- ROS 2 Humble
- Gazebo Classic
- Gemini APIキー

## ビルド
```bash
cd ~/pai_ws
rosdep install \
  --from-paths src \
  --ignore-src \
  -r \
  -y

colcon build \
  --symlink-install \
  --packages-select color_goal_robot

source install/setup.bash
```

## Gemini APIキーの設定
APIキーはソースコードに直接記述しません。実行前に環境変数として設定してください。
```bash
export GEMINI_API_KEY="YOUR_API_KEY"
export GEMINI_MODEL="YOUR_AVAILABLE_MODEL"
```

## 実行方法

**1. Gazeboを起動**
```bash
source /opt/ros/humble/setup.bash
source ~/pai_ws/install/setup.bash
ros2 launch color_goal_robot robot.launch.py
```

**2. 移動ノードを起動**
```bash
source ~/pai_ws/install/setup.bash
ros2 run color_goal_robot move_to_goal.py
```

**3. Geminiノードを起動**
```bash
source ~/pai_ws/install/setup.bash
export GEMINI_API_KEY="YOUR_API_KEY"
export GEMINI_MODEL="YOUR_AVAILABLE_MODEL"
ros2 run color_goal_robot command_gemini_node.py
```

起動後、ターミナルで次のような指示を入力します。
```text
青い場所へ行って
```
Geminiが次のように分類します。
```text
blue
```
その後、Gazebo上のロボットが青色の目的地へ移動します。

## ROS 2トピック

| トピック | 型 | 役割 |
| --- | --- | --- |
| `/target_color` | `std_msgs/msg/String` | 目的地ラベル |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | 速度指令 |
| `/odom` | `nav_msgs/msg/Odometry` | ロボット位置 |

## AIの出力制限
誤動作を防ぐため、Geminiの出力は以下の3種類に限定しています。
- `red`
- `blue`
- `green`

許可されていない出力はROS 2トピックへ送信しません。

## 制約
- 目的地は固定座標で定義しています。
- 画像による色認識は実装していません。
- 障害物回避は実装していません。
- Gemini APIを利用するためのインターネット環境が必要です。
- Gemini APIキーは利用者自身で取得・設定する必要があります。

## 動画
提出動画：
- URL: <YouTube動画URLを記載>
